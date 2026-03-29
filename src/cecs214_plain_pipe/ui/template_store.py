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

VALID_RESULTS_TAB_KEYS = {
    "summary",
    "actions",
    "forces",
    "checks",
    "formula",
    "preview",
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

    try:
        normalized = _normalize_template(raw, builtin)
        normalized["ui_preferences"], ui_error = coerce_ui_preferences(
            normalized["ui_preferences"], fallback=builtin["ui_preferences"]
        )
        if ui_error is not None:
            raise ValueError(ui_error)
        _validate_project_defaults(normalized["project_defaults"])
    except (TypeError, ValueError) as exc:
        return builtin, {"source": "builtin", "error": str(exc)}

    return normalized, {"source": "disk", "message": f"Loaded template: {path}"}


def save_shared_template(path: Path, template: dict[str, Any]) -> None:
    normalized = _normalize_template(template, build_builtin_template())
    normalized["ui_preferences"], ui_error = coerce_ui_preferences(normalized["ui_preferences"])
    if ui_error is not None:
        raise ValueError(ui_error)
    _validate_project_defaults(normalized["project_defaults"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def coerce_ui_preferences(
    candidate: Any,
    *,
    fallback: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str | None]:
    base = deepcopy(DEFAULT_UI_PREFERENCES if fallback is None else fallback)
    if candidate is None:
        return base, None
    if not isinstance(candidate, dict):
        return base, "ui_preferences must be an object"

    try:
        results_tab = candidate.get("results_tab", base["results_tab"])
        if results_tab not in VALID_RESULTS_TAB_KEYS:
            raise ValueError(f"results_tab must be one of {sorted(VALID_RESULTS_TAB_KEYS)}")
        base["results_tab"] = results_tab

        preview_height = candidate.get("preview_height", base["preview_height"])
        if isinstance(preview_height, bool) or not isinstance(preview_height, (int, float)):
            raise ValueError("preview_height must be a number")
        if preview_height <= 0:
            raise ValueError("preview_height must be greater than zero")
        base["preview_height"] = int(preview_height)

        for key in ("show_formula_trace_expanded", "sidebar_tips_expanded"):
            value = candidate.get(key, base[key])
            if not isinstance(value, bool):
                raise ValueError(f"{key} must be a boolean")
            base[key] = value
    except (TypeError, ValueError) as exc:
        return deepcopy(DEFAULT_UI_PREFERENCES if fallback is None else fallback), str(exc)

    return base, None


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
