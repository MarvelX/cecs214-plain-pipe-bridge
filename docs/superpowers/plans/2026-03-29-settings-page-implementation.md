# Settings Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real `Settings` page backed by a repository-level shared JSON template for UI preferences and project defaults, while keeping the calculation workflow on a separate workspace page.

**Architecture:** Split the current single-file Streamlit UI into thin native page entrypoints plus focused helper modules under `src/cecs214_plain_pipe/ui/`. Introduce a shared template store, explicit session-state helpers, and group-based template application so new sessions, imports, and manual re-apply flows all use the same logic.

**Tech Stack:** Python 3.9+, Streamlit, dataclasses, pytest

---

## File Structure

- Create: `config/shared_template.json`
- Create: `src/cecs214_plain_pipe/ui/__init__.py`
- Create: `src/cecs214_plain_pipe/ui/template_store.py`
- Create: `src/cecs214_plain_pipe/ui/template_apply.py`
- Create: `src/cecs214_plain_pipe/ui/state.py`
- Create: `src/cecs214_plain_pipe/ui/form_sections.py`
- Create: `src/cecs214_plain_pipe/ui/pages/workspace.py`
- Create: `src/cecs214_plain_pipe/ui/pages/settings.py`
- Create: `pages/1_Engineering_Workspace.py`
- Create: `pages/2_Settings.py`
- Create: `tests/test_template_store.py`
- Create: `tests/test_template_apply.py`
- Modify: `app.py`
- Modify: `src/cecs214_plain_pipe/__init__.py`
- Modify: `tests/test_engine.py`

Each new module owns one responsibility:

- `template_store.py`: load, merge, validate, and save shared template JSON
- `template_apply.py`: apply selected template groups to project/session state
- `state.py`: initialize session state, clear stale calculation outputs, handle import prompt flags
- `form_sections.py`: shared project/default form sections with key prefixing
- `ui/pages/workspace.py`: render the existing engineering workflow plus import prompt handling
- `ui/pages/settings.py`: render shared template editors and apply/save/reset actions
- `pages/*.py`: very thin Streamlit native page entrypoints

### Task 1: Add Shared Template Store And Its Tests

**Files:**
- Create: `config/shared_template.json`
- Create: `src/cecs214_plain_pipe/ui/__init__.py`
- Create: `src/cecs214_plain_pipe/ui/template_store.py`
- Create: `tests/test_template_store.py`
- Modify: `src/cecs214_plain_pipe/__init__.py`

- [ ] **Step 1: Write the failing template-store tests**

```python
from pathlib import Path

import pytest

from cecs214_plain_pipe.ui.template_store import (
    build_builtin_template,
    load_shared_template,
    save_shared_template,
)


def test_load_shared_template_reads_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "shared_template.json"
    path.write_text(
        """
        {
          "ui_preferences": {
            "results_tab": "formula",
            "preview_height": 720,
            "show_formula_trace_expanded": true,
            "sidebar_tips_expanded": false
          },
          "project_defaults": {
            "meta": {"project_name": "模板工程"}
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    template, status = load_shared_template(path)

    assert status["source"] == "disk"
    assert template["ui_preferences"]["preview_height"] == 720
    assert template["project_defaults"]["meta"]["project_name"] == "模板工程"
    assert "geometry" in template["project_defaults"]


def test_load_shared_template_falls_back_when_missing(tmp_path: Path) -> None:
    template, status = load_shared_template(tmp_path / "missing.json")

    assert status["source"] == "builtin"
    assert "ui_preferences" in template
    assert template["project_defaults"]["meta"]["project_name"] == "平管管桥示例工程"


def test_load_shared_template_falls_back_when_json_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not-json}", encoding="utf-8")

    template, status = load_shared_template(path)

    assert status["source"] == "builtin"
    assert "error" in status


def test_save_shared_template_writes_normalized_json(tmp_path: Path) -> None:
    path = tmp_path / "shared_template.json"
    template = build_builtin_template()
    template["project_defaults"]["meta"]["project_name"] = "归档模板"

    save_shared_template(path, template)

    written = path.read_text(encoding="utf-8")
    assert '"project_name": "归档模板"' in written
    assert written.endswith("\n")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_template_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cecs214_plain_pipe.ui'`

