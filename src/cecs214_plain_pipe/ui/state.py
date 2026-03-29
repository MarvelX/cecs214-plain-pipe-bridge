from __future__ import annotations

from copy import deepcopy
from typing import Any

from cecs214_plain_pipe.ui.template_store import TEMPLATE_PATH, build_builtin_template, load_shared_template


def initialize_app_state(state: dict[str, Any]) -> None:
    if "shared_template" not in state:
        template, status = load_shared_template(TEMPLATE_PATH)
        state["shared_template"] = template
        state["shared_template_status"] = status
    if "ui_preferences" not in state:
        state["ui_preferences"] = deepcopy(state["shared_template"]["ui_preferences"])
    if "project_input" not in state:
        state["project_input"] = deepcopy(state["shared_template"]["project_defaults"])
    state.setdefault("pending_import_template_prompt", False)


def mark_import_template_prompt(state: dict[str, Any], enabled: bool = True) -> None:
    state["pending_import_template_prompt"] = enabled


def reset_template_to_builtin(state: dict[str, Any]) -> None:
    state["shared_template"] = build_builtin_template()
    state["shared_template_status"] = {"source": "builtin", "message": "Using built-in defaults."}
