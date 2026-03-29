from __future__ import annotations

from typing import Any

from cecs214_plain_pipe.ui.template_store import coerce_ui_preferences

RESULT_VIEW_OPTIONS = [
    ("summary", "输入摘要"),
    ("actions", "作用与组合"),
    ("forces", "内力与应力"),
    ("checks", "验算结论"),
    ("formula", "公式追溯"),
    ("preview", "计算书预览"),
]
RESULT_VIEW_KEYS = [key for key, _label in RESULT_VIEW_OPTIONS]
RESULT_VIEW_LABELS = {key: label for key, label in RESULT_VIEW_OPTIONS}


def resolve_ui_preferences(ui_preferences: dict[str, Any] | None) -> dict[str, Any]:
    resolved, _error = coerce_ui_preferences(ui_preferences)
    return resolved


def resolve_result_view_key(ui_preferences: dict[str, Any] | None) -> str:
    resolved = resolve_ui_preferences(ui_preferences)
    value = resolved.get("results_tab", "summary")
    return value if value in RESULT_VIEW_KEYS else "summary"


def resolve_preview_height(ui_preferences: dict[str, Any] | None) -> int:
    resolved = resolve_ui_preferences(ui_preferences)
    return int(resolved.get("preview_height", 900))


def resolve_formula_trace_expanded(ui_preferences: dict[str, Any] | None) -> bool:
    resolved = resolve_ui_preferences(ui_preferences)
    return bool(resolved.get("show_formula_trace_expanded", False))


def resolve_sidebar_tips_expanded(ui_preferences: dict[str, Any] | None) -> bool:
    resolved = resolve_ui_preferences(ui_preferences)
    return bool(resolved.get("sidebar_tips_expanded", True))