- [ ] **Step 3: Write minimal implementation for built-in template and disk load/save**

```python
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from cecs214_plain_pipe.models import default_project_input, project_input_from_dict

TEMPLATE_PATH = Path("config/shared_template.json")

DEFAULT_UI_PREFERENCES = {
    "results_tab": "summary",
    "preview_height": 900,
    "show_formula_trace_expanded": False,
    "sidebar_tips_expanded": True,
}


def build_builtin_template() -> dict[str, Any]:
    return {
        "ui_preferences": deepcopy(DEFAULT_UI_PREFERENCES),
        "project_defaults": default_project_input().to_dict(),
    }


def load_shared_template(path: Path) -> tuple[dict[str, Any], dict[str, str]]:
    builtin = build_builtin_template()
    if not path.exists():
        return builtin, {"source": "builtin", "message": f"Template not found: {path}"}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return builtin, {"source": "builtin", "error": str(exc)}
    merged = _merge_template_defaults(raw, builtin)
    _validate_project_defaults(merged["project_defaults"])
    return merged, {"source": "disk", "message": f"Loaded template: {path}"}


def save_shared_template(path: Path, template: dict[str, Any]) -> None:
    normalized = _merge_template_defaults(template, build_builtin_template())
    _validate_project_defaults(normalized["project_defaults"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _validate_project_defaults(project_defaults: dict[str, Any]) -> None:
    project_input_from_dict(project_defaults)


def _merge_template_defaults(candidate: dict[str, Any], builtin: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(builtin)
    merged["ui_preferences"].update(candidate.get("ui_preferences", {}))
    for group_name, group_value in candidate.get("project_defaults", {}).items():
        if isinstance(group_value, dict) and group_name in merged["project_defaults"]:
            merged["project_defaults"][group_name].update(group_value)
    return merged
```

Also add a package marker:

```python
# src/cecs214_plain_pipe/ui/__init__.py
"""UI helpers for the Streamlit application."""
```

And export the template helpers:

```python
from .ui.template_store import build_builtin_template, load_shared_template, save_shared_template
```

- [ ] **Step 4: Create the initial repository template file**

