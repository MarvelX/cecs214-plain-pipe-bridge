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

    normalized = _normalize_template(raw, builtin)
    _validate_project_defaults(normalized["project_defaults"])
    return normalized, {"source": "disk", "message": f"Loaded template: {path}"}


def save_shared_template(path: Path, template: dict[str, Any]) -> None:
    normalized = _normalize_template(template, build_builtin_template())
    _validate_project_defaults(normalized["project_defaults"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _validate_project_defaults(project_defaults: dict[str, Any]) -> None:
    project_input_from_dict(project_defaults)


def _normalize_template(candidate: dict[str, Any], builtin: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(builtin)

    candidate_ui_preferences = candidate.get("ui_preferences", {})
    if isinstance(candidate_ui_preferences, dict):
        _merge_dict(normalized["ui_preferences"], candidate_ui_preferences)

    candidate_project_defaults = candidate.get("project_defaults", {})
    if isinstance(candidate_project_defaults, dict):
        for group_name, group_value in candidate_project_defaults.items():
            if group_name not in normalized["project_defaults"] or not isinstance(group_value, dict):
                continue
            _merge_dict(normalized["project_defaults"][group_name], group_value)

    return normalized


def _merge_dict(target: dict[str, Any], updates: dict[str, Any]) -> None:
    for key, value in updates.items():
        if key not in target:
            continue
        if isinstance(target[key], dict) and isinstance(value, dict):
            _merge_dict(target[key], value)
        else:
            target[key] = value
