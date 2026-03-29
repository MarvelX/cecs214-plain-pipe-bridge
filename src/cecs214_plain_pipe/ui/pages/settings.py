from __future__ import annotations

import streamlit as st

from cecs214_plain_pipe import build_builtin_template
from cecs214_plain_pipe.models import ProjectInput, project_input_from_dict
from cecs214_plain_pipe.ui.form_sections import (
    render_actions_section,
    render_combination_section,
    render_geometry_material_section,
    render_meta_section,
    render_pier_foundation_section,
    render_support_section,
)
from cecs214_plain_pipe.ui.state import initialize_app_state, reset_template_to_builtin
from cecs214_plain_pipe.ui.template_apply import APPLY_GROUPS, apply_template_groups, clear_calculation_outputs
from cecs214_plain_pipe.ui.template_store import TEMPLATE_PATH, coerce_ui_preferences, save_shared_template


RESULT_TAB_OPTIONS = [
    ("summary", "输入摘要"),
    ("actions", "作用与组合"),
    ("forces", "内力与应力"),
    ("checks", "验算结论"),
    ("formula", "公式追溯"),
    ("preview", "计算书预览"),
]


def render_settings_page() -> None:
    initialize_app_state(st.session_state)
    template = st.session_state["shared_template"]
    status = st.session_state["shared_template_status"]
    ui_preferences, ui_error = coerce_ui_preferences(
        template.get("ui_preferences"),
        fallback=build_builtin_template()["ui_preferences"],
    )
    template["ui_preferences"] = ui_preferences

    st.title("设置")
    st.caption(f"共享模板文件：{TEMPLATE_PATH} | 来源：{status['source']}")
    if "message" in status:
        st.caption(status["message"])
    if "error" in status:
        st.warning(f"模板读取失败，当前使用内置默认值：{status['error']}")
    if ui_error is not None:
        st.warning(f"界面默认值无效，已回退到内置默认值：{ui_error}")

    open_panel("界面偏好", "维护共享模板中的界面默认设置。")
    tab_keys = [key for key, _label in RESULT_TAB_OPTIONS]
    template["ui_preferences"]["results_tab"] = st.selectbox(
        "默认结果标签页",
        options=tab_keys,
        index=tab_keys.index(template["ui_preferences"]["results_tab"]),
        format_func=lambda key: dict(RESULT_TAB_OPTIONS)[key],
    )
    template["ui_preferences"]["preview_height"] = st.number_input(
        "计算书预览高度",
        min_value=400,
        max_value=1600,
        value=int(template["ui_preferences"]["preview_height"]),
        step=50,
    )
    template["ui_preferences"]["show_formula_trace_expanded"] = st.checkbox(
        "默认展开公式追溯",
        value=bool(template["ui_preferences"]["show_formula_trace_expanded"]),
    )
    template["ui_preferences"]["sidebar_tips_expanded"] = st.checkbox(
        "默认展开侧栏提示",
        value=bool(template["ui_preferences"]["sidebar_tips_expanded"]),
    )
    close_panel()

    defaults = project_input_from_dict(template["project_defaults"])
    open_panel("项目默认参数", "这些参数会写入仓库级共享模板，用于初始化新工程或重新应用到当前工程。")
    with st.form("settings_template_form"):
        defaults = render_project_defaults_form(defaults)
        save_pressed = st.form_submit_button("保存模板", type="primary", use_container_width=True)
        reset_pressed = st.form_submit_button("恢复内置默认模板", use_container_width=True)
    close_panel()

    template["project_defaults"] = defaults.to_dict()

    if save_pressed:
        try:
            save_shared_template(TEMPLATE_PATH, template)
        except (TypeError, ValueError) as exc:
            st.error(f"共享模板保存失败：{exc}")
        else:
            st.session_state["shared_template"] = template
            st.session_state["shared_template_status"] = {"source": "disk", "message": f"Saved template: {TEMPLATE_PATH}"}
            st.success("共享模板已保存。")

    if reset_pressed:
        reset_template_to_builtin(st.session_state)
        st.rerun()

    open_panel("应用到当前工程", "按分组把共享模板重新应用到当前 session，不会自动保存工程文件。")
    selected = st.multiselect(
        "选择要覆盖的模板分组",
        options=[key for key, _label in APPLY_GROUPS],
        default=[key for key, _label in APPLY_GROUPS if key != "ui_preferences"],
        format_func=lambda key: dict(APPLY_GROUPS)[key],
    )
    if st.button("应用模板到当前工程", use_container_width=True):
        updated_project, updated_ui = apply_template_groups(
            project=st.session_state["project_input"],
            ui_preferences=st.session_state["ui_preferences"],
            template=template,
            selected_groups=selected,
        )
        st.session_state["project_input"] = updated_project
        st.session_state["ui_preferences"] = updated_ui
        clear_calculation_outputs(st.session_state)
        st.success("模板已应用到当前工程。")
    close_panel()


def render_project_defaults_form(project: ProjectInput) -> ProjectInput:
    render_meta_section(project, key_prefix="settings")
    render_geometry_material_section(project, key_prefix="settings")
    render_support_section(project, key_prefix="settings")
    render_actions_section(project, key_prefix="settings")
    render_combination_section(project, key_prefix="settings")
    render_pier_foundation_section(project, key_prefix="settings")
    return project


def open_panel(title: str, description: str) -> None:
    st.markdown(
        f"""
        <section class="workspace-panel">
          <div class="panel-head">
            <div>
              <h2>{title}</h2>
              <p>{description}</p>
            </div>
          </div>
        """,
        unsafe_allow_html=True,
    )


def close_panel() -> None:
    st.markdown("</section>", unsafe_allow_html=True)