```json
{
  "ui_preferences": {
    "results_tab": "summary",
    "preview_height": 900,
    "show_formula_trace_expanded": false,
    "sidebar_tips_expanded": true
  },
  "project_defaults": {
    "meta": {
      "project_name": "平管管桥示例工程",
      "project_code": "PPB-001",
      "designer": "",
      "notes": ""
    },
    "geometry": {
      "span_m": 18.0,
      "outer_diameter_mm": 1020.0,
      "wall_thickness_mm": 12.0,
      "corrosion_allowance_mm": 1.0,
      "insulation_weight_kn_m": 0.4,
      "lining_weight_kn_m": 0.0,
      "attachments_weight_kn_m": 0.15,
      "steel_density_kn_m3": 78.5,
      "water_density_kn_m3": 10.0
    },
    "material": {
      "steel_grade": "Q235",
      "elastic_modulus_mpa": 206000.0,
      "design_strength_mpa": 215.0,
      "thermal_expansion_per_c": 1.2e-05,
      "poisson_ratio": 0.3
    },
    "support_scheme": {
      "support_type": "simple_simple",
      "support_friction_coefficient": 0.15,
      "has_expansion_joint": false,
      "stiffener_spacing_mm": 3000.0,
      "stiffener_equivalent_inertia_mm4": 42000000.0,
      "shell_centroid_radius_mm": 510.0
    },
    "actions": {
      "live_load_kn_m": 0.8,
      "wind_load_kn_m": 1.2,
      "design_internal_pressure_mpa": 0.9,
      "working_internal_pressure_mpa": 0.6,
      "vacuum_pressure_mpa": 0.05,
      "closure_temperature_c": 10.0,
      "service_temperature_min_c": -5.0,
      "service_temperature_max_c": 35.0,
      "flow_velocity_m_s": 2.5,
      "water_unit_weight_kn_m3": 10.0,
      "blocking_area_m2": 1.8,
      "flow_coefficient": 1.47,
      "ice_mode": "vertical",
      "ice_width_m": 1.6,
      "ice_thickness_m": 0.15,
      "ice_strength_kn_m2": 750.0,
      "ice_shape_coefficient": 0.9,
      "ice_breaking_angle_deg": 60.0,
      "drift_weight_kn": 12.0,
      "drift_velocity_m_s": 3.0,
      "drift_time_s": 1.0
    },
    "combination_factors": {
      "importance_factor": 1.0,
      "permanent_factor": 1.2,
      "variable_factors": {
        "live": 1.4,
        "wind": 1.4,
        "pressure": 1.3,
        "temperature": 1.3,
        "flow_pressure": 1.3,
        "ice_pressure": 1.3,
        "drift_impact": 1.3
      },
      "accompanying_factors": {
        "live": 0.7,
        "wind": 0.6,
        "pressure": 0.7,
        "temperature": 0.6,
        "flow_pressure": 0.6,
        "ice_pressure": 0.6,
        "drift_impact": 0.6
      },
      "quasi_permanent_factors": {
        "live": 0.4,
        "wind": 0.0,
        "pressure": 0.7,
        "temperature": 0.5,
        "flow_pressure": 0.0,
        "ice_pressure": 0.0,
        "drift_impact": 0.0
      }
    },
    "pier_foundation": {
      "base_length_m": 3.0,
      "base_width_m": 4.0,
      "allowable_bearing_kpa": 220.0,
      "friction_coefficient": 0.45,
      "required_sliding_safety": 1.2,
      "foundation_self_weight_kn": 500.0,
      "pier_self_weight_kn": 110.0,
      "buoyancy_kn": 0.0,
      "pipe_reaction_height_m": 2.2,
      "hydraulic_force_height_m": 1.4,
      "drift_force_height_m": 1.4,
      "axial_force_height_m": 2.2,
      "additional_vertical_kn": 0.0,
      "additional_horizontal_x_kn": 0.0,
      "additional_horizontal_y_kn": 0.0,
      "additional_moment_x_kn_m": 0.0,
      "additional_moment_y_kn_m": 0.0
    }
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_template_store.py -v`
Expected: PASS with 4 passing tests

- [ ] **Step 6: Commit**

```bash
git add config/shared_template.json src/cecs214_plain_pipe/__init__.py src/cecs214_plain_pipe/ui/__init__.py src/cecs214_plain_pipe/ui/template_store.py tests/test_template_store.py
git commit -m "feat: add shared template store"
```

### Task 2: Add Group-Based Template Apply Logic And Session State Helpers

**Files:**
- Create: `src/cecs214_plain_pipe/ui/template_apply.py`
- Create: `src/cecs214_plain_pipe/ui/state.py`
- Create: `tests/test_template_apply.py`
- Modify: `tests/test_engine.py`

- [ ] **Step 1: Write the failing apply/state tests**

