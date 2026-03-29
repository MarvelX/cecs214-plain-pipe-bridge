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
