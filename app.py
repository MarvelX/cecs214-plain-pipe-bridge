from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cecs214_plain_pipe import CalculationInputError, build_html_report, calculate_project, default_project_input, project_input_from_dict
from cecs214_plain_pipe.models import ApplicableAction, ProjectInput, SupportType
from cecs214_plain_pipe.ui import form_sections as fs
from cecs214_plain_pipe.ui.template_apply import APPLY_GROUPS, apply_template_groups, clear_calculation_outputs
from cecs214_plain_pipe.ui.state import initialize_app_state, mark_import_template_prompt


def main() -> None:
    initialize_app_state(st.session_state)
    inject_custom_css()

    project = load_project_input()
    result = st.session_state.get("calculation_result")

    render_workspace_header(project, result)
    render_import_template_prompt()
    open_panel("参数录入", "按工程流程录入几何、材料、荷载和支墩基础参数。")
    with st.form("plain_pipe_form"):
        edited = render_project_form(project)
        submitted = st.form_submit_button("开始计算", use_container_width=True, type="primary")
    close_panel()

    if submitted:
        st.session_state["project_input"] = edited.to_dict()
        try:
            st.session_state["calculation_result"] = calculate_project(edited).to_dict()
            st.session_state.pop("calculation_error", None)
        except CalculationInputError as exc:
            st.session_state["calculation_error"] = {"errors": exc.errors, "warnings": exc.warnings}
            st.session_state.pop("calculation_result", None)

    if "calculation_error" in st.session_state:
        render_calculation_errors(st.session_state["calculation_error"])

    if "calculation_result" in st.session_state:
        render_results(
            project_input_from_dict(st.session_state["project_input"]),
            st.session_state["calculation_result"],
        )
    else:
        render_empty_state()


def load_project_input() -> ProjectInput:
    default_project = default_project_input()

    with st.sidebar:
        st.markdown("### 工程文件")
        st.caption("导入已有项目 JSON，或继续编辑当前参数。")
        uploaded = st.file_uploader("导入项目 JSON", type=["json"], label_visibility="collapsed")
        if uploaded is not None:
            try:
                parsed = json.load(uploaded)
                project = project_input_from_dict(parsed)
                st.session_state["project_input"] = project.to_dict()
                mark_import_template_prompt(st.session_state, True)
                st.session_state.pop("input_error", None)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                st.session_state["input_error"] = str(exc)

        if "input_error" in st.session_state:
            st.error(f"导入 JSON 失败：{st.session_state['input_error']}")

        st.markdown("### 使用提示")
        st.markdown(
            "\n".join(
                [
                    "- 先录入几何与材料，再补荷载和支墩参数。",
                    "- 计算失败时，下方结果区会显示必须修正的输入错误。",
                    "- 计算通过后，可直接导出 JSON 和 HTML 计算书。",
                ]
            )
        )

    try:
        return project_input_from_dict(st.session_state["project_input"])
    except (TypeError, ValueError):
        fallback_payload = st.session_state.get("shared_template", {}).get("project_defaults", default_project.to_dict())
        st.session_state["project_input"] = fallback_payload
        return project_input_from_dict(st.session_state["project_input"])


def render_import_template_prompt() -> None:
    if not st.session_state.get("pending_import_template_prompt"):
        return

    st.info("项目已导入。是否将共享模板重新应用到当前工程？")
    default_selected = [key for key, _label in APPLY_GROUPS if key != "ui_preferences"]
    selected = st.multiselect(
        "选择要覆盖的模板分组",
        options=[key for key, _label in APPLY_GROUPS],
        default=default_selected,
        format_func=lambda key: dict(APPLY_GROUPS)[key],
        key="workspace-import-template-groups",
    )
    col1, col2 = st.columns(2)
    if col1.button("应用模板到当前工程", use_container_width=True):
        updated_project, updated_ui = apply_template_groups(
            project=st.session_state["project_input"],
            ui_preferences=st.session_state["ui_preferences"],
            template=st.session_state["shared_template"],
            selected_groups=selected,
        )
        st.session_state["project_input"] = updated_project
        st.session_state["ui_preferences"] = updated_ui
        clear_calculation_outputs(st.session_state)
        st.session_state["pending_import_template_prompt"] = False
        st.success("共享模板已应用。")
    if col2.button("保留导入项目原值", use_container_width=True):
        st.session_state["pending_import_template_prompt"] = False