```python
from copy import deepcopy

from cecs214_plain_pipe.models import default_project_input
from cecs214_plain_pipe.ui.template_apply import (
    APPLY_GROUPS,
    apply_template_groups,
    clear_calculation_outputs,
)
from cecs214_plain_pipe.ui.template_store import build_builtin_template


def test_apply_template_groups_updates_selected_project_sections_only() -> None:
    project = default_project_input().to_dict()
    template = build_builtin_template()
    template["project_defaults"]["geometry"]["span_m"] = 28.0
    template["project_defaults"]["material"]["steel_grade"] = "Q355"
    template["ui_preferences"]["results_tab"] = "formula"

    updated_project, updated_ui = apply_template_groups(
        project=project,
        ui_preferences={"results_tab": "summary"},
        template=template,
        selected_groups=["geometry", "ui_preferences"],
    )

    assert updated_project["geometry"]["span_m"] == 28.0
    assert updated_project["material"]["steel_grade"] == "Q235"
    assert updated_ui["results_tab"] == "formula"


def test_clear_calculation_outputs_removes_stale_results() -> None:
    state = {
        "project_input": default_project_input().to_dict(),
        "calculation_result": {"ok": True},
        "calculation_error": {"errors": ["bad input"]},
    }

    clear_calculation_outputs(state)

    assert "calculation_result" not in state
    assert "calculation_error" not in state


def test_apply_groups_constant_matches_settings_ui_sections() -> None:
    assert APPLY_GROUPS == [
        ("ui_preferences", "界面偏好"),
        ("meta", "工程信息默认值"),
        ("geometry", "管道几何"),
        ("material", "材料参数"),
        ("support_scheme", "支承形式"),
        ("actions", "作用参数"),
        ("combination_factors", "组合系数"),
        ("pier_foundation", "支墩基础参数"),
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_template_apply.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing symbol errors for `template_apply`

- [ ] **Step 3: Implement group-based merge helpers and output clearing**

```python
from __future__ import annotations

from copy import deepcopy
from typing import Any

APPLY_GROUPS = [
    ("ui_preferences", "界面偏好"),
    ("meta", "工程信息默认值"),
    ("geometry", "管道几何"),
    ("material", "材料参数"),
    ("support_scheme", "支承形式"),
    ("actions", "作用参数"),
    ("combination_factors", "组合系数"),
    ("pier_foundation", "支墩基础参数"),
]


