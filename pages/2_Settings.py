from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cecs214_plain_pipe.ui.pages.settings import render_settings_page
from cecs214_plain_pipe.ui.pages.workspace import inject_custom_css

st.set_page_config(page_title="平管管桥计算软件 - 设置", layout="wide")
inject_custom_css()
render_settings_page()
