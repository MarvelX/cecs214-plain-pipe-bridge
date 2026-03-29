from __future__ import annotations

import streamlit as st

from cecs214_plain_pipe.models import ApplicableAction, ProjectInput, SupportType


def _key(key_prefix: str, field_name: str) -> str:
    return f"{key_prefix}-{field_name}"


def render_project_form(project: ProjectInput, *, key_prefix: str) -> ProjectInput:
    st.markdown('<div class="form-stack">', unsafe_allow_html=True)
    render_meta_section(project, key_prefix=key_prefix)
    render_geometry_material_section(project, key_prefix=key_prefix)
    render_support_section(project, key_prefix=key_prefix)
    render_actions_section(project, key_prefix=key_prefix)
    render_combination_section(project, key_prefix=key_prefix)
    render_pier_foundation_section(project, key_prefix=key_prefix)
    st.markdown("</div>", unsafe_allow_html=True)
    return project


def render_meta_section(project: ProjectInput, *, key_prefix: str) -> None:
    with st.expander("1. 工程信息", expanded=True):
        col1, col2, col3 = st.columns(3)
        project.meta.project_name = col1.text_input("工程名称", value=project.meta.project_name, key=_key(key_prefix, "meta-project-name"))
        project.meta.project_code = col2.text_input("工程编号", value=project.meta.project_code, key=_key(key_prefix, "meta-project-code"))
        project.meta.designer = col3.text_input("设计人", value=project.meta.designer, key=_key(key_prefix, "meta-designer"))
        project.meta.notes = st.text_area("备注", value=project.meta.notes, height=80, key=_key(key_prefix, "meta-notes"))


