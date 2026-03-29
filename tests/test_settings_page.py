from copy import deepcopy
from pathlib import Path

from cecs214_plain_pipe.ui.settings_helpers import SETTINGS_TEMPLATE_DRAFT_KEY, save_settings_template_draft
from cecs214_plain_pipe.ui.template_store import build_builtin_template


def test_failed_settings_save_keeps_session_template_valid(tmp_path: Path) -> None:
    shared_template = build_builtin_template()
    invalid_draft = deepcopy(shared_template)
    invalid_draft["project_defaults"]["support_scheme"]["support_type"] = "invalid-support"

    state = {
        "shared_template": shared_template,
        "shared_template_status": {"source": "disk", "message": "Loaded template"},
        SETTINGS_TEMPLATE_DRAFT_KEY: invalid_draft,
    }

    try:
        save_settings_template_draft(state, tmp_path / "shared_template.json")
    except ValueError:
        pass

    assert state["shared_template"] == shared_template
    assert state[SETTINGS_TEMPLATE_DRAFT_KEY] == shared_template
    assert not (tmp_path / "shared_template.json").exists()
