from cecs214_plain_pipe.ui.workspace_preferences import (
    resolve_formula_trace_expanded,
    resolve_preview_height,
    resolve_result_view_key,
    resolve_sidebar_tips_expanded,
)
from cecs214_plain_pipe.ui.state import initialize_app_state, mark_import_template_prompt, reset_template_to_builtin
from cecs214_plain_pipe.models import default_project_input
from cecs214_plain_pipe.ui.template_apply import (
    APPLY_GROUPS,
    apply_template_groups,
    clear_calculation_outputs,
)
from cecs214_plain_pipe.ui.template_store import build_builtin_template, coerce_ui_preferences


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


def test_initialize_app_state_seeds_project_and_ui_preferences() -> None:
    state: dict[str, object] = {}

    initialize_app_state(state)

    assert "project_input" in state
    assert "ui_preferences" in state
    assert state["pending_import_template_prompt"] is False


def test_reset_template_to_builtin_replaces_shared_template() -> None:
    state = {"shared_template": {"ui_preferences": {"preview_height": 500}, "project_defaults": {}}}

    reset_template_to_builtin(state)

    assert state["shared_template"] == build_builtin_template()


def test_mark_import_template_prompt_sets_flag() -> None:
    state: dict[str, object] = {}

    mark_import_template_prompt(state, True)

    assert state["pending_import_template_prompt"] is True


def test_workspace_ui_preferences_are_consumed_by_runtime_helpers() -> None:
    ui_preferences = {
        "results_tab": "checks",
        "preview_height": 840,
        "show_formula_trace_expanded": True,
        "sidebar_tips_expanded": False,
    }

    assert resolve_result_view_key(ui_preferences) == "checks"
    assert resolve_preview_height(ui_preferences) == 840
    assert resolve_formula_trace_expanded(ui_preferences) is True
    assert resolve_sidebar_tips_expanded(ui_preferences) is False


def test_workspace_ui_preferences_fall_back_for_invalid_results_tab() -> None:
    assert resolve_result_view_key({"results_tab": "not-a-real-tab"}) == "summary"


def test_coerce_ui_preferences_falls_back_for_invalid_results_tab() -> None:
    prefs, error = coerce_ui_preferences({"results_tab": "not-a-real-tab"})

    assert prefs == build_builtin_template()["ui_preferences"]
    assert error is not None
