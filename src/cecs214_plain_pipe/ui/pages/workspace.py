from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as workspace_app

inject_custom_css = workspace_app.inject_custom_css
render_workspace_page = workspace_app.main