def _legacy_render_project_form(project: ProjectInput) -> ProjectInput:
    st.markdown('<div class="form-stack">', unsafe_allow_html=True)
    with st.expander("1. 工程信息", expanded=True):
        col1, col2, col3 = st.columns(3)
        project.meta.project_name = col1.text_input("工程名称", value=project.meta.project_name)
        project.meta.project_code = col2.text_input("工程编号", value=project.meta.project_code)
        project.meta.designer = col3.text_input("设计人", value=project.meta.designer)
        project.meta.notes = st.text_area("备注", value=project.meta.notes, height=80)

    with st.expander("2. 管道几何与材料", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        project.geometry.span_m = col1.number_input("跨径 L (m)", value=float(project.geometry.span_m), min_value=0.1, step=0.5)
        project.geometry.outer_diameter_mm = col2.number_input("外径 D (mm)", value=float(project.geometry.outer_diameter_mm), min_value=100.0, step=10.0)
        project.geometry.wall_thickness_mm = col3.number_input("壁厚 t (mm)", value=float(project.geometry.wall_thickness_mm), min_value=1.0, step=1.0)
        project.geometry.corrosion_allowance_mm = col4.number_input("腐蚀裕量 (mm)", value=float(project.geometry.corrosion_allowance_mm), min_value=0.0, step=0.5)

        col1, col2, col3, col4 = st.columns(4)
        project.geometry.insulation_weight_kn_m = col1.number_input("保温层重 (kN/m)", value=float(project.geometry.insulation_weight_kn_m), min_value=0.0, step=0.05)
        project.geometry.lining_weight_kn_m = col2.number_input("内衬重 (kN/m)", value=float(project.geometry.lining_weight_kn_m), min_value=0.0, step=0.05)
        project.geometry.attachments_weight_kn_m = col3.number_input("附属设施重 (kN/m)", value=float(project.geometry.attachments_weight_kn_m), min_value=0.0, step=0.05)
        project.geometry.steel_density_kn_m3 = col4.number_input("钢材重度 (kN/m3)", value=float(project.geometry.steel_density_kn_m3), min_value=1.0, step=0.5)

        col1, col2, col3, col4 = st.columns(4)
        project.geometry.water_density_kn_m3 = col1.number_input("管内水重度 (kN/m3)", value=float(project.geometry.water_density_kn_m3), min_value=1.0, step=0.5)
        project.material.steel_grade = col2.text_input("钢材牌号", value=project.material.steel_grade)
        project.material.elastic_modulus_mpa = col3.number_input("弹性模量 E (MPa)", value=float(project.material.elastic_modulus_mpa), min_value=1.0, step=1000.0, format="%.0f")
        project.material.design_strength_mpa = col4.number_input("设计强度 f (MPa)", value=float(project.material.design_strength_mpa), min_value=1.0, step=5.0)

        col1, col2 = st.columns(2)
        project.material.thermal_expansion_per_c = col1.number_input("线膨胀系数 α (/°C)", value=float(project.material.thermal_expansion_per_c), min_value=0.0, step=0.000001, format="%.6f")
        project.material.poisson_ratio = col2.number_input("泊松比", value=float(project.material.poisson_ratio), min_value=0.0, max_value=0.49, step=0.01)

    with st.expander("3. 支承形式", expanded=True):
        options = list(SupportType)
        selected_index = options.index(project.support_scheme.support_type)
        project.support_scheme.support_type = st.selectbox(
            "支承形式",
            options=options,
            index=selected_index,
            format_func=lambda item: item.label,
        )
        col1, col2, col3, col4 = st.columns(4)
        project.support_scheme.support_friction_coefficient = col1.number_input("支承摩擦系数 μ", value=float(project.support_scheme.support_friction_coefficient), min_value=0.0, step=0.01)
        project.support_scheme.has_expansion_joint = col2.checkbox("设伸缩缝", value=project.support_scheme.has_expansion_joint)
        project.support_scheme.stiffener_spacing_mm = col3.number_input("加劲环间距 l0 (mm)", value=float(project.support_scheme.stiffener_spacing_mm), min_value=0.0, step=100.0)
        project.support_scheme.shell_centroid_radius_mm = col4.number_input("等效形心半径 Rk (mm)", value=float(project.support_scheme.shell_centroid_radius_mm), min_value=0.0, step=10.0)
        project.support_scheme.stiffener_equivalent_inertia_mm4 = st.number_input(
            "加劲环等效惯性矩 Jk (mm4)",
            value=float(project.support_scheme.stiffener_equivalent_inertia_mm4),
            min_value=0.0,
            step=1000000.0,
            format="%.0f",
        )

    with st.expander("4. 作用参数", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        project.actions.live_load_kn_m = col1.number_input("施工/检修荷载 (kN/m)", value=float(project.actions.live_load_kn_m), min_value=0.0, step=0.1)
        project.actions.wind_load_kn_m = col2.number_input("风荷载标准值 (kN/m)", value=float(project.actions.wind_load_kn_m), min_value=0.0, step=0.1)
        project.actions.design_internal_pressure_mpa = col3.number_input("设计内水压力 (MPa)", value=float(project.actions.design_internal_pressure_mpa), min_value=0.0, step=0.05)
        project.actions.working_internal_pressure_mpa = col4.number_input("工作内水压力 (MPa)", value=float(project.actions.working_internal_pressure_mpa), min_value=0.0, step=0.05)

        col1, col2, col3, col4 = st.columns(4)
        project.actions.vacuum_pressure_mpa = col1.number_input("真空压力 (MPa)", value=float(project.actions.vacuum_pressure_mpa), min_value=0.0, step=0.01)
        project.actions.closure_temperature_c = col2.number_input("合龙气温 T (°C)", value=float(project.actions.closure_temperature_c), step=1.0)
        project.actions.service_temperature_min_c = col3.number_input("运行月平均最低气温 T1 (°C)", value=float(project.actions.service_temperature_min_c), step=1.0)
        project.actions.service_temperature_max_c = col4.number_input("运行月平均最高气温 T2 (°C)", value=float(project.actions.service_temperature_max_c), step=1.0)

        col1, col2, col3, col4 = st.columns(4)
        project.actions.flow_velocity_m_s = col1.number_input("水流平均流速 Vw (m/s)", value=float(project.actions.flow_velocity_m_s), min_value=0.0, step=0.1)
        project.actions.water_unit_weight_kn_m3 = col2.number_input("河道水重度 γw (kN/m3)", value=float(project.actions.water_unit_weight_kn_m3), min_value=0.0, step=0.5)
        project.actions.blocking_area_m2 = col3.number_input("支墩阻水面积 F (m2)", value=float(project.actions.blocking_area_m2), min_value=0.0, step=0.1)
        project.actions.flow_coefficient = col4.number_input("水流力系数 Kf", value=float(project.actions.flow_coefficient), min_value=0.0, step=0.01)

        col1, col2, col3, col4 = st.columns(4)
        project.actions.ice_mode = col1.selectbox("融冰压力模式", options=["vertical", "sharp"], index=0 if project.actions.ice_mode == "vertical" else 1, format_func=lambda v: "竖直迎冰面" if v == "vertical" else "尖端/破冰面")
        project.actions.ice_width_m = col2.number_input("冰宽 b (m)", value=float(project.actions.ice_width_m), min_value=0.0, step=0.1)
        project.actions.ice_thickness_m = col3.number_input("冰厚 ti (m)", value=float(project.actions.ice_thickness_m), min_value=0.0, step=0.01)
        project.actions.ice_strength_kn_m2 = col4.number_input("冰抗压强度 fi (kN/m2)", value=float(project.actions.ice_strength_kn_m2), min_value=0.0, step=10.0)

        col1, col2, col3, col4 = st.columns(4)
        project.actions.ice_shape_coefficient = col1.number_input("竖直边缘支墩体型系数 mh", value=float(project.actions.ice_shape_coefficient), min_value=0.0, step=0.01)
        project.actions.ice_breaking_angle_deg = col2.number_input("破冰坡水平夹角 θ (°)", value=float(project.actions.ice_breaking_angle_deg), min_value=0.0, max_value=180.0, step=1.0)
        project.actions.drift_weight_kn = col3.number_input("漂流物重力 W (kN)", value=float(project.actions.drift_weight_kn), min_value=0.0, step=1.0)
        project.actions.drift_velocity_m_s = col4.number_input("漂流物流速 V (m/s)", value=float(project.actions.drift_velocity_m_s), min_value=0.0, step=0.1)

        project.actions.drift_time_s = st.number_input("撞击时间 t (s)", value=float(project.actions.drift_time_s), min_value=0.1, step=0.1)

    with st.expander("5. 组合与控制参数", expanded=True):
        col1, col2 = st.columns(2)
        project.combination_factors.importance_factor = col1.number_input("重要性系数 γ0", value=float(project.combination_factors.importance_factor), min_value=0.1, step=0.1)
        project.combination_factors.permanent_factor = col2.number_input("永久作用分项系数 γG", value=float(project.combination_factors.permanent_factor), min_value=0.1, step=0.1)
        render_factor_editor("变量作用分项系数 γQ", project.combination_factors.variable_factors)
        render_factor_editor("伴随系数 φ", project.combination_factors.accompanying_factors)
        render_factor_editor("准永久值系数 ψ", project.combination_factors.quasi_permanent_factors)

    with st.expander("6. 支墩基础参数", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        project.pier_foundation.base_length_m = col1.number_input("基础长度 a (m)", value=float(project.pier_foundation.base_length_m), min_value=0.1, step=0.1)
        project.pier_foundation.base_width_m = col2.number_input("基础宽度 b (m)", value=float(project.pier_foundation.base_width_m), min_value=0.1, step=0.1)
        project.pier_foundation.allowable_bearing_kpa = col3.number_input("地基承载力特征值 (kPa)", value=float(project.pier_foundation.allowable_bearing_kpa), min_value=1.0, step=10.0)
        project.pier_foundation.friction_coefficient = col4.number_input("基础抗滑摩擦系数 μ", value=float(project.pier_foundation.friction_coefficient), min_value=0.0, step=0.01)

        col1, col2, col3, col4 = st.columns(4)
        project.pier_foundation.required_sliding_safety = col1.number_input("抗滑稳定要求 Kc", value=float(project.pier_foundation.required_sliding_safety), min_value=0.1, step=0.1)
        project.pier_foundation.foundation_self_weight_kn = col2.number_input("基础自重 (kN)", value=float(project.pier_foundation.foundation_self_weight_kn), step=5.0)
        project.pier_foundation.pier_self_weight_kn = col3.number_input("墩身自重 (kN)", value=float(project.pier_foundation.pier_self_weight_kn), step=5.0)
        project.pier_foundation.buoyancy_kn = col4.number_input("浮力 Rw (kN)", value=float(project.pier_foundation.buoyancy_kn), min_value=0.0, step=5.0)

        col1, col2, col3, col4 = st.columns(4)
        project.pier_foundation.pipe_reaction_height_m = col1.number_input("管道反力作用点高度 (m)", value=float(project.pier_foundation.pipe_reaction_height_m), min_value=0.0, step=0.1)
        project.pier_foundation.hydraulic_force_height_m = col2.number_input("水力/融冰作用点高度 (m)", value=float(project.pier_foundation.hydraulic_force_height_m), min_value=0.0, step=0.1)
        project.pier_foundation.drift_force_height_m = col3.number_input("漂流物作用点高度 (m)", value=float(project.pier_foundation.drift_force_height_m), min_value=0.0, step=0.1)
        project.pier_foundation.axial_force_height_m = col4.number_input("轴力作用点高度 (m)", value=float(project.pier_foundation.axial_force_height_m), min_value=0.0, step=0.1)

        col1, col2, col3, col4 = st.columns(4)
        project.pier_foundation.additional_vertical_kn = col1.number_input("附加竖向力 (kN)", value=float(project.pier_foundation.additional_vertical_kn), step=5.0)
        project.pier_foundation.additional_horizontal_x_kn = col2.number_input("附加 X 向水平力 (kN)", value=float(project.pier_foundation.additional_horizontal_x_kn), step=5.0)
        project.pier_foundation.additional_horizontal_y_kn = col3.number_input("附加 Y 向水平力 (kN)", value=float(project.pier_foundation.additional_horizontal_y_kn), step=5.0)
        project.pier_foundation.additional_moment_x_kn_m = col4.number_input("附加 X 向弯矩 (kN·m)", value=float(project.pier_foundation.additional_moment_x_kn_m), step=5.0)
        project.pier_foundation.additional_moment_y_kn_m = st.number_input("附加 Y 向弯矩 (kN·m)", value=float(project.pier_foundation.additional_moment_y_kn_m), step=5.0)

    st.markdown("</div>", unsafe_allow_html=True)
    return project


def render_project_form(project: ProjectInput) -> ProjectInput:
    return fs.render_project_form(project, key_prefix="workspace")


def render_factor_editor(title: str, values: dict[str, float]) -> None:
    st.markdown(f'<div class="subsection-label">{title}</div>', unsafe_allow_html=True)
    actions = [
        ApplicableAction.LIVE,
        ApplicableAction.WIND,
        ApplicableAction.PRESSURE,
        ApplicableAction.TEMPERATURE,
        ApplicableAction.FLOW_PRESSURE,
        ApplicableAction.ICE_PRESSURE,
        ApplicableAction.DRIFT_IMPACT,
    ]
    columns = st.columns(len(actions))
    for column, action in zip(columns, actions):
        values[action.value] = column.number_input(
            action.label,
            value=float(values.get(action.value, 0.0)),
            min_value=0.0,
            step=0.1,
            key=f"{title}-{action.value}",
        )


def render_results(project: ProjectInput, result: dict) -> None:
    open_panel("结果工作区", "结果按复核顺序组织，可直接查看关键结论、公式追溯和计算书预览。")
    report_html = build_html_report(project, result)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    col1, col2 = st.columns(2)
    col1.download_button(
        "导出项目 JSON",
        data=json.dumps(project.to_dict(), ensure_ascii=False, indent=2),
        file_name=f"plain-pipe-input-{timestamp}.json",
        mime="application/json",
    )
    col2.download_button(
        "导出计算书 HTML",
        data=report_html,
        file_name=f"plain-pipe-report-{timestamp}.html",
        mime="text/html",
    )

    if result["validation_messages"]:
        st.warning("输入存在提示项，请结合下方结果复核。")

    tabs = st.tabs(["输入摘要", "作用与组合", "内力与应力", "验算结论", "公式追溯", "计算书预览"])

    with tabs[0]:
        render_input_summary(project)

    with tabs[1]:
        st.subheader("作用取值")
        st.dataframe(build_action_rows(result["action_values"]), use_container_width=True, hide_index=True)
        st.subheader("作用组合")
        st.dataframe(build_combination_rows(result["combinations"]), use_container_width=True, hide_index=True)
        with st.expander("展开查看组合分项明细", expanded=False):
            for combo in result["formula_trace"]["combinations"]:
                st.markdown(f"**{combo['name']}**")
                st.caption(combo["formula"])
                st.dataframe(combo["details"], use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("平管内力")
        st.dataframe(build_internal_force_rows(result["internal_forces"]), use_container_width=True, hide_index=True)
        st.subheader("强度控制")
        st.dataframe(result["stress_checks"]["rows"], use_container_width=True, hide_index=True)

    with tabs[3]:
        st.subheader("稳定与挠度")
        col1, col2 = st.columns(2)
        col1.dataframe([result["stability_checks"]], use_container_width=True, hide_index=True)
        col2.dataframe([result["deflection_check"]], use_container_width=True, hide_index=True)
        st.subheader("支墩验算")
        left_col, right_col = st.columns(2)
        left_col.markdown("**左支墩**")
        left_col.dataframe(result["pier_checks"]["details"]["left_pier"], use_container_width=True, hide_index=True)
        right_col.markdown("**右支墩**")
        right_col.dataframe(result["pier_checks"]["details"]["right_pier"], use_container_width=True, hide_index=True)

    with tabs[4]:
        render_formula_trace(result["formula_trace"])

    with tabs[5]:
        st.components.v1.html(report_html, height=900, scrolling=True)
    close_panel()


def build_action_rows(rows: list[dict]) -> list[dict]:
    return [
        {
            "作用": row["label"],
            "类别": row["category"],
            "竖向线荷载(kN/m)": row.get("vertical_kn_m", 0.0),
            "水平线荷载(kN/m)": row.get("horizontal_kn_m", 0.0),
            "轴向应力(MPa)": row.get("axial_stress_mpa", 0.0),
            "环向应力(MPa)": row.get("hoop_stress_mpa", 0.0),
            "真空压力(MPa)": row.get("vacuum_pressure_mpa", 0.0),
            "X向水平力(kN)": row.get("pier_horizontal_x_kn", 0.0),
            "Y向水平力(kN)": row.get("pier_horizontal_y_kn", 0.0),
            "条文": row.get("formula", ""),
        }
        for row in rows
    ]


def render_input_summary(project: ProjectInput) -> None:
    st.subheader("工程信息")
    meta_rows = [
        {"项目": "工程名称", "取值": project.meta.project_name},
        {"项目": "工程编号", "取值": project.meta.project_code},
        {"项目": "设计人", "取值": project.meta.designer or "-"},
        {"项目": "备注", "取值": project.meta.notes or "-"},
    ]
    st.dataframe(meta_rows, use_container_width=True, hide_index=True)

    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("管道几何与材料")
        geometry_rows = [
            {"项目": "跨径 L", "取值": project.geometry.span_m, "单位": "m"},
            {"项目": "外径 D", "取值": project.geometry.outer_diameter_mm, "单位": "mm"},
            {"项目": "壁厚 t", "取值": project.geometry.wall_thickness_mm, "单位": "mm"},
            {"项目": "腐蚀裕量", "取值": project.geometry.corrosion_allowance_mm, "单位": "mm"},
            {"项目": "保温层重", "取值": project.geometry.insulation_weight_kn_m, "单位": "kN/m"},
            {"项目": "内衬重", "取值": project.geometry.lining_weight_kn_m, "单位": "kN/m"},
            {"项目": "附属设施重", "取值": project.geometry.attachments_weight_kn_m, "单位": "kN/m"},
            {"项目": "钢材重度", "取值": project.geometry.steel_density_kn_m3, "单位": "kN/m3"},
            {"项目": "管内水重度", "取值": project.geometry.water_density_kn_m3, "单位": "kN/m3"},
            {"项目": "钢材牌号", "取值": project.material.steel_grade, "单位": ""},
            {"项目": "弹性模量 E", "取值": project.material.elastic_modulus_mpa, "单位": "MPa"},
            {"项目": "设计强度 f", "取值": project.material.design_strength_mpa, "单位": "MPa"},
            {"项目": "线膨胀系数 α", "取值": project.material.thermal_expansion_per_c, "单位": "/°C"},
            {"项目": "泊松比", "取值": project.material.poisson_ratio, "单位": ""},
        ]
        st.dataframe(geometry_rows, use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("支承与加劲环")
        support_rows = [
            {"项目": "支承形式", "取值": project.support_scheme.support_type.label, "单位": ""},
            {"项目": "支承摩擦系数 μ", "取值": project.support_scheme.support_friction_coefficient, "单位": ""},
            {"项目": "设伸缩缝", "取值": "是" if project.support_scheme.has_expansion_joint else "否", "单位": ""},
            {"项目": "加劲环间距 l0", "取值": project.support_scheme.stiffener_spacing_mm, "单位": "mm"},
            {"项目": "等效形心半径 Rk", "取值": project.support_scheme.shell_centroid_radius_mm, "单位": "mm"},
            {"项目": "加劲环等效惯性矩 Jk", "取值": project.support_scheme.stiffener_equivalent_inertia_mm4, "单位": "mm4"},
        ]
        st.dataframe(support_rows, use_container_width=True, hide_index=True)

    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("作用参数")
        action_rows = [
            {"项目": "施工/检修荷载", "取值": project.actions.live_load_kn_m, "单位": "kN/m"},
            {"项目": "风荷载标准值", "取值": project.actions.wind_load_kn_m, "单位": "kN/m"},
            {"项目": "设计内水压力", "取值": project.actions.design_internal_pressure_mpa, "单位": "MPa"},
            {"项目": "工作内水压力", "取值": project.actions.working_internal_pressure_mpa, "单位": "MPa"},
            {"项目": "真空压力", "取值": project.actions.vacuum_pressure_mpa, "单位": "MPa"},
            {"项目": "合龙气温 T", "取值": project.actions.closure_temperature_c, "单位": "°C"},
            {"项目": "运行月平均最低气温 T1", "取值": project.actions.service_temperature_min_c, "单位": "°C"},
            {"项目": "运行月平均最高气温 T2", "取值": project.actions.service_temperature_max_c, "单位": "°C"},
            {"项目": "水流平均流速 Vw", "取值": project.actions.flow_velocity_m_s, "单位": "m/s"},
            {"项目": "河道水重度 γw", "取值": project.actions.water_unit_weight_kn_m3, "单位": "kN/m3"},
            {"项目": "支墩阻水面积 F", "取值": project.actions.blocking_area_m2, "单位": "m2"},
            {"项目": "水流力系数 Kf", "取值": project.actions.flow_coefficient, "单位": ""},
            {"项目": "融冰模式", "取值": "竖直迎冰面" if project.actions.ice_mode == "vertical" else "尖端/破冰面", "单位": ""},
            {"项目": "冰宽 b", "取值": project.actions.ice_width_m, "单位": "m"},
            {"项目": "冰厚 ti", "取值": project.actions.ice_thickness_m, "单位": "m"},
            {"项目": "冰抗压强度 fi", "取值": project.actions.ice_strength_kn_m2, "单位": "kN/m2"},
            {"项目": "体型系数 mh", "取值": project.actions.ice_shape_coefficient, "单位": ""},
            {"项目": "破冰坡水平夹角 θ", "取值": project.actions.ice_breaking_angle_deg, "单位": "°"},
            {"项目": "漂流物重力 W", "取值": project.actions.drift_weight_kn, "单位": "kN"},
            {"项目": "漂流物流速 V", "取值": project.actions.drift_velocity_m_s, "单位": "m/s"},
            {"项目": "撞击时间 t", "取值": project.actions.drift_time_s, "单位": "s"},
        ]
        st.dataframe(action_rows, use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("组合系数")
        factor_rows = []
        factor_labels = {
            "live": "活荷载",
            "wind": "风荷载",
            "pressure": "内水压力",
            "temperature": "温度作用",
            "flow_pressure": "流水压力",
            "ice_pressure": "融冰压力",
            "drift_impact": "漂流物撞击",
        }
        for key, label in factor_labels.items():
            factor_rows.append(
                {
                    "作用": label,
                    "γQ": project.combination_factors.variable_factors.get(key, 0.0),
                    "φ": project.combination_factors.accompanying_factors.get(key, 0.0),
                    "ψ": project.combination_factors.quasi_permanent_factors.get(key, 0.0),
                }
            )
        st.dataframe(
            [{"作用": "重要性系数 γ0", "γQ": project.combination_factors.importance_factor, "φ": "", "ψ": ""},
             {"作用": "永久作用分项系数 γG", "γQ": project.combination_factors.permanent_factor, "φ": "", "ψ": ""}]
            + factor_rows,
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("支墩基础参数")
    pier_rows = [
        {"项目": "基础长度 a", "取值": project.pier_foundation.base_length_m, "单位": "m"},
        {"项目": "基础宽度 b", "取值": project.pier_foundation.base_width_m, "单位": "m"},
        {"项目": "地基承载力特征值", "取值": project.pier_foundation.allowable_bearing_kpa, "单位": "kPa"},
        {"项目": "基础抗滑摩擦系数 μ", "取值": project.pier_foundation.friction_coefficient, "单位": ""},
        {"项目": "抗滑稳定要求 Kc", "取值": project.pier_foundation.required_sliding_safety, "单位": ""},
        {"项目": "基础自重", "取值": project.pier_foundation.foundation_self_weight_kn, "单位": "kN"},
        {"项目": "墩身自重", "取值": project.pier_foundation.pier_self_weight_kn, "单位": "kN"},
        {"项目": "浮力 Rw", "取值": project.pier_foundation.buoyancy_kn, "单位": "kN"},
        {"项目": "管道反力作用点高度", "取值": project.pier_foundation.pipe_reaction_height_m, "单位": "m"},
        {"项目": "水力/融冰作用点高度", "取值": project.pier_foundation.hydraulic_force_height_m, "单位": "m"},
        {"项目": "漂流物作用点高度", "取值": project.pier_foundation.drift_force_height_m, "单位": "m"},
        {"项目": "轴力作用点高度", "取值": project.pier_foundation.axial_force_height_m, "单位": "m"},
        {"项目": "附加竖向力", "取值": project.pier_foundation.additional_vertical_kn, "单位": "kN"},
        {"项目": "附加 X 向水平力", "取值": project.pier_foundation.additional_horizontal_x_kn, "单位": "kN"},
        {"项目": "附加 Y 向水平力", "取值": project.pier_foundation.additional_horizontal_y_kn, "单位": "kN"},
        {"项目": "附加 X 向弯矩", "取值": project.pier_foundation.additional_moment_x_kn_m, "单位": "kN·m"},
        {"项目": "附加 Y 向弯矩", "取值": project.pier_foundation.additional_moment_y_kn_m, "单位": "kN·m"},
    ]
    st.dataframe(pier_rows, use_container_width=True, hide_index=True)


def build_combination_rows(rows: list[dict]) -> list[dict]:
    return [
        {
            "组合名": row["name"],
            "类型": row["combo_type"],
            "验算目的": row["purpose"],
            "条文": row.get("clause", ""),
            "说明": row.get("description", ""),
            "主导作用": row.get("lead_action_label") or "-",
            "竖向线荷载(kN/m)": row["vertical_kn_m"],
            "水平线荷载(kN/m)": row["horizontal_kn_m"],
            "轴向应力(MPa)": row["axial_stress_mpa"],
            "环向应力(MPa)": row["hoop_stress_mpa"],
            "真空压力(MPa)": row["vacuum_pressure_mpa"],
            "X向水平力(kN)": row["pier_horizontal_x_kn"],
            "Y向水平力(kN)": row["pier_horizontal_y_kn"],
        }
        for row in rows
    ]


def build_internal_force_rows(rows: list[dict]) -> list[dict]:
    return [
        {
            "组合名": row["name"],
            "组合代码": row.get("code", ""),
            "类型": row["combo_type"],
            "Mv(kN·m)": row["moment_vertical_kn_m"],
            "Mh(kN·m)": row["moment_horizontal_kn_m"],
            "M(kN·m)": row["moment_resultant_kn_m"],
            "Vv(kN)": row["shear_vertical_kn"],
            "Vh(kN)": row["shear_horizontal_kn"],
            "V(kN)": row["shear_resultant_kn"],
            "N(kN)": row["axial_force_kn"],
            "左竖反力(kN)": row["left_reaction_vertical_kn"],
            "右竖反力(kN)": row["right_reaction_vertical_kn"],
            "左横反力(kN)": row["left_reaction_horizontal_kn"],
            "右横反力(kN)": row["right_reaction_horizontal_kn"],
        }
        for row in rows
    ]


def render_formula_trace(trace: dict) -> None:
    st.subheader("截面参数公式")
    for item in trace["section"]:
        render_formula_card(item["title"], item["clause"], item["formula"], item["substitution"], item["result"])

    st.subheader("作用取值公式")
    for item in trace["actions"]:
        render_formula_card(item["title"], item["clause"], item["formula"], item["substitution"], item["result"])

    st.subheader("组合公式")
    for item in trace["combinations"]:
        with st.expander(item["name"], expanded=False):
            render_formula_card("组合总式", item["combo_type"], item["formula"], item["substitution"], item["result"])
            st.dataframe(item["details"], use_container_width=True, hide_index=True)

    st.subheader("内力公式")
    for item in trace["internal_forces"]:
        with st.expander(item["name"], expanded=False):
            for formula in item["formulae"]:
                render_formula_card(formula["title"], "", formula["formula"], formula["substitution"], formula["result"])

    st.subheader("强度验算公式")
    for item in trace["stress"]:
        with st.expander(item["name"], expanded=False):
            for formula in item["formulae"]:
                render_formula_card(formula["title"], item["status"], formula["formula"], formula["substitution"], formula["result"])

    st.subheader("稳定与挠度公式")
    for item in trace["stability"]:
        render_formula_card(item["title"], item["clause"], item["formula"], item["substitution"], item["result"])
    for item in trace["deflection"]:
        render_formula_card(item["title"], item["clause"], item["formula"], item["substitution"], item["result"])

    st.subheader("支墩验算公式")
    for side_key, side_label in (("left_pier", "左支墩"), ("right_pier", "右支墩")):
        st.markdown(f"**{side_label}**")
        for item in trace["piers"][side_key]:
            with st.expander(item["name"], expanded=False):
                for formula in item["formulae"]:
                    render_formula_card(formula["title"], item["status"], formula["formula"], formula["substitution"], formula["result"])


def render_formula_card(title: str, clause: str, formula: str, substitution: str, result: str) -> None:
    st.markdown(f"**{title}**")
    if clause:
        st.caption(clause)
    st.code(f"公式: {formula}\n代入: {substitution}\n结果: {result}", language="text")


def render_workspace_header(project: ProjectInput, result: dict | None) -> None:
    status_line = "等待计算" if result is None else "已生成最新结果"
    stress_value = "-"
    deflection_value = "-"
    pier_value = "-"
    if result is not None:
        stress_value = f"{result['stress_checks']['governing']['equivalent_stress_mpa']:.2f} MPa"
        deflection_value = f"{result['deflection_check']['deflection_mm']:.2f} mm"
        pier_value = f"{result['pier_checks']['governing']['left_pier']['qmax_kpa']:.2f} kPa"

    st.markdown(
        f"""
        <section class="workspace-hero">
          <div class="hero-copy">
            <p class="eyebrow">CECS 214:2006 · 平管工作台</p>
            <h1>{project.meta.project_name}</h1>
            <p class="hero-note">面向复核的平管管桥计算界面，参数录入、组合验算、公式追溯和计算书输出保持在同一工作面。</p>
          </div>
          <div class="hero-meta">
            <div class="hero-meta-row"><span>工程编号</span><strong>{project.meta.project_code}</strong></div>
            <div class="hero-meta-row"><span>支承形式</span><strong>{project.support_scheme.support_type.label}</strong></div>
            <div class="hero-meta-row"><span>当前状态</span><strong>{status_line}</strong></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <section class="metric-ribbon">
          <div class="metric-tile"><span>控制应力</span><strong>{stress_value}</strong></div>
          <div class="metric-tile"><span>控制挠度</span><strong>{deflection_value}</strong></div>
          <div class="metric-tile"><span>左支墩 qmax</span><strong>{pier_value}</strong></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_calculation_errors(error_state: dict) -> None:
    open_panel("输入校验", "当前参数包含必须修正的问题，系统已阻断计算。")
    for message in error_state["errors"]:
        st.error(message)
    for message in error_state["warnings"]:
        st.warning(message)
    close_panel()


def render_empty_state() -> None:
    st.markdown(
        """
        <section class="empty-stage">
          <div class="empty-stage-copy">
            <p class="eyebrow">结果区</p>
            <h2>先完成一次计算</h2>
            <p>左侧参数录入完成后点击“开始计算”，右侧会生成组合、内力、验算结论、公式追溯和计算书预览。</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


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


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
          :root {
            --bg-0: #f3efe7;
            --bg-1: #fbf8f2;
            --ink-0: #14202b;
            --ink-1: #50606f;
            --line-0: rgba(34, 43, 53, 0.12);
            --line-1: rgba(159, 119, 54, 0.22);
            --accent: #9a6a24;
            --accent-soft: #efe0c8;
            --hero: linear-gradient(135deg, #172533 0%, #21384a 38%, #82603a 100%);
          }
          .stApp {
            background:
              radial-gradient(circle at top left, rgba(154, 106, 36, 0.12), transparent 26%),
              linear-gradient(180deg, #f1ece3 0%, #f7f4ee 30%, #f8f6f2 100%);
            color: var(--ink-0);
          }
          [data-testid="stHeader"] {
            background: rgba(248, 246, 242, 0.72);
            backdrop-filter: blur(12px);
          }
          [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f5efe4 0%, #f7f3eb 100%);
            border-right: 1px solid var(--line-0);
          }
          [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.2rem;
          }
          .block-container {
            padding-top: 1.2rem;
            padding-bottom: 3rem;
            max-width: 1460px;
          }
          .workspace-hero {
            display: grid;
            grid-template-columns: 1.5fr 0.8fr;
            gap: 1rem;
            padding: 1.4rem 1.5rem;
            margin-bottom: 1rem;
            border-radius: 26px;
            background: var(--hero);
            color: #f9f5ee;
            box-shadow: 0 18px 40px rgba(23, 37, 51, 0.16);
            animation: riseIn 420ms ease-out;
          }
          .workspace-hero h1 {
            margin: 0.2rem 0 0.5rem;
            font-size: clamp(2rem, 3.6vw, 3.3rem);
            line-height: 0.98;
            letter-spacing: -0.03em;
          }
          .eyebrow {
            margin: 0;
            font-size: 0.82rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            opacity: 0.72;
          }
          .hero-note {
            max-width: 44rem;
            margin: 0;
            font-size: 0.98rem;
            color: rgba(249, 245, 238, 0.85);
          }
          .hero-meta {
            display: grid;
            gap: 0.75rem;
            align-content: end;
          }
          .hero-meta-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding-top: 0.65rem;
            border-top: 1px solid rgba(255, 248, 238, 0.18);
          }
          .hero-meta-row span {
            color: rgba(249, 245, 238, 0.65);
          }
          .hero-meta-row strong {
            font-weight: 600;
          }
          .metric-ribbon {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-bottom: 1.2rem;
            animation: fadeSlide 520ms ease-out;
          }
          .metric-tile {
            padding: 1rem 1.05rem;
            border-radius: 18px;
            background: rgba(255, 252, 246, 0.88);
            border: 1px solid var(--line-1);
            box-shadow: 0 10px 26px rgba(20, 32, 43, 0.05);
          }
          .metric-tile span {
            display: block;
            margin-bottom: 0.35rem;
            font-size: 0.84rem;
            color: var(--ink-1);
          }
          .metric-tile strong {
            font-size: 1.1rem;
            color: var(--ink-0);
          }
          .workspace-panel {
            padding: 1.1rem 1.1rem 1.2rem;
            margin-bottom: 1rem;
            border: 1px solid var(--line-0);
            border-radius: 24px;
            background: rgba(255, 253, 248, 0.88);
            box-shadow: 0 16px 30px rgba(20, 32, 43, 0.05);
            animation: fadeSlide 520ms ease-out;
          }
          .panel-head {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 1rem;
            margin-bottom: 0.8rem;
          }
          .panel-head h2 {
            margin: 0;
            font-size: 1.2rem;
            letter-spacing: -0.02em;
          }
          .panel-head p {
            margin: 0.28rem 0 0;
            color: var(--ink-1);
            font-size: 0.92rem;
          }
          .empty-stage {
            min-height: 420px;
            display: grid;
            place-items: center;
            padding: 2.4rem 1.2rem;
            border: 1px dashed var(--line-1);
            border-radius: 28px;
            background:
              radial-gradient(circle at top right, rgba(154, 106, 36, 0.08), transparent 25%),
              rgba(255, 252, 247, 0.74);
            animation: fadeSlide 520ms ease-out;
          }
          .empty-stage-copy {
            max-width: 28rem;
            text-align: center;
          }
          .empty-stage-copy h2 {
            margin: 0.2rem 0 0.55rem;
            font-size: 1.8rem;
          }
          .empty-stage-copy p {
            margin: 0;
            color: var(--ink-1);
          }
          .subsection-label {
            margin: 0.45rem 0 0.5rem;
            color: var(--accent);
            font-size: 0.82rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
          }
          .stButton > button,
          .stDownloadButton > button,
          [data-testid="stFormSubmitButton"] > button {
            border-radius: 999px;
            border: 1px solid rgba(154, 106, 36, 0.18);
            background: linear-gradient(180deg, #b27b2f 0%, #8c6023 100%);
            color: #fffaf2;
            font-weight: 600;
            transition: transform 160ms ease, box-shadow 160ms ease, filter 160ms ease;
            box-shadow: 0 10px 24px rgba(154, 106, 36, 0.18);
          }
          .stDownloadButton > button {
            background: linear-gradient(180deg, #fffaf2 0%, #f5e6ce 100%);
            color: var(--ink-0);
          }
          .stButton > button:hover,
          .stDownloadButton > button:hover,
          [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 16px 30px rgba(20, 32, 43, 0.10);
            filter: saturate(1.04);
          }
          [data-testid="stExpander"] {
            border: 1px solid rgba(34, 43, 53, 0.09);
            border-radius: 18px;
            background: rgba(255, 253, 249, 0.85);
            overflow: hidden;
          }
          [data-testid="stExpander"] details summary {
            padding-top: 0.15rem;
            padding-bottom: 0.15rem;
          }
          [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.45rem;
            padding-bottom: 0.4rem;
          }
          [data-testid="stTabs"] [data-baseweb="tab"] {
            height: 2.6rem;
            border-radius: 999px;
            padding-left: 1rem;
            padding-right: 1rem;
            background: rgba(239, 230, 214, 0.58);
            color: var(--ink-1);
          }
          [data-testid="stTabs"] [aria-selected="true"] {
            background: linear-gradient(180deg, #21384a 0%, #152634 100%);
            color: #fff8ee !important;
          }
          [data-testid="stDataFrame"] {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(34, 43, 53, 0.08);
          }
          .stCodeBlock {
            border-radius: 18px;
            border: 1px solid rgba(34, 43, 53, 0.08);
          }
          @keyframes riseIn {
            from { opacity: 0; transform: translateY(10px) scale(0.992); }
            to { opacity: 1; transform: translateY(0) scale(1); }
          }
          @keyframes fadeSlide {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @media (max-width: 1080px) {
            .workspace-hero,
            .metric-ribbon {
              grid-template-columns: 1fr;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    st.set_page_config(page_title="平管管桥计算软件", layout="wide")
    main()