def render_geometry_material_section(project: ProjectInput, *, key_prefix: str) -> None:
    with st.expander("2. 管道几何与材料", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        project.geometry.span_m = col1.number_input("跨径 L (m)", value=float(project.geometry.span_m), min_value=0.1, step=0.5, key=_key(key_prefix, "geometry-span-m"))
        project.geometry.outer_diameter_mm = col2.number_input("外径 D (mm)", value=float(project.geometry.outer_diameter_mm), min_value=100.0, step=10.0, key=_key(key_prefix, "geometry-outer-diameter-mm"))
        project.geometry.wall_thickness_mm = col3.number_input("壁厚 t (mm)", value=float(project.geometry.wall_thickness_mm), min_value=1.0, step=1.0, key=_key(key_prefix, "geometry-wall-thickness-mm"))
        project.geometry.corrosion_allowance_mm = col4.number_input("腐蚀裕量 (mm)", value=float(project.geometry.corrosion_allowance_mm), min_value=0.0, step=0.5, key=_key(key_prefix, "geometry-corrosion-allowance-mm"))

        col1, col2, col3, col4 = st.columns(4)
        project.geometry.insulation_weight_kn_m = col1.number_input("保温层重 (kN/m)", value=float(project.geometry.insulation_weight_kn_m), min_value=0.0, step=0.05, key=_key(key_prefix, "geometry-insulation-weight-kn-m"))
        project.geometry.lining_weight_kn_m = col2.number_input("内衬重 (kN/m)", value=float(project.geometry.lining_weight_kn_m), min_value=0.0, step=0.05, key=_key(key_prefix, "geometry-lining-weight-kn-m"))
        project.geometry.attachments_weight_kn_m = col3.number_input("附属设施重 (kN/m)", value=float(project.geometry.attachments_weight_kn_m), min_value=0.0, step=0.05, key=_key(key_prefix, "geometry-attachments-weight-kn-m"))
        project.geometry.steel_density_kn_m3 = col4.number_input("钢材重度 (kN/m3)", value=float(project.geometry.steel_density_kn_m3), min_value=1.0, step=0.5, key=_key(key_prefix, "geometry-steel-density-kn-m3"))

        col1, col2, col3, col4 = st.columns(4)
        project.geometry.water_density_kn_m3 = col1.number_input("管内水重度 (kN/m3)", value=float(project.geometry.water_density_kn_m3), min_value=1.0, step=0.5, key=_key(key_prefix, "geometry-water-density-kn-m3"))
        project.material.steel_grade = col2.text_input("钢材牌号", value=project.material.steel_grade, key=_key(key_prefix, "material-steel-grade"))
        project.material.elastic_modulus_mpa = col3.number_input("弹性模量 E (MPa)", value=float(project.material.elastic_modulus_mpa), min_value=1.0, step=1000.0, format="%.0f", key=_key(key_prefix, "material-elastic-modulus-mpa"))
        project.material.design_strength_mpa = col4.number_input("设计强度 f (MPa)", value=float(project.material.design_strength_mpa), min_value=1.0, step=5.0, key=_key(key_prefix, "material-design-strength-mpa"))

        col1, col2 = st.columns(2)
        project.material.thermal_expansion_per_c = col1.number_input("线膨胀系数 α (/°C)", value=float(project.material.thermal_expansion_per_c), min_value=0.0, step=0.000001, format="%.6f", key=_key(key_prefix, "material-thermal-expansion"))
        project.material.poisson_ratio = col2.number_input("泊松比", value=float(project.material.poisson_ratio), min_value=0.0, max_value=0.49, step=0.01, key=_key(key_prefix, "material-poisson-ratio"))


def render_support_section(project: ProjectInput, *, key_prefix: str) -> None:
    with st.expander("3. 支承形式", expanded=True):
        options = list(SupportType)
        selected_index = options.index(project.support_scheme.support_type)
        project.support_scheme.support_type = st.selectbox(
            "支承形式",
            options=options,
            index=selected_index,
            format_func=lambda item: item.label,
            key=_key(key_prefix, "support-type"),
        )
        col1, col2, col3, col4 = st.columns(4)
        project.support_scheme.support_friction_coefficient = col1.number_input("支承摩擦系数 μ", value=float(project.support_scheme.support_friction_coefficient), min_value=0.0, step=0.01, key=_key(key_prefix, "support-friction"))
        project.support_scheme.has_expansion_joint = col2.checkbox("设伸缩缝", value=project.support_scheme.has_expansion_joint, key=_key(key_prefix, "support-expansion-joint"))
        project.support_scheme.stiffener_spacing_mm = col3.number_input("加劲环间距 l0 (mm)", value=float(project.support_scheme.stiffener_spacing_mm), min_value=0.0, step=100.0, key=_key(key_prefix, "support-stiffener-spacing"))
        project.support_scheme.shell_centroid_radius_mm = col4.number_input("等效形心半径 Rk (mm)", value=float(project.support_scheme.shell_centroid_radius_mm), min_value=0.0, step=10.0, key=_key(key_prefix, "support-shell-centroid-radius"))
        project.support_scheme.stiffener_equivalent_inertia_mm4 = st.number_input(
            "加劲环等效惯性矩 Jk (mm4)",
            value=float(project.support_scheme.stiffener_equivalent_inertia_mm4),
            min_value=0.0,
            step=100000.0,
            format="%.0f",
            key=_key(key_prefix, "support-stiffener-inertia"),
        )


def render_actions_section(project: ProjectInput, *, key_prefix: str) -> None:
    with st.expander("4. 作用参数", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        project.actions.live_load_kn_m = col1.number_input("施工/检修荷载 (kN/m)", value=float(project.actions.live_load_kn_m), min_value=0.0, step=0.1, key=_key(key_prefix, "actions-live-load"))
        project.actions.wind_load_kn_m = col2.number_input("风荷载标准值 (kN/m)", value=float(project.actions.wind_load_kn_m), min_value=0.0, step=0.1, key=_key(key_prefix, "actions-wind-load"))
        project.actions.design_internal_pressure_mpa = col3.number_input("设计内水压力 (MPa)", value=float(project.actions.design_internal_pressure_mpa), min_value=0.0, step=0.05, key=_key(key_prefix, "actions-design-pressure"))
        project.actions.working_internal_pressure_mpa = col4.number_input("工作内水压力 (MPa)", value=float(project.actions.working_internal_pressure_mpa), min_value=0.0, step=0.05, key=_key(key_prefix, "actions-working-pressure"))

        col1, col2, col3, col4 = st.columns(4)
        project.actions.vacuum_pressure_mpa = col1.number_input("真空压力 (MPa)", value=float(project.actions.vacuum_pressure_mpa), min_value=0.0, step=0.01, key=_key(key_prefix, "actions-vacuum-pressure"))
        project.actions.closure_temperature_c = col2.number_input("合龙气温 T (°C)", value=float(project.actions.closure_temperature_c), step=1.0, key=_key(key_prefix, "actions-closure-temperature"))
        project.actions.service_temperature_min_c = col3.number_input("运行月平均最低气温 T1 (°C)", value=float(project.actions.service_temperature_min_c), step=1.0, key=_key(key_prefix, "actions-service-min-temperature"))
        project.actions.service_temperature_max_c = col4.number_input("运行月平均最高气温 T2 (°C)", value=float(project.actions.service_temperature_max_c), step=1.0, key=_key(key_prefix, "actions-service-max-temperature"))

        col1, col2, col3, col4 = st.columns(4)
        project.actions.flow_velocity_m_s = col1.number_input("水流平均流速 Vw (m/s)", value=float(project.actions.flow_velocity_m_s), min_value=0.0, step=0.1, key=_key(key_prefix, "actions-flow-velocity"))
        project.actions.water_unit_weight_kn_m3 = col2.number_input("河道水重度 γw (kN/m3)", value=float(project.actions.water_unit_weight_kn_m3), min_value=0.0, step=0.5, key=_key(key_prefix, "actions-water-unit-weight"))
        project.actions.blocking_area_m2 = col3.number_input("支墩阻水面积 F (m2)", value=float(project.actions.blocking_area_m2), min_value=0.0, step=0.1, key=_key(key_prefix, "actions-blocking-area"))
        project.actions.flow_coefficient = col4.number_input("水流力系数 Kf", value=float(project.actions.flow_coefficient), min_value=0.0, step=0.01, key=_key(key_prefix, "actions-flow-coefficient"))

        col1, col2, col3, col4 = st.columns(4)
        project.actions.ice_mode = col1.selectbox("融冰压力模式", options=["vertical", "sharp"], index=0 if project.actions.ice_mode == "vertical" else 1, format_func=lambda v: "竖直迎冰面" if v == "vertical" else "尖端/破冰面", key=_key(key_prefix, "actions-ice-mode"))
        project.actions.ice_width_m = col2.number_input("冰宽 b (m)", value=float(project.actions.ice_width_m), min_value=0.0, step=0.1, key=_key(key_prefix, "actions-ice-width"))
        project.actions.ice_thickness_m = col3.number_input("冰厚 ti (m)", value=float(project.actions.ice_thickness_m), min_value=0.0, step=0.01, key=_key(key_prefix, "actions-ice-thickness"))
        project.actions.ice_strength_kn_m2 = col4.number_input("冰抗压强度 fi (kN/m2)", value=float(project.actions.ice_strength_kn_m2), min_value=0.0, step=10.0, key=_key(key_prefix, "actions-ice-strength"))

        col1, col2, col3, col4 = st.columns(4)
        project.actions.ice_shape_coefficient = col1.number_input("竖直边缘支墩体型系数 mh", value=float(project.actions.ice_shape_coefficient), min_value=0.0, step=0.01, key=_key(key_prefix, "actions-ice-shape"))
        project.actions.ice_breaking_angle_deg = col2.number_input("破冰坡水平夹角 θ (°)", value=float(project.actions.ice_breaking_angle_deg), min_value=0.0, max_value=180.0, step=1.0, key=_key(key_prefix, "actions-ice-angle"))
        project.actions.drift_weight_kn = col3.number_input("漂流物重力 W (kN)", value=float(project.actions.drift_weight_kn), min_value=0.0, step=1.0, key=_key(key_prefix, "actions-drift-weight"))
        project.actions.drift_velocity_m_s = col4.number_input("漂流物流速 V (m/s)", value=float(project.actions.drift_velocity_m_s), min_value=0.0, step=0.1, key=_key(key_prefix, "actions-drift-velocity"))

        project.actions.drift_time_s = st.number_input("撞击时间 t (s)", value=float(project.actions.drift_time_s), min_value=0.1, step=0.1, key=_key(key_prefix, "actions-drift-time"))


def render_combination_section(project: ProjectInput, *, key_prefix: str) -> None:
    with st.expander("5. 组合与控制参数", expanded=True):
        col1, col2 = st.columns(2)
        project.combination_factors.importance_factor = col1.number_input("重要性系数 γ0", value=float(project.combination_factors.importance_factor), min_value=0.1, step=0.1, key=_key(key_prefix, "combination-importance-factor"))
        project.combination_factors.permanent_factor = col2.number_input("永久作用分项系数 γG", value=float(project.combination_factors.permanent_factor), min_value=0.1, step=0.1, key=_key(key_prefix, "combination-permanent-factor"))
        render_factor_editor("变量作用分项系数 γQ", project.combination_factors.variable_factors, key_prefix=key_prefix)
        render_factor_editor("伴随系数 φ", project.combination_factors.accompanying_factors, key_prefix=key_prefix)
        render_factor_editor("准永久值系数 ψ", project.combination_factors.quasi_permanent_factors, key_prefix=key_prefix)


def render_pier_foundation_section(project: ProjectInput, *, key_prefix: str) -> None:
    with st.expander("6. 支墩基础参数", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        project.pier_foundation.base_length_m = col1.number_input("基础长度 a (m)", value=float(project.pier_foundation.base_length_m), min_value=0.1, step=0.1, key=_key(key_prefix, "pier-base-length"))
        project.pier_foundation.base_width_m = col2.number_input("基础宽度 b (m)", value=float(project.pier_foundation.base_width_m), min_value=0.1, step=0.1, key=_key(key_prefix, "pier-base-width"))
        project.pier_foundation.allowable_bearing_kpa = col3.number_input("地基承载力特征值 (kPa)", value=float(project.pier_foundation.allowable_bearing_kpa), min_value=1.0, step=10.0, key=_key(key_prefix, "pier-bearing"))
        project.pier_foundation.friction_coefficient = col4.number_input("基础抗滑摩擦系数 μ", value=float(project.pier_foundation.friction_coefficient), min_value=0.0, step=0.01, key=_key(key_prefix, "pier-friction"))

        col1, col2, col3, col4 = st.columns(4)
        project.pier_foundation.required_sliding_safety = col1.number_input("抗滑稳定要求 Kc", value=float(project.pier_foundation.required_sliding_safety), min_value=0.1, step=0.1, key=_key(key_prefix, "pier-sliding-safety"))
        project.pier_foundation.foundation_self_weight_kn = col2.number_input("基础自重 (kN)", value=float(project.pier_foundation.foundation_self_weight_kn), step=5.0, key=_key(key_prefix, "pier-foundation-weight"))
        project.pier_foundation.pier_self_weight_kn = col3.number_input("墩身自重 (kN)", value=float(project.pier_foundation.pier_self_weight_kn), step=5.0, key=_key(key_prefix, "pier-self-weight"))
        project.pier_foundation.buoyancy_kn = col4.number_input("浮力 Rw (kN)", value=float(project.pier_foundation.buoyancy_kn), min_value=0.0, step=5.0, key=_key(key_prefix, "pier-buoyancy"))

        col1, col2, col3, col4 = st.columns(4)
        project.pier_foundation.pipe_reaction_height_m = col1.number_input("管道反力作用点高度 (m)", value=float(project.pier_foundation.pipe_reaction_height_m), min_value=0.0, step=0.1, key=_key(key_prefix, "pier-pipe-reaction-height"))
        project.pier_foundation.hydraulic_force_height_m = col2.number_input("水力/融冰作用点高度 (m)", value=float(project.pier_foundation.hydraulic_force_height_m), min_value=0.0, step=0.1, key=_key(key_prefix, "pier-hydraulic-height"))
        project.pier_foundation.drift_force_height_m = col3.number_input("漂流物作用点高度 (m)", value=float(project.pier_foundation.drift_force_height_m), min_value=0.0, step=0.1, key=_key(key_prefix, "pier-drift-height"))
        project.pier_foundation.axial_force_height_m = col4.number_input("轴力作用点高度 (m)", value=float(project.pier_foundation.axial_force_height_m), min_value=0.0, step=0.1, key=_key(key_prefix, "pier-axial-height"))

        col1, col2, col3, col4 = st.columns(4)
        project.pier_foundation.additional_vertical_kn = col1.number_input("附加竖向力 (kN)", value=float(project.pier_foundation.additional_vertical_kn), step=5.0, key=_key(key_prefix, "pier-additional-vertical"))
        project.pier_foundation.additional_horizontal_x_kn = col2.number_input("附加 X 向水平力 (kN)", value=float(project.pier_foundation.additional_horizontal_x_kn), step=5.0, key=_key(key_prefix, "pier-additional-horizontal-x"))
        project.pier_foundation.additional_horizontal_y_kn = col3.number_input("附加 Y 向水平力 (kN)", value=float(project.pier_foundation.additional_horizontal_y_kn), step=5.0, key=_key(key_prefix, "pier-additional-horizontal-y"))
        project.pier_foundation.additional_moment_x_kn_m = col4.number_input("附加 X 向弯矩 (kN·m)", value=float(project.pier_foundation.additional_moment_x_kn_m), step=5.0, key=_key(key_prefix, "pier-additional-moment-x"))
        project.pier_foundation.additional_moment_y_kn_m = st.number_input("附加 Y 向弯矩 (kN·m)", value=float(project.pier_foundation.additional_moment_y_kn_m), step=5.0, key=_key(key_prefix, "pier-additional-moment-y"))


def render_factor_editor(title: str, values: dict[str, float], *, key_prefix: str) -> None:
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
            key=_key(key_prefix, f"{title}-{action.value}"),
        )
