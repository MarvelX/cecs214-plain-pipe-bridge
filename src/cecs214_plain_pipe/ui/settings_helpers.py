from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from cecs214_plain_pipe import build_builtin_template
from cecs214_plain_pipe.models import project_input_from_dict
from cecs214_plain_pipe.ui.state import reset_template_to_builtin
from cecs214_plain_pipe.ui.template_store import coerce_ui_preferences, save_shared_template

SETTINGS_TEMPLATE_DRAFT_KEY = "settings_template_draft"


def load_settings_template_draft(state: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    draft = deepcopy(state.get(SETTINGS_TEMPLATE_DRAFT_KEY, state["shared_template"]))
    builtin = build_builtin_template()

    ui_preferences, ui_error = coerce_ui_preferences(
        draft.get("ui_preferences"),
        fallback=builtin["ui_preferences"],
    )
    if ui_error is not None:
        state[SETTINGS_TEMPLATE_DRAFT_KEY] = deepcopy(state["shared_template"])
        return deepcopy(state["shared_template"]), ui_error

    try:
        defaults = project_input_from_dict(draft["project_defaults"])
    except (TypeError, ValueError) as exc:
        state[SETTINGS_TEMPLATE_DRAFT_KEY] = deepcopy(state["shared_template"])
        return deepcopy(state["shared_template"]), str(exc)

    draft["ui_preferences"] = ui_preferences
    draft["project_defaults"] = defaults.to_dict()
    state[SETTINGS_TEMPLATE_DRAFT_KEY] = deepcopy(draft)
    return draft, None


def save_settings_template_draft(state: dict[str, Any], path: Path) -> None:
    draft = deepcopy(state.get(SETTINGS_TEMPLATE_DRAFT_KEY, state["shared_template"]))
    try:
        save_shared_template(path, draft)
    except (TypeError, ValueError):
        state[SETTINGS_TEMPLATE_DRAFT_KEY] = deepcopy(state["shared_template"])
        raise
    state["shared_template"] = deepcopy(draft)
    state["shared_template_status"] = {"source": "disk", "message": f"Saved template: {path}"}
    state[SETTINGS_TEMPLATE_DRAFT_KEY] = deepcopy(draft)


def reset_settings_template_to_builtin(state: dict[str, Any]) -> None:
    reset_template_to_builtin(state)
    state[SETTINGS_TEMPLATE_DRAFT_KEY] = deepcopy(state["shared_template"])