def apply_template_groups(
    project: dict[str, Any],
    ui_preferences: dict[str, Any],
    template: dict[str, Any],
    selected_groups: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_project = deepcopy(project)
    updated_ui = deepcopy(ui_preferences)

    if "ui_preferences" in selected_groups:
        updated_ui.update(template["ui_preferences"])

    for group_name in selected_groups:
        if group_name == "ui_preferences":
            continue
        updated_project[group_name] = deepcopy(template["project_defaults"][group_name])

    return updated_project, updated_ui


def clear_calculation_outputs(state: dict[str, Any]) -> None:
    state.pop("calculation_result", None)
    state.pop("calculation_error", None)
```

And add state bootstrap helpers:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from cecs214_plain_pipe.ui.template_store import TEMPLATE_PATH, build_builtin_template, load_shared_template


def initialize_app_state(state: dict[str, Any]) -> None:
    if "shared_template" not in state:
        template, status = load_shared_template(TEMPLATE_PATH)
        state["shared_template"] = template
        state["shared_template_status"] = status
    if "ui_preferences" not in state:
        state["ui_preferences"] = dict(state["shared_template"]["ui_preferences"])
    if "project_input" not in state:
        state["project_input"] = dict(state["shared_template"]["project_defaults"])
    state.setdefault("pending_import_template_prompt", False)


def mark_import_template_prompt(state: dict[str, Any], enabled: bool = True) -> None:
    state["pending_import_template_prompt"] = enabled


def reset_template_to_builtin(state: dict[str, Any]) -> None:
    state["shared_template"] = build_builtin_template()
    state["shared_template_status"] = {"source": "builtin", "message": "Using built-in defaults."}
```

- [ ] **Step 4: Extend regression coverage for template-shaped project defaults**

Add this test to `tests/test_engine.py`:

```python
def test_default_project_input_matches_template_project_shape() -> None:
    project = default_project_input().to_dict()

    assert set(project) == {
        "meta",
        "geometry",
        "material",
        "support_scheme",
        "actions",
        "combination_factors",
        "pier_foundation",
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_template_apply.py tests/test_engine.py -v`
Expected: PASS with the new apply tests and existing engine tests green

- [ ] **Step 6: Commit**

```bash
git add src/cecs214_plain_pipe/ui/template_apply.py src/cecs214_plain_pipe/ui/state.py tests/test_template_apply.py tests/test_engine.py
git commit -m "feat: add template apply and state helpers"
```

### Task 3: Split The Workspace Into A Native Streamlit Page

**Files:**
- Create: `src/cecs214_plain_pipe/ui/form_sections.py`
- Create: `src/cecs214_plain_pipe/ui/pages/workspace.py`
- Create: `pages/1_Engineering_Workspace.py`
- Modify: `app.py`

- [ ] **Step 1: Write the failing workspace bootstrap test**

Append this smoke test to `tests/test_template_apply.py` so the refactor has a contract:

```python
from cecs214_plain_pipe.ui.state import initialize_app_state


def test_initialize_app_state_seeds_project_and_ui_preferences() -> None:
    state: dict[str, object] = {}

    initialize_app_state(state)

    assert "project_input" in state
    assert "ui_preferences" in state
    assert state["pending_import_template_prompt"] is False
```

- [ ] **Step 2: Run test to verify it fails if bootstrap is incomplete**

Run: `pytest tests/test_template_apply.py::test_initialize_app_state_seeds_project_and_ui_preferences -v`
Expected: FAIL if `initialize_app_state()` is still not creating all required keys

- [ ] **Step 3: Extract the existing workspace UI into a reusable render module**

Create `src/cecs214_plain_pipe/ui/pages/workspace.py` with this structure:

```python
from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from cecs214_plain_pipe import CalculationInputError, build_html_report, calculate_project, project_input_from_dict
from cecs214_plain_pipe.models import ProjectInput
from cecs214_plain_pipe.ui.state import initialize_app_state, mark_import_template_prompt


def render_workspace_page() -> None:
    initialize_app_state(st.session_state)
    project = load_project_input()
    result = st.session_state.get("calculation_result")

    render_workspace_header(project, result)
    render_import_template_prompt()
    open_panel("参数录入", "按工程流程录入几何、材料、荷载和支墩基础参数。")
    with st.form("plain_pipe_form"):
        edited = render_project_form(project)
        submitted = st.form_submit_button("开始计算", use_container_width=True, type="primary")
    close_panel()

    if submitted:
        st.session_state["project_input"] = edited.to_dict()
        try:
            st.session_state["calculation_result"] = calculate_project(edited).to_dict()
            st.session_state.pop("calculation_error", None)
        except CalculationInputError as exc:
            st.session_state["calculation_error"] = {"errors": exc.errors, "warnings": exc.warnings}
            st.session_state.pop("calculation_result", None)

    if "calculation_error" in st.session_state:
        render_calculation_errors(st.session_state["calculation_error"])
    if "calculation_result" in st.session_state:
        render_results(project_input_from_dict(st.session_state["project_input"]), st.session_state["calculation_result"])
    else:
        render_empty_state()


def load_project_input() -> ProjectInput:
    with st.sidebar:
        st.markdown("### 工程文件")
        uploaded = st.file_uploader("导入项目 JSON", type=["json"], label_visibility="collapsed")
        if uploaded is not None:
            parsed = json.load(uploaded)
            project = project_input_from_dict(parsed)
            st.session_state["project_input"] = project.to_dict()
            mark_import_template_prompt(st.session_state, True)
    return project_input_from_dict(st.session_state["project_input"])
```

Create `src/cecs214_plain_pipe/ui/form_sections.py` and move the project-input sections there:

- `render_meta_section(project: ProjectInput, *, key_prefix: str) -> None`
- `render_geometry_material_section(project: ProjectInput, *, key_prefix: str) -> None`
- `render_support_section(project: ProjectInput, *, key_prefix: str) -> None`
- `render_actions_section(project: ProjectInput, *, key_prefix: str) -> None`
- `render_combination_section(project: ProjectInput, *, key_prefix: str) -> None`
- `render_pier_foundation_section(project: ProjectInput, *, key_prefix: str) -> None`

Then define `render_project_form()` in `workspace.py` as:

```python
def render_project_form(project: ProjectInput) -> ProjectInput:
    st.markdown('<div class="form-stack">', unsafe_allow_html=True)
    render_meta_section(project, key_prefix="workspace")
    render_geometry_material_section(project, key_prefix="workspace")
    render_support_section(project, key_prefix="workspace")
    render_actions_section(project, key_prefix="workspace")
    render_combination_section(project, key_prefix="workspace")
    render_pier_foundation_section(project, key_prefix="workspace")
    st.markdown("</div>", unsafe_allow_html=True)
    return project
```

Move the remaining workspace-only helpers from `app.py` into `workspace.py` unchanged:

- `render_factor_editor`
- `render_results`
- `build_action_rows`
- `render_input_summary`
- `build_combination_rows`
- `build_internal_force_rows`
- `render_formula_trace`
- `render_formula_card`
- `render_workspace_header`
- `render_calculation_errors`
- `render_empty_state`
- `open_panel`
- `close_panel`
- `inject_custom_css`

Add a thin native page entrypoint:

```python
import streamlit as st

from cecs214_plain_pipe.ui.pages.workspace import inject_custom_css, render_workspace_page

st.set_page_config(page_title="平管管桥计算软件", layout="wide")
inject_custom_css()
render_workspace_page()
```

- [ ] **Step 4: Reduce `app.py` to shared bootstrap**

Replace `app.py` with:

```python
from __future__ import annotations

import streamlit as st

from cecs214_plain_pipe.ui.pages.workspace import inject_custom_css, render_workspace_page

st.set_page_config(page_title="平管管桥计算软件", layout="wide")
inject_custom_css()
render_workspace_page()
```

This keeps `streamlit run app.py` working while native pages appear in the sidebar.

- [ ] **Step 5: Run tests and a manual workspace smoke check**

Run: `pytest tests/test_template_apply.py tests/test_engine.py -v`
Expected: PASS

Run: `streamlit run app.py`
Expected: sidebar shows `Engineering Workspace` and `Settings` pages, workspace still loads, import still works

- [ ] **Step 6: Commit**

```bash
git add app.py pages/1_Engineering_Workspace.py src/cecs214_plain_pipe/ui/form_sections.py src/cecs214_plain_pipe/ui/pages/workspace.py tests/test_template_apply.py
git commit -m "refactor: split workspace into native streamlit page"
```

### Task 4: Add The Settings Page And Integrate Save/Reset/Apply Flows

**Files:**
- Create: `src/cecs214_plain_pipe/ui/pages/settings.py`
- Create: `pages/2_Settings.py`
- Modify: `src/cecs214_plain_pipe/ui/form_sections.py`
- Modify: `src/cecs214_plain_pipe/ui/pages/workspace.py`
- Modify: `src/cecs214_plain_pipe/ui/state.py`
- Modify: `src/cecs214_plain_pipe/ui/template_store.py`
- Modify: `tests/test_template_store.py`
- Modify: `tests/test_template_apply.py`

- [ ] **Step 1: Write the failing tests for reset/apply prompt behavior**

Append these tests:

```python
from cecs214_plain_pipe.ui.state import mark_import_template_prompt, reset_template_to_builtin
from cecs214_plain_pipe.ui.template_store import build_builtin_template


def test_reset_template_to_builtin_replaces_shared_template() -> None:
    state = {"shared_template": {"ui_preferences": {"preview_height": 500}, "project_defaults": {}}}

    reset_template_to_builtin(state)

    assert state["shared_template"] == build_builtin_template()


def test_mark_import_template_prompt_sets_flag() -> None:
    state: dict[str, object] = {}

    mark_import_template_prompt(state, True)

    assert state["pending_import_template_prompt"] is True
```

- [ ] **Step 2: Run tests to verify they fail if state helpers are incomplete**

Run: `pytest tests/test_template_apply.py tests/test_template_store.py -v`
Expected: FAIL until reset/apply helpers and save-path behavior are wired correctly

- [ ] **Step 3: Build the settings page renderer**

Create `src/cecs214_plain_pipe/ui/pages/settings.py`:

```python
from __future__ import annotations

import streamlit as st

from cecs214_plain_pipe.models import ProjectInput, project_input_from_dict
from cecs214_plain_pipe.ui.form_sections import (
    render_actions_section,
    render_combination_section,
    render_geometry_material_section,
    render_meta_section,
    render_pier_foundation_section,
    render_support_section,
)
from cecs214_plain_pipe.ui.state import initialize_app_state, reset_template_to_builtin
from cecs214_plain_pipe.ui.template_apply import APPLY_GROUPS, apply_template_groups, clear_calculation_outputs
from cecs214_plain_pipe.ui.template_store import TEMPLATE_PATH, save_shared_template


def render_settings_page() -> None:
    initialize_app_state(st.session_state)
    template = st.session_state["shared_template"]
    status = st.session_state["shared_template_status"]

    st.title("设置")
    st.caption(f"共享模板文件：{TEMPLATE_PATH} | 来源：{status['source']}")

    template["ui_preferences"]["results_tab"] = st.selectbox(
        "默认结果标签页",
        options=["summary", "actions", "forces", "checks", "formula", "preview"],
        index=["summary", "actions", "forces", "checks", "formula", "preview"].index(
            template["ui_preferences"]["results_tab"]
        ),
    )
    template["ui_preferences"]["preview_height"] = st.number_input(
        "计算书预览高度",
        min_value=400,
        max_value=1600,
        value=int(template["ui_preferences"]["preview_height"]),
        step=50,
    )
    template["ui_preferences"]["show_formula_trace_expanded"] = st.checkbox(
        "默认展开公式追溯",
        value=bool(template["ui_preferences"]["show_formula_trace_expanded"]),
    )
    template["ui_preferences"]["sidebar_tips_expanded"] = st.checkbox(
        "默认展开侧栏提示",
        value=bool(template["ui_preferences"]["sidebar_tips_expanded"]),
    )

    defaults = project_input_from_dict(template["project_defaults"])
    with st.form("settings_template_form"):
        defaults = render_project_defaults_form(defaults)
        save_pressed = st.form_submit_button("保存模板", type="primary", use_container_width=True)
        reset_pressed = st.form_submit_button("恢复内置默认模板", use_container_width=True)

    template["project_defaults"] = defaults.to_dict()

    if save_pressed:
        save_shared_template(TEMPLATE_PATH, template)
        st.session_state["shared_template"] = template
        st.success("共享模板已保存。")

    st.subheader("应用到当前工程")
    selected = st.multiselect(
        "选择要覆盖的模板分组",
        options=[key for key, _label in APPLY_GROUPS],
        default=[key for key, _label in APPLY_GROUPS if key != "ui_preferences"],
        format_func=lambda key: dict(APPLY_GROUPS)[key],
    )
    if st.button("应用模板到当前工程", use_container_width=True):
        updated_project, updated_ui = apply_template_groups(
            project=st.session_state["project_input"],
            ui_preferences=st.session_state["ui_preferences"],
            template=template,
            selected_groups=selected,
        )
        st.session_state["project_input"] = updated_project
        st.session_state["ui_preferences"] = updated_ui
        clear_calculation_outputs(st.session_state)
        st.success("模板已应用到当前工程。")
    if reset_pressed:
        reset_template_to_builtin(st.session_state)
        st.rerun()
```

Add a helper in the same module to keep the form manageable:

```python
def render_project_defaults_form(project: ProjectInput) -> ProjectInput:
    render_meta_section(project, key_prefix="settings")
    render_geometry_material_section(project, key_prefix="settings")
    render_support_section(project, key_prefix="settings")
    render_actions_section(project, key_prefix="settings")
    render_combination_section(project, key_prefix="settings")
    render_pier_foundation_section(project, key_prefix="settings")
    return project
```

Add the native page entrypoint:

```python
import streamlit as st

from cecs214_plain_pipe.ui.pages.workspace import inject_custom_css
from cecs214_plain_pipe.ui.pages.settings import render_settings_page

st.set_page_config(page_title="平管管桥计算软件 - 设置", layout="wide")
inject_custom_css()
render_settings_page()
```

- [ ] **Step 4: Finish import prompt integration in the workspace page**

Extend `src/cecs214_plain_pipe/ui/pages/workspace.py` with:

```python
from cecs214_plain_pipe.ui.template_apply import APPLY_GROUPS, apply_template_groups, clear_calculation_outputs


def render_import_template_prompt() -> None:
    if not st.session_state.get("pending_import_template_prompt"):
        return
    st.info("项目已导入。是否将共享模板重新应用到当前工程？")
    selected = [key for key, _label in APPLY_GROUPS if st.checkbox(f"import-apply-{key}", value=key != "ui_preferences")]
    col1, col2 = st.columns(2)
    if col1.button("应用模板到当前工程", use_container_width=True):
        updated_project, updated_ui = apply_template_groups(
            project=st.session_state["project_input"],
            ui_preferences=st.session_state["ui_preferences"],
            template=st.session_state["shared_template"],
            selected_groups=selected,
        )
        st.session_state["project_input"] = updated_project
        st.session_state["ui_preferences"] = updated_ui
        clear_calculation_outputs(st.session_state)
        st.session_state["pending_import_template_prompt"] = False
        st.success("共享模板已应用。")
    if col2.button("保留导入项目原值", use_container_width=True):
        st.session_state["pending_import_template_prompt"] = False
```

- [ ] **Step 5: Run full verification**

Run: `pytest -v`
Expected: PASS

Run: `streamlit run app.py`
Expected:
- `Settings` page renders
- editing and saving writes `config/shared_template.json`
- reset returns to built-in defaults
- import shows optional template prompt
- applying selected groups clears stale calculation results

- [ ] **Step 6: Commit**

```bash
git add app.py pages/2_Settings.py src/cecs214_plain_pipe/ui/pages/settings.py src/cecs214_plain_pipe/ui/pages/workspace.py src/cecs214_plain_pipe/ui/state.py src/cecs214_plain_pipe/ui/template_store.py tests/test_template_store.py tests/test_template_apply.py
git commit -m "feat: add settings page and template workflows"
```

## Self-Review

### Spec Coverage

- Separate `Engineering Workspace` and `Settings` pages: covered by Task 3 and Task 4
- Shared repository JSON template: covered by Task 1
- UI preferences plus project defaults: covered by Task 1 and Task 4
- Automatic defaults for new sessions: covered by Task 2 and Task 3
- Optional template apply after import: covered by Task 4
- Manual group-based re-apply to current project: covered by Task 2 and Task 4
- Built-in fallback and error handling: covered by Task 1 and Task 4
- Automated test coverage: covered by Tasks 1, 2, and 4

### Placeholder Scan

- No `TBD`, `TODO`, or deferred implementation markers remain
- Each task names exact files, commands, and target behavior
- Code steps include concrete function names and code blocks rather than abstract instructions

### Type Consistency

- Shared template keys consistently use `ui_preferences` and `project_defaults`
- Project-group names consistently mirror `ProjectInput` top-level fields
- State keys consistently use `shared_template`, `shared_template_status`, and `pending_import_template_prompt`
