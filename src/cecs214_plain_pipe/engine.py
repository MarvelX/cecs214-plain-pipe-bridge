from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

from .models import (
    ApplicableAction,
    CalculationResult,
    CheckResultStatus,
    ProjectInput,
    SupportType,
)


@dataclass(frozen=True)
class SupportCoefficients:
    moment_coeff: float
    shear_coeff: float
    left_reaction_coeff: float
    right_reaction_coeff: float
    deflection_coeff: float
    axial_split: Tuple[float, float]


class CalculationInputError(ValueError):
    def __init__(self, errors: List[str], warnings: List[str] | None = None):
        self.errors = errors
        self.warnings = warnings or []
        message = "；".join(errors)
        super().__init__(message)


@dataclass(frozen=True)
class CombinationScenario:
    code: str
    name: str
    combo_type: str
    purpose: str
    clause: str
    description: str
    included_actions: Tuple[str, ...]
    lead_action: str | None = None


SUPPORT_COEFFICIENTS: Dict[SupportType, SupportCoefficients] = {
    SupportType.SIMPLE_SIMPLE: SupportCoefficients(
        moment_coeff=1.0 / 8.0,
        shear_coeff=1.0 / 2.0,
        left_reaction_coeff=1.0 / 2.0,
        right_reaction_coeff=1.0 / 2.0,
        deflection_coeff=5.0 / 384.0,
        axial_split=(0.0, 0.0),
    ),
    SupportType.FIXED_SIMPLE: SupportCoefficients(
        moment_coeff=1.0 / 8.0,
        shear_coeff=5.0 / 8.0,
        left_reaction_coeff=5.0 / 8.0,
        right_reaction_coeff=3.0 / 8.0,
        deflection_coeff=0.00542,
        axial_split=(1.0, 0.0),
    ),
    SupportType.FIXED_FIXED: SupportCoefficients(
        moment_coeff=1.0 / 12.0,
        shear_coeff=1.0 / 2.0,
        left_reaction_coeff=1.0 / 2.0,
        right_reaction_coeff=1.0 / 2.0,
        deflection_coeff=1.0 / 384.0,
        axial_split=(0.5, 0.5),
    ),
}


COMBINATION_SCENARIOS: Tuple[CombinationScenario, ...] = (
    CombinationScenario(
        code="ULS-STRENGTH-PRESSURE",
        name="强度计算 1",
        combo_type="ULS",
        purpose="pipe_strength",
        clause="5.2.2 / 5.2.7",
        description="承载力极限状态强度计算，设计内水压力主导。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.PRESSURE.value,
            ApplicableAction.LIVE.value,
            ApplicableAction.WIND.value,
            ApplicableAction.TEMPERATURE.value,
        ),
        lead_action=ApplicableAction.PRESSURE.value,
    ),
    CombinationScenario(
        code="ULS-STRENGTH-WIND",
        name="强度计算 2",
        combo_type="ULS",
        purpose="pipe_strength",
        clause="5.2.2 / 5.2.7",
        description="承载力极限状态强度计算，风荷载主导。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.WIND.value,
            ApplicableAction.PRESSURE.value,
            ApplicableAction.LIVE.value,
            ApplicableAction.TEMPERATURE.value,
        ),
        lead_action=ApplicableAction.WIND.value,
    ),
    CombinationScenario(
        code="ULS-STRENGTH-LIVE",
        name="强度计算 3",
        combo_type="ULS",
        purpose="pipe_strength",
        clause="5.2.2 / 5.2.7",
        description="承载力极限状态强度计算，施工或检修荷载主导。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.LIVE.value,
            ApplicableAction.PRESSURE.value,
            ApplicableAction.WIND.value,
            ApplicableAction.TEMPERATURE.value,
        ),
        lead_action=ApplicableAction.LIVE.value,
    ),
    CombinationScenario(
        code="ULS-STABILITY-VACUUM",
        name="稳定计算 1",
        combo_type="ULS",
        purpose="pipe_stability",
        clause="5.2.2 / 8.1.2",
        description="承载力极限状态稳定计算，真空压力主导。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.VACUUM.value,
            ApplicableAction.WIND.value,
            ApplicableAction.LIVE.value,
        ),
        lead_action=ApplicableAction.VACUUM.value,
    ),
    CombinationScenario(
        code="ULS-PIER-FLOW",
        name="支墩计算 1",
        combo_type="ULS",
        purpose="pier",
        clause="5.2.2 / 10.2",
        description="支墩基础验算，流水压力主导。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.PRESSURE.value,
            ApplicableAction.TEMPERATURE.value,
            ApplicableAction.FLOW_PRESSURE.value,
        ),
        lead_action=ApplicableAction.FLOW_PRESSURE.value,
    ),
    CombinationScenario(
        code="ULS-PIER-ICE",
        name="支墩计算 2",
        combo_type="ULS",
        purpose="pier",
        clause="5.2.2 / 10.2",
        description="支墩基础验算，融冰压力主导。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.PRESSURE.value,
            ApplicableAction.TEMPERATURE.value,
            ApplicableAction.ICE_PRESSURE.value,
        ),
        lead_action=ApplicableAction.ICE_PRESSURE.value,
    ),
    CombinationScenario(
        code="ULS-PIER-DRIFT",
        name="支墩计算 3",
        combo_type="ULS",
        purpose="pier",
        clause="5.2.2 / 10.2",
        description="支墩基础验算，漂流物撞击主导。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.PRESSURE.value,
            ApplicableAction.TEMPERATURE.value,
            ApplicableAction.DRIFT_IMPACT.value,
        ),
        lead_action=ApplicableAction.DRIFT_IMPACT.value,
    ),
    CombinationScenario(
        code="SLS-SHORT-PRESSURE",
        name="短期组合 1",
        combo_type="SLS_SHORT",
        purpose="service_short",
        clause="5.3.3",
        description="正常使用极限状态短期组合，工作内水压力主导。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.PRESSURE.value,
            ApplicableAction.LIVE.value,
            ApplicableAction.WIND.value,
            ApplicableAction.TEMPERATURE.value,
        ),
        lead_action=ApplicableAction.PRESSURE.value,
    ),
    CombinationScenario(
        code="SLS-SHORT-LIVE",
        name="短期组合 2",
        combo_type="SLS_SHORT",
        purpose="service_short",
        clause="5.3.3",
        description="正常使用极限状态短期组合，施工或检修荷载主导。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.LIVE.value,
            ApplicableAction.PRESSURE.value,
            ApplicableAction.WIND.value,
            ApplicableAction.TEMPERATURE.value,
        ),
        lead_action=ApplicableAction.LIVE.value,
    ),
    CombinationScenario(
        code="SLS-SHORT-WIND",
        name="短期组合 3",
        combo_type="SLS_SHORT",
        purpose="service_short",
        clause="5.3.3",
        description="正常使用极限状态短期组合，风荷载主导。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.WIND.value,
            ApplicableAction.PRESSURE.value,
            ApplicableAction.LIVE.value,
            ApplicableAction.TEMPERATURE.value,
        ),
        lead_action=ApplicableAction.WIND.value,
    ),
    CombinationScenario(
        code="SLS-LONG",
        name="长期组合",
        combo_type="SLS_LONG",
        purpose="service_long",
        clause="5.3.4",
        description="正常使用极限状态长期准永久组合。",
        included_actions=(
            ApplicableAction.DEAD.value,
            ApplicableAction.PRESSURE.value,
            ApplicableAction.LIVE.value,
            ApplicableAction.TEMPERATURE.value,
        ),
    ),
)


def calculate_project(project: ProjectInput) -> CalculationResult:
    validation = validate_project_input(project)
    if validation["errors"]:
        raise CalculationInputError(validation["errors"], validation["warnings"])
    validation_messages = validation["warnings"]
    derived = _derive_section(project)
    action_values = _build_action_values(project, derived)
    combinations = _build_combinations(project, action_values)
    internal_forces = _calculate_internal_forces(project, derived, combinations)
    stress_checks = _calculate_stress_checks(project, derived, internal_forces)
    stability_checks = _calculate_stability(project)
    deflection_check = _calculate_deflection(project, derived, combinations)
    pier_checks = _calculate_pier_checks(project, internal_forces)
    formula_trace = _build_formula_trace(
        project,
        derived,
        action_values,
        combinations,
        internal_forces,
        stress_checks,
        stability_checks,
        deflection_check,
        pier_checks,
    )
    report_context = _build_report_context(
        project,
        derived,
        action_values,
        combinations,
        internal_forces,
        stress_checks,
        stability_checks,
        deflection_check,
        pier_checks,
        formula_trace,
        validation_messages,
    )
    return CalculationResult(
        derived_section=derived,
        action_values=action_values,
        combinations=combinations,
        internal_forces=internal_forces,
        stress_checks=stress_checks,
        stability_checks=stability_checks,
        deflection_check=deflection_check,
        pier_checks=pier_checks,
        formula_trace=formula_trace,
        report_context=report_context,
        validation_messages=validation_messages,
    )


def validate_project_input(project: ProjectInput) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    effective_thickness_mm = project.geometry.wall_thickness_mm - project.geometry.corrosion_allowance_mm
    inner_diameter_mm = project.geometry.outer_diameter_mm - 2.0 * effective_thickness_mm

    if project.geometry.span_m <= 0:
        errors.append("跨径必须大于零。")
    if project.geometry.wall_thickness_mm <= 0:
        errors.append("管壁厚度必须大于零。")
    if project.geometry.corrosion_allowance_mm < 0:
        errors.append("腐蚀裕量不能小于零。")
    if effective_thickness_mm <= 0:
        errors.append("扣除腐蚀裕量后的有效壁厚必须大于零。")
    if project.geometry.outer_diameter_mm <= 0:
        errors.append("外径必须大于零。")
    if inner_diameter_mm <= 0:
        errors.append("截面几何无效：内径必须大于零。")
    if project.geometry.steel_density_kn_m3 <= 0:
        errors.append("钢材重度必须大于零。")
    if project.geometry.water_density_kn_m3 <= 0:
        errors.append("管内水重度必须大于零。")
    if project.material.elastic_modulus_mpa <= 0:
        errors.append("钢材弹性模量必须大于零。")
    if project.material.design_strength_mpa <= 0:
        errors.append("设计强度必须大于零。")
    if not (0.0 <= project.material.poisson_ratio < 0.5):
        errors.append("泊松比必须在 0 到 0.5 之间。")
    if project.material.thermal_expansion_per_c < 0:
        errors.append("线膨胀系数不能小于零。")
    if project.actions.design_internal_pressure_mpa < 0 or project.actions.working_internal_pressure_mpa < 0:
        errors.append("内水压力不能小于零。")
    if project.actions.vacuum_pressure_mpa < 0:
        errors.append("真空压力不能小于零。")
    if project.actions.flow_velocity_m_s < 0:
        errors.append("水流流速不能小于零。")
    if project.actions.drift_time_s <= 0:
        errors.append("漂流物撞击时间必须大于零。")
    if project.actions.ice_breaking_angle_deg < 0 or project.actions.ice_breaking_angle_deg > 180:
        errors.append("破冰坡水平夹角必须在 0 到 180 度之间。")
    if project.support_scheme.support_friction_coefficient < 0:
        errors.append("支承摩擦系数不能小于零。")
    if project.support_scheme.stiffener_spacing_mm < 0 or project.support_scheme.stiffener_equivalent_inertia_mm4 < 0:
        errors.append("加劲环参数不能小于零。")
    if project.support_scheme.shell_centroid_radius_mm < 0:
        errors.append("等效形心半径不能小于零。")
    if project.pier_foundation.base_length_m <= 0 or project.pier_foundation.base_width_m <= 0:
        errors.append("基础平面尺寸必须大于零。")
    if project.pier_foundation.allowable_bearing_kpa <= 0:
        errors.append("地基承载力特征值必须大于零。")
    if project.pier_foundation.friction_coefficient < 0:
        errors.append("基础抗滑摩擦系数不能小于零。")
    if project.pier_foundation.required_sliding_safety <= 0:
        errors.append("抗滑稳定要求必须大于零。")

    if project.actions.working_internal_pressure_mpa > project.actions.design_internal_pressure_mpa:
        warnings.append("工作内水压力大于设计内水压力，请复核压力输入。")
    if project.actions.vacuum_pressure_mpa == 0:
        warnings.append("未启用真空压力，稳定验算将按满足处理。")

    return {"errors": errors, "warnings": warnings}


def _derive_section(project: ProjectInput) -> Dict[str, Any]:
    geometry = project.geometry
    thickness_mm = geometry.wall_thickness_mm - geometry.corrosion_allowance_mm
    outer_d_mm = geometry.outer_diameter_mm
    inner_d_mm = outer_d_mm - 2.0 * thickness_mm
    if thickness_mm <= 0:
        raise CalculationInputError(["扣除腐蚀裕量后的有效壁厚必须大于零。"])
    if inner_d_mm <= 0:
        raise CalculationInputError(["截面几何无效：内径必须大于零。"])
    outer_r_mm = outer_d_mm / 2.0
    inner_r_mm = inner_d_mm / 2.0
    area_mm2 = math.pi / 4.0 * (outer_d_mm**2 - inner_d_mm**2)
    inertia_mm4 = math.pi / 64.0 * (outer_d_mm**4 - inner_d_mm**4)
    section_modulus_mm3 = inertia_mm4 / outer_r_mm
    radius_of_gyration_mm = math.sqrt(inertia_mm4 / area_mm2)
    steel_area_m2 = area_mm2 / 1e6
    water_area_m2 = math.pi / 4.0 * (inner_d_mm / 1000.0) ** 2
    steel_weight_kn_m = steel_area_m2 * geometry.steel_density_kn_m3
    water_weight_kn_m = water_area_m2 * geometry.water_density_kn_m3
    total_dead_kn_m = (
        steel_weight_kn_m
        + water_weight_kn_m
        + geometry.insulation_weight_kn_m
        + geometry.lining_weight_kn_m
        + geometry.attachments_weight_kn_m
    )
    return {
        "effective_thickness_mm": thickness_mm,
        "inner_diameter_mm": inner_d_mm,
        "outer_radius_mm": outer_r_mm,
        "inner_radius_mm": inner_r_mm,
        "area_mm2": area_mm2,
        "inertia_mm4": inertia_mm4,
        "section_modulus_mm3": section_modulus_mm3,
        "radius_of_gyration_mm": radius_of_gyration_mm,
        "steel_weight_kn_m": steel_weight_kn_m,
        "water_weight_kn_m": water_weight_kn_m,
        "total_dead_load_kn_m": total_dead_kn_m,
    }


def _build_action_values(project: ProjectInput, derived: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions = project.actions
    geometry = project.geometry
    material = project.material
    support = project.support_scheme
    ri = derived["inner_radius_mm"]
    t = derived["effective_thickness_mm"]
    steel_weight_kn_m = derived["steel_weight_kn_m"]
    water_weight_kn_m = derived["water_weight_kn_m"]

    design_pressure_stress = actions.design_internal_pressure_mpa * ri / (2.0 * t)
    working_pressure_stress = actions.working_internal_pressure_mpa * ri / (2.0 * t)
    hoop_design_stress = actions.design_internal_pressure_mpa * ri / t
    hoop_working_stress = actions.working_internal_pressure_mpa * ri / t

    delta_t = abs(
        (actions.service_temperature_max_c - actions.closure_temperature_c)
        - (actions.service_temperature_max_c - actions.service_temperature_min_c) / 2.0
    )
    restraint_factor = 0.0 if support.support_type == SupportType.SIMPLE_SIMPLE else 1.0
    if support.has_expansion_joint:
        restraint_factor *= 0.5
    temperature_stress = material.thermal_expansion_per_c * material.elastic_modulus_mpa * delta_t * restraint_factor

    flow_pressure_kn = (
        actions.flow_coefficient
        * actions.water_unit_weight_kn_m3
        * (actions.flow_velocity_m_s**2)
        / (2.0 * 9.81)
        * actions.blocking_area_m2
    )
    if actions.ice_mode == "vertical":
        ice_vertical_kn = (
            actions.ice_shape_coefficient
            * actions.ice_strength_kn_m2
            * actions.ice_width_m
            * actions.ice_thickness_m
        )
        ice_horizontal_kn = 0.0
    else:
        ice_vertical_kn = (
            0.7
            * actions.ice_strength_kn_m2
            * actions.ice_width_m
            * (actions.ice_thickness_m**2)
        )
        ice_horizontal_kn = ice_vertical_kn * math.tan(math.radians(actions.ice_breaking_angle_deg))

    drift_impact_kn = actions.drift_weight_kn * actions.drift_velocity_m_s / (9.81 * actions.drift_time_s)

    return [
        {
            "action": ApplicableAction.DEAD.value,
            "label": ApplicableAction.DEAD.label,
            "category": "permanent",
            "vertical_kn_m": derived["total_dead_load_kn_m"],
            "horizontal_kn_m": 0.0,
            "axial_stress_mpa": 0.0,
            "hoop_stress_mpa": 0.0,
            "vacuum_pressure_mpa": 0.0,
            "pier_horizontal_x_kn": 0.0,
            "pier_horizontal_y_kn": 0.0,
            "formula": "4.2.1 按实际尺寸与单位体积自重计算",
            "formula_expression": "g = g_steel + g_water + g_insulation + g_lining + g_attachment",
            "formula_substitution": (
                f"g = {steel_weight_kn_m:.6f} + {water_weight_kn_m:.6f} + "
                f"{geometry.insulation_weight_kn_m:.6f} + {geometry.lining_weight_kn_m:.6f} + "
                f"{geometry.attachments_weight_kn_m:.6f}"
            ),
        },
        {
            "action": ApplicableAction.LIVE.value,
            "label": ApplicableAction.LIVE.label,
            "category": "variable",
            "vertical_kn_m": actions.live_load_kn_m,
            "horizontal_kn_m": 0.0,
            "axial_stress_mpa": 0.0,
            "hoop_stress_mpa": 0.0,
            "vacuum_pressure_mpa": 0.0,
            "pier_horizontal_x_kn": 0.0,
            "pier_horizontal_y_kn": 0.0,
            "formula": "4.3.6 施工安装荷载或检修荷载",
            "formula_expression": "q_live = 用户输入",
            "formula_substitution": f"q_live = {actions.live_load_kn_m:.6f} kN/m",
        },
        {
            "action": ApplicableAction.WIND.value,
            "label": ApplicableAction.WIND.label,
            "category": "variable",
            "vertical_kn_m": 0.0,
            "horizontal_kn_m": actions.wind_load_kn_m,
            "axial_stress_mpa": 0.0,
            "hoop_stress_mpa": 0.0,
            "vacuum_pressure_mpa": 0.0,
            "pier_horizontal_x_kn": 0.0,
            "pier_horizontal_y_kn": 0.0,
            "formula": "4.3.1 风荷载标准值手工录入",
            "formula_expression": "q_wind = 用户输入",
            "formula_substitution": f"q_wind = {actions.wind_load_kn_m:.6f} kN/m",
        },
        {
            "action": ApplicableAction.PRESSURE.value,
            "label": ApplicableAction.PRESSURE.label,
            "category": "variable",
            "vertical_kn_m": 0.0,
            "horizontal_kn_m": 0.0,
            "axial_stress_mpa": design_pressure_stress,
            "axial_stress_service_mpa": working_pressure_stress,
            "hoop_stress_mpa": hoop_design_stress,
            "hoop_stress_service_mpa": hoop_working_stress,
            "vacuum_pressure_mpa": 0.0,
            "pier_horizontal_x_kn": 0.0,
            "pier_horizontal_y_kn": 0.0,
            "formula": "7.2.1 内压产生环向应力；闭口端按薄壁圆筒取纵向应力",
            "formula_expression": "σx = p r / (2 t), σθ = p r / t",
            "formula_substitution": (
                f"σx = {actions.design_internal_pressure_mpa:.6f} × {ri:.6f} / (2 × {t:.6f}), "
                f"σθ = {actions.design_internal_pressure_mpa:.6f} × {ri:.6f} / {t:.6f}"
            ),
        },
        {
            "action": ApplicableAction.TEMPERATURE.value,
            "label": ApplicableAction.TEMPERATURE.label,
            "category": "variable",
            "vertical_kn_m": 0.0,
            "horizontal_kn_m": 0.0,
            "axial_stress_mpa": temperature_stress,
            "hoop_stress_mpa": 0.0,
            "vacuum_pressure_mpa": 0.0,
            "pier_horizontal_x_kn": 0.0,
            "pier_horizontal_y_kn": 0.0,
            "delta_t_c": delta_t,
            "formula": "4.3.4 与 7.2.2 温度作用按约束应力计算",
            "formula_expression": "σt = α E Δt × η",
            "formula_substitution": (
                f"σt = {material.thermal_expansion_per_c:.8f} × {material.elastic_modulus_mpa:.3f} × "
                f"{delta_t:.6f} × {restraint_factor:.6f}"
            ),
        },
        {
            "action": ApplicableAction.VACUUM.value,
            "label": ApplicableAction.VACUUM.label,
            "category": "variable",
            "vertical_kn_m": 0.0,
            "horizontal_kn_m": 0.0,
            "axial_stress_mpa": 0.0,
            "hoop_stress_mpa": 0.0,
            "vacuum_pressure_mpa": actions.vacuum_pressure_mpa,
            "pier_horizontal_x_kn": 0.0,
            "pier_horizontal_y_kn": 0.0,
            "formula": "4.3.3 真空压力标准值",
            "formula_expression": "Fv = 用户输入",
            "formula_substitution": f"Fv = {actions.vacuum_pressure_mpa:.6f} MPa",
        },
        {
            "action": ApplicableAction.FLOW_PRESSURE.value,
            "label": ApplicableAction.FLOW_PRESSURE.label,
            "category": "variable",
            "vertical_kn_m": 0.0,
            "horizontal_kn_m": 0.0,
            "axial_stress_mpa": 0.0,
            "hoop_stress_mpa": 0.0,
            "vacuum_pressure_mpa": 0.0,
            "pier_horizontal_x_kn": flow_pressure_kn,
            "pier_horizontal_y_kn": 0.0,
            "formula": "4.3.7 作用在支墩上的流水压力标准值",
            "formula_expression": "Fd = Kf γw Vw² F / (2 g)",
            "formula_substitution": (
                f"Fd = {actions.flow_coefficient:.6f} × {actions.water_unit_weight_kn_m3:.6f} × "
                f"{actions.flow_velocity_m_s:.6f}² × {actions.blocking_area_m2:.6f} / (2 × 9.81)"
            ),
        },
        {
            "action": ApplicableAction.ICE_PRESSURE.value,
            "label": ApplicableAction.ICE_PRESSURE.label,
            "category": "variable",
            "vertical_kn_m": 0.0,
            "horizontal_kn_m": 0.0,
            "axial_stress_mpa": 0.0,
            "hoop_stress_mpa": 0.0,
            "vacuum_pressure_mpa": 0.0,
            "pier_horizontal_x_kn": ice_horizontal_kn,
            "pier_horizontal_y_kn": ice_vertical_kn,
            "formula": "4.3.9 融冰压力标准值",
            "formula_expression": (
                "Fiv = mh fi b ti" if actions.ice_mode == "vertical" else "Fiv = 0.7 fi b ti², Fih = Fiv tanθ"
            ),
            "formula_substitution": (
                f"Fiv = {actions.ice_shape_coefficient:.6f} × {actions.ice_strength_kn_m2:.6f} × "
                f"{actions.ice_width_m:.6f} × {actions.ice_thickness_m:.6f}"
                if actions.ice_mode == "vertical"
                else (
                    f"Fiv = 0.7 × {actions.ice_strength_kn_m2:.6f} × {actions.ice_width_m:.6f} × "
                    f"{actions.ice_thickness_m:.6f}², Fih = Fiv × tan({actions.ice_breaking_angle_deg:.6f}°)"
                )
            ),
        },
        {
            "action": ApplicableAction.DRIFT_IMPACT.value,
            "label": ApplicableAction.DRIFT_IMPACT.label,
            "category": "variable",
            "vertical_kn_m": 0.0,
            "horizontal_kn_m": 0.0,
            "axial_stress_mpa": 0.0,
            "hoop_stress_mpa": 0.0,
            "vacuum_pressure_mpa": 0.0,
            "pier_horizontal_x_kn": drift_impact_kn,
            "pier_horizontal_y_kn": 0.0,
            "formula": "4.4.1 漂流物对支墩撞击力标准值",
            "formula_expression": "P = W V / (g t)",
            "formula_substitution": (
                f"P = {actions.drift_weight_kn:.6f} × {actions.drift_velocity_m_s:.6f} / "
                f"(9.81 × {actions.drift_time_s:.6f})"
            ),
        },
    ]


def _build_combinations(project: ProjectInput, action_values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    action_lookup = {item["action"]: item for item in action_values}
    combinations: List[Dict[str, Any]] = []

    for scenario in COMBINATION_SCENARIOS:
        if not _scenario_is_applicable(scenario, action_lookup):
            continue
        combinations.append(_sum_combination(project, action_lookup, scenario))

    if not combinations:
        combinations.append(
            _sum_combination(
                project,
                action_lookup,
                CombinationScenario(
                    code="ULS-PERM",
                    name="永久作用组合",
                    combo_type="ULS",
                    purpose="pipe_strength",
                    clause="5.2.2",
                    description="仅永久作用的保底组合。",
                    included_actions=(ApplicableAction.DEAD.value,),
                ),
            )
        )
    return combinations


def _sum_combination(
    project: ProjectInput,
    action_lookup: Dict[str, Dict[str, Any]],
    scenario: CombinationScenario,
) -> Dict[str, Any]:
    factors = project.combination_factors
    totals = {
        "vertical_kn_m": 0.0,
        "horizontal_kn_m": 0.0,
        "axial_stress_mpa": 0.0,
        "hoop_stress_mpa": 0.0,
        "vacuum_pressure_mpa": 0.0,
        "pier_horizontal_x_kn": 0.0,
        "pier_horizontal_y_kn": 0.0,
    }
    contribution_rows: List[Dict[str, Any]] = []

    for action_name in scenario.included_actions:
        item = action_lookup[action_name]
        factor = _resolve_combination_factor(factors, scenario, item)

        for key in totals:
            value = item.get(key, 0.0)
            if action_name == ApplicableAction.PRESSURE.value and scenario.combo_type != "ULS":
                if key == "axial_stress_mpa":
                    value = item.get("axial_stress_service_mpa", value)
                elif key == "hoop_stress_mpa":
                    value = item.get("hoop_stress_service_mpa", value)
            totals[key] += factor * value

        contribution_rows.append(
            {
                "action": action_name,
                "label": item["label"],
                "factor": factor,
                "vertical_contribution_kn_m": factor * item.get("vertical_kn_m", 0.0),
                "horizontal_contribution_kn_m": factor * item.get("horizontal_kn_m", 0.0),
                "axial_contribution_mpa": factor * (
                    item.get("axial_stress_service_mpa", item.get("axial_stress_mpa", 0.0))
                    if action_name == ApplicableAction.PRESSURE.value and scenario.combo_type != "ULS"
                    else item.get("axial_stress_mpa", 0.0)
                ),
                "hoop_contribution_mpa": factor * (
                    item.get("hoop_stress_service_mpa", item.get("hoop_stress_mpa", 0.0))
                    if action_name == ApplicableAction.PRESSURE.value and scenario.combo_type != "ULS"
                    else item.get("hoop_stress_mpa", 0.0)
                ),
            }
        )

    return {
        "name": scenario.name,
        "code": scenario.code,
        "combo_type": scenario.combo_type,
        "lead_action": scenario.lead_action,
        "lead_action_label": (
            ApplicableAction(scenario.lead_action).label if scenario.lead_action is not None else ""
        ),
        "purpose": scenario.purpose,
        "clause": scenario.clause,
        "description": scenario.description,
        **totals,
        "contributors": contribution_rows,
        "formula_expression": (
            "S = Σ(γG·Gk) + γQ1·Q1 + φc·Σ(γQj·Qj)"
            if scenario.combo_type == "ULS"
            else ("Ss = Σ(CG·Gk) + CQ1·Q1 + φc·Σ(CQj·Qj)" if scenario.combo_type == "SLS_SHORT" else "Sl = Σ(CG·Gk) + Σ(CQ·ψq·Qk)")
        ),
    }


def _scenario_is_applicable(
    scenario: CombinationScenario,
    action_lookup: Dict[str, Dict[str, Any]],
) -> bool:
    if scenario.lead_action is None:
        return True
    lead_item = action_lookup[scenario.lead_action]
    return _is_action_enabled(lead_item)


def _resolve_combination_factor(
    factors: Any,
    scenario: CombinationScenario,
    item: Dict[str, Any],
) -> float:
    action_name = item["action"]
    if item["category"] == "permanent":
        return factors.importance_factor * factors.permanent_factor if scenario.combo_type == "ULS" else 1.0
    if scenario.combo_type == "ULS":
        gamma_q = factors.variable_factors.get(action_name, 1.4)
        combination_factor = 1.0 if action_name == scenario.lead_action else factors.accompanying_factors.get(action_name, 0.9)
        return gamma_q * combination_factor
    if scenario.combo_type == "SLS_SHORT":
        return 1.0 if action_name == scenario.lead_action else factors.accompanying_factors.get(action_name, 0.9)
    return factors.quasi_permanent_factors.get(action_name, 0.0)


def _is_action_enabled(item: Dict[str, Any]) -> bool:
    keys = (
        "vertical_kn_m",
        "horizontal_kn_m",
        "axial_stress_mpa",
        "hoop_stress_mpa",
        "vacuum_pressure_mpa",
        "pier_horizontal_x_kn",
        "pier_horizontal_y_kn",
    )
    return any(abs(item.get(key, 0.0)) > 1e-9 for key in keys)


def _calculate_internal_forces(
    project: ProjectInput,
    derived: Dict[str, Any],
    combinations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    support_coeffs = SUPPORT_COEFFICIENTS[project.support_scheme.support_type]
    span_m = project.geometry.span_m
    area_mm2 = derived["area_mm2"]
    results: List[Dict[str, Any]] = []

    for combo in combinations:
        qv = combo["vertical_kn_m"]
        qh = combo["horizontal_kn_m"]
        moment_v = support_coeffs.moment_coeff * qv * span_m**2
        moment_h = support_coeffs.moment_coeff * qh * span_m**2
        shear_v = support_coeffs.shear_coeff * qv * span_m
        shear_h = support_coeffs.shear_coeff * qh * span_m
        axial_force = combo["axial_stress_mpa"] * area_mm2 / 1000.0
        left_v = support_coeffs.left_reaction_coeff * qv * span_m
        right_v = support_coeffs.right_reaction_coeff * qv * span_m
        left_h = support_coeffs.left_reaction_coeff * qh * span_m
        right_h = support_coeffs.right_reaction_coeff * qh * span_m
        left_axial = support_coeffs.axial_split[0] * axial_force
        right_axial = support_coeffs.axial_split[1] * axial_force
        results.append(
            {
                "name": combo["name"],
                "code": combo["code"],
                "combo_type": combo["combo_type"],
                "lead_action": combo["lead_action"],
                "lead_action_label": combo.get("lead_action_label", ""),
                "purpose": combo["purpose"],
                "clause": combo["clause"],
                "description": combo["description"],
                "vertical_load_kn_m": qv,
                "horizontal_load_kn_m": qh,
                "moment_vertical_kn_m": moment_v,
                "moment_horizontal_kn_m": moment_h,
                "moment_resultant_kn_m": math.hypot(moment_v, moment_h),
                "shear_vertical_kn": shear_v,
                "shear_horizontal_kn": shear_h,
                "shear_resultant_kn": math.hypot(shear_v, shear_h),
                "axial_force_kn": axial_force,
                "axial_stress_mpa": combo["axial_stress_mpa"],
                "hoop_stress_mpa": combo["hoop_stress_mpa"],
                "vacuum_pressure_mpa": combo["vacuum_pressure_mpa"],
                "left_reaction_vertical_kn": left_v,
                "right_reaction_vertical_kn": right_v,
                "left_reaction_horizontal_kn": left_h,
                "right_reaction_horizontal_kn": right_h,
                "left_reaction_axial_kn": left_axial,
                "right_reaction_axial_kn": right_axial,
                "pier_horizontal_x_kn": combo["pier_horizontal_x_kn"],
                "pier_horizontal_y_kn": combo["pier_horizontal_y_kn"],
                "formula_expression": {
                    "moment_vertical": f"Mv = {support_coeffs.moment_coeff:.6f}·qv·L²",
                    "moment_horizontal": f"Mh = {support_coeffs.moment_coeff:.6f}·qh·L²",
                    "shear_vertical": f"Vv = {support_coeffs.shear_coeff:.6f}·qv·L",
                    "shear_horizontal": f"Vh = {support_coeffs.shear_coeff:.6f}·qh·L",
                    "axial_force": "N = σx·A / 1000",
                },
            }
        )
    return results


def _calculate_stress_checks(
    project: ProjectInput,
    derived: Dict[str, Any],
    internal_forces: List[Dict[str, Any]],
) -> Dict[str, Any]:
    support = project.support_scheme
    material = project.material
    area_mm2 = derived["area_mm2"]
    section_modulus_mm3 = derived["section_modulus_mm3"]
    worst: Dict[str, Any] | None = None
    rows: List[Dict[str, Any]] = []

    for item in internal_forces:
        if item["purpose"] != "pipe_strength":
            continue
        bending_stress = item["moment_resultant_kn_m"] * 1e6 / section_modulus_mm3
        support_reaction_n = max(item["left_reaction_vertical_kn"], item["right_reaction_vertical_kn"]) * 1000.0
        friction_stress = support.support_friction_coefficient * support_reaction_n / area_mm2
        shear_stress = 2.0 * item["shear_resultant_kn"] * 1000.0 / area_mm2
        longitudinal_stress = item["axial_stress_mpa"] + friction_stress + bending_stress
        equivalent_stress = math.sqrt(
            longitudinal_stress**2
            + item["hoop_stress_mpa"] ** 2
            - longitudinal_stress * item["hoop_stress_mpa"]
            + 3.0 * shear_stress**2
        )
        status = CheckResultStatus.PASS if equivalent_stress <= material.design_strength_mpa else CheckResultStatus.FAIL
        row = {
            "combo_name": item["name"],
            "combo_code": item["code"],
            "bending_stress_mpa": bending_stress,
            "friction_stress_mpa": friction_stress,
            "shear_stress_mpa": shear_stress,
            "longitudinal_stress_mpa": longitudinal_stress,
            "hoop_stress_mpa": item["hoop_stress_mpa"],
            "equivalent_stress_mpa": equivalent_stress,
            "allowable_stress_mpa": material.design_strength_mpa,
            "status": status.value,
            "clause": "7.2",
            "formula_expression": "σ = sqrt(σx² + σθ² - σxσθ + 3τ²)",
        }
        rows.append(row)
        if worst is None or row["equivalent_stress_mpa"] > worst["equivalent_stress_mpa"]:
            worst = row

    if worst is None:
        worst = {
            "combo_name": "",
            "combo_code": "",
            "bending_stress_mpa": 0.0,
            "friction_stress_mpa": 0.0,
            "shear_stress_mpa": 0.0,
            "longitudinal_stress_mpa": 0.0,
            "hoop_stress_mpa": 0.0,
            "equivalent_stress_mpa": 0.0,
            "allowable_stress_mpa": material.design_strength_mpa,
            "status": CheckResultStatus.WARNING.value,
            "clause": "7.2",
        }

    return {
        "governing": worst,
        "rows": rows,
        "status": worst["status"],
    }


def _calculate_stability(project: ProjectInput) -> Dict[str, Any]:
    support = project.support_scheme
    material = project.material
    vacuum = project.actions.vacuum_pressure_mpa

    if vacuum <= 0:
        return {
            "critical_pressure_mpa": 0.0,
            "required_pressure_mpa": 0.0,
            "status": CheckResultStatus.PASS.value,
            "clause": "8.1",
            "note": "未考虑真空压力，按满足处理。",
            "formula_expression": "未启用真空压力",
        }

    if support.stiffener_spacing_mm <= 0 or support.stiffener_equivalent_inertia_mm4 <= 0 or support.shell_centroid_radius_mm <= 0:
        return {
            "critical_pressure_mpa": 0.0,
            "required_pressure_mpa": 2.0 * vacuum,
            "status": CheckResultStatus.WARNING.value,
            "clause": "8.1.2",
            "note": "未提供加劲环参数，无法完成真空稳定验算。",
            "formula_expression": "Pcr = 3 E Jk / (Rk³ l0)",
        }

    critical = (
        3.0
        * material.elastic_modulus_mpa
        * support.stiffener_equivalent_inertia_mm4
        / (support.shell_centroid_radius_mm**3 * support.stiffener_spacing_mm)
    )
    required = 2.0 * vacuum
    status = CheckResultStatus.PASS if critical >= required else CheckResultStatus.FAIL
    return {
        "critical_pressure_mpa": critical,
        "required_pressure_mpa": required,
        "status": status.value,
        "clause": "8.1.2",
        "note": "按 Pcr >= 2Fv 校核。",
        "formula_expression": "Pcr = 3 E Jk / (Rk³ l0), 要求 Pcr >= 2Fv",
    }


def _calculate_deflection(
    project: ProjectInput,
    derived: Dict[str, Any],
    combinations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    support_coeffs = SUPPORT_COEFFICIENTS[project.support_scheme.support_type]
    sls_combos = [item for item in combinations if item["purpose"] == "service_short"]
    if not sls_combos:
        return {
        "governing_combo": "",
        "governing_combo_code": "",
        "deflection_mm": 0.0,
            "allowable_mm": project.geometry.span_m * 1000.0 / 250.0,
            "status": CheckResultStatus.WARNING.value,
            "clause": "9.1",
            "formula_expression": "W = k q L⁴ / (E I)",
        }

    span_mm = project.geometry.span_m * 1000.0
    q_n_per_mm = max(item["vertical_kn_m"] for item in sls_combos)
    inertia = derived["inertia_mm4"]
    elastic = project.material.elastic_modulus_mpa
    deflection_mm = support_coeffs.deflection_coeff * q_n_per_mm * span_mm**4 / (elastic * inertia)
    governing_combo = max(sls_combos, key=lambda item: item["vertical_kn_m"])
    allowable_mm = span_mm / 250.0
    status = CheckResultStatus.PASS if deflection_mm <= allowable_mm else CheckResultStatus.FAIL
    return {
        "governing_combo": governing_combo["name"],
        "governing_combo_code": governing_combo["code"],
        "deflection_mm": deflection_mm,
        "allowable_mm": allowable_mm,
        "status": status.value,
        "clause": "9.1",
        "formula_expression": f"W = {support_coeffs.deflection_coeff:.6f}·q·L⁴ / (E·I)",
    }


def _calculate_pier_checks(project: ProjectInput, internal_forces: List[Dict[str, Any]]) -> Dict[str, Any]:
    uls_rows = [item for item in internal_forces if item["purpose"] == "pier"]
    piers = [
        ("left_pier", "左支墩", "left"),
        ("right_pier", "右支墩", "right"),
    ]
    details: Dict[str, List[Dict[str, Any]]] = {}
    governing: Dict[str, Dict[str, Any]] = {}
    foundation = project.pier_foundation

    for key, label, side in piers:
        rows: List[Dict[str, Any]] = []
        for item in uls_rows:
            vertical_pipe = item[f"{side}_reaction_vertical_kn"]
            transverse_pipe = item[f"{side}_reaction_horizontal_kn"]
            axial_pipe = abs(item[f"{side}_reaction_axial_kn"])
            total_vertical = (
                foundation.foundation_self_weight_kn
                + foundation.pier_self_weight_kn
                + foundation.additional_vertical_kn
                + vertical_pipe
            )
            hx = transverse_pipe + item["pier_horizontal_x_kn"] + foundation.additional_horizontal_x_kn
            hy = axial_pipe + item["pier_horizontal_y_kn"] + foundation.additional_horizontal_y_kn
            my = (
                transverse_pipe * foundation.pipe_reaction_height_m
                + item["pier_horizontal_x_kn"] * foundation.hydraulic_force_height_m
                + foundation.additional_horizontal_x_kn * foundation.pipe_reaction_height_m
                + foundation.additional_moment_y_kn_m
            )
            mx = (
                axial_pipe * foundation.axial_force_height_m
                + item["pier_horizontal_y_kn"] * foundation.hydraulic_force_height_m
                + foundation.additional_horizontal_y_kn * foundation.axial_force_height_m
                + foundation.additional_moment_x_kn_m
            )
            ex = my / total_vertical if total_vertical else float("inf")
            ey = mx / total_vertical if total_vertical else float("inf")
            area = foundation.base_length_m * foundation.base_width_m
            mean_pressure = total_vertical / area if area else float("inf")
            qmax = mean_pressure * (1.0 + 6.0 * ex / foundation.base_length_m + 6.0 * ey / foundation.base_width_m)
            qmin = mean_pressure * (1.0 - 6.0 * ex / foundation.base_length_m - 6.0 * ey / foundation.base_width_m)
            resultant_h = math.hypot(hx, hy)
            sliding_ratio = (
                foundation.friction_coefficient * max(total_vertical - foundation.buoyancy_kn, 0.0) / resultant_h
                if resultant_h > 1e-9
                else float("inf")
            )
            eccentricity_pass = ex / foundation.base_length_m + ey / foundation.base_width_m <= 1.0 / 6.0
            bearing_pass = qmax <= foundation.allowable_bearing_kpa and qmin >= 0.0
            sliding_pass = sliding_ratio >= foundation.required_sliding_safety
            if eccentricity_pass and bearing_pass and sliding_pass:
                status = CheckResultStatus.PASS
            else:
                status = CheckResultStatus.FAIL
            rows.append(
                {
                    "combo_name": item["name"],
                    "combo_code": item["code"],
                    "total_vertical_kn": total_vertical,
                    "horizontal_x_kn": hx,
                    "horizontal_y_kn": hy,
                    "moment_x_kn_m": mx,
                    "moment_y_kn_m": my,
                    "eccentricity_x_m": ex,
                    "eccentricity_y_m": ey,
                    "qmax_kpa": qmax,
                    "qmin_kpa": qmin,
                    "sliding_ratio": sliding_ratio,
                    "status": status.value,
                    "clause": "10.2",
                    "formula_expression": {
                        "eccentricity": "ex = My / ΣR, ey = Mx / ΣR",
                        "bearing": "q = ΣR/(ab) · (1 ± 6ex/a ± 6ey/b)",
                        "sliding": "kc = μ(ΣR - Rw) / ΣH",
                    },
                }
            )
        details[key] = rows
        governing[key] = _select_governing_pier_row(rows, label)

    return {
        "details": details,
        "governing": governing,
    }


def _select_governing_pier_row(rows: Iterable[Dict[str, Any]], label: str) -> Dict[str, Any]:
    row_list = list(rows)
    if not row_list:
        return {
            "pier_label": label,
            "combo_name": "",
            "combo_code": "",
            "total_vertical_kn": 0.0,
            "horizontal_x_kn": 0.0,
            "horizontal_y_kn": 0.0,
            "moment_x_kn_m": 0.0,
            "moment_y_kn_m": 0.0,
            "eccentricity_x_m": 0.0,
            "eccentricity_y_m": 0.0,
            "qmax_kpa": 0.0,
            "qmin_kpa": 0.0,
            "sliding_ratio": float("inf"),
            "status": CheckResultStatus.WARNING.value,
            "clause": "10.2",
        }
    worst = max(
        row_list,
        key=lambda item: (
            item["qmax_kpa"],
            item["eccentricity_x_m"] + item["eccentricity_y_m"],
            -item["sliding_ratio"],
        ),
    )
    return {
        "pier_label": label,
        **worst,
    }


def _build_report_context(
    project: ProjectInput,
    derived: Dict[str, Any],
    action_values: List[Dict[str, Any]],
    combinations: List[Dict[str, Any]],
    internal_forces: List[Dict[str, Any]],
    stress_checks: Dict[str, Any],
    stability_checks: Dict[str, Any],
    deflection_check: Dict[str, Any],
    pier_checks: Dict[str, Any],
    formula_trace: Dict[str, Any],
    validation_messages: List[str],
) -> Dict[str, Any]:
    return {
        "project": project.to_dict(),
        "derived_section": derived,
        "action_values": action_values,
        "combinations": combinations,
        "internal_forces": internal_forces,
        "stress_checks": stress_checks,
        "stability_checks": stability_checks,
        "deflection_check": deflection_check,
        "pier_checks": pier_checks,
        "formula_trace": formula_trace,
        "validation_messages": validation_messages,
        "governing_summary": {
            "stress_combo": stress_checks["governing"]["combo_name"],
            "stress_status": stress_checks["status"],
            "stability_status": stability_checks["status"],
            "deflection_combo": deflection_check["governing_combo"],
            "deflection_status": deflection_check["status"],
            "left_pier_status": pier_checks["governing"]["left_pier"]["status"],
            "right_pier_status": pier_checks["governing"]["right_pier"]["status"],
        },
    }


def _build_formula_trace(
    project: ProjectInput,
    derived: Dict[str, Any],
    action_values: List[Dict[str, Any]],
    combinations: List[Dict[str, Any]],
    internal_forces: List[Dict[str, Any]],
    stress_checks: Dict[str, Any],
    stability_checks: Dict[str, Any],
    deflection_check: Dict[str, Any],
    pier_checks: Dict[str, Any],
) -> Dict[str, Any]:
    geometry = project.geometry
    material = project.material
    support = project.support_scheme
    area_mm2 = derived["area_mm2"]
    support_coeffs = SUPPORT_COEFFICIENTS[support.support_type]

    section_trace = [
        {
            "title": "有效壁厚",
            "clause": "2.0.2 / 4.2.1",
            "formula": "te = t - c",
            "substitution": f"te = {geometry.wall_thickness_mm:.6f} - {geometry.corrosion_allowance_mm:.6f}",
            "result": f"{derived['effective_thickness_mm']:.6f} mm",
        },
        {
            "title": "内径",
            "clause": "2.0.2",
            "formula": "Di = D - 2te",
            "substitution": (
                f"Di = {geometry.outer_diameter_mm:.6f} - 2 × {derived['effective_thickness_mm']:.6f}"
            ),
            "result": f"{derived['inner_diameter_mm']:.6f} mm",
        },
        {
            "title": "截面面积",
            "clause": "2.0.2",
            "formula": "A = π/4 × (D² - Di²)",
            "substitution": (
                f"A = π/4 × ({geometry.outer_diameter_mm:.6f}² - {derived['inner_diameter_mm']:.6f}²)"
            ),
            "result": f"{derived['area_mm2']:.6f} mm²",
        },
        {
            "title": "惯性矩",
            "clause": "2.0.2",
            "formula": "I = π/64 × (D⁴ - Di⁴)",
            "substitution": (
                f"I = π/64 × ({geometry.outer_diameter_mm:.6f}⁴ - {derived['inner_diameter_mm']:.6f}⁴)"
            ),
            "result": f"{derived['inertia_mm4']:.6f} mm⁴",
        },
        {
            "title": "截面抵抗矩",
            "clause": "2.0.2",
            "formula": "W = I / (D/2)",
            "substitution": f"W = {derived['inertia_mm4']:.6f} / {derived['outer_radius_mm']:.6f}",
            "result": f"{derived['section_modulus_mm3']:.6f} mm³",
        },
    ]

    action_trace = [
        {
            "title": item["label"],
            "clause": item["formula"],
            "formula": item.get("formula_expression", ""),
            "substitution": item.get("formula_substitution", ""),
            "result": _format_action_result(item),
        }
        for item in action_values
    ]

    combination_trace = []
    for combo in combinations:
        details = [
            {
                "action": contributor["label"],
                "factor": contributor["factor"],
                "vertical_kn_m": contributor["vertical_contribution_kn_m"],
                "horizontal_kn_m": contributor["horizontal_contribution_kn_m"],
                "axial_mpa": contributor["axial_contribution_mpa"],
                "hoop_mpa": contributor["hoop_contribution_mpa"],
            }
            for contributor in combo["contributors"]
        ]
        combination_trace.append(
            {
                "name": combo["name"],
                "combo_type": combo["combo_type"],
                "formula": combo["formula_expression"],
                "substitution": "逐项按下表系数累加。",
                "result": (
                    f"qv={combo['vertical_kn_m']:.6f} kN/m, qh={combo['horizontal_kn_m']:.6f} kN/m, "
                    f"σx={combo['axial_stress_mpa']:.6f} MPa, σθ={combo['hoop_stress_mpa']:.6f} MPa"
                ),
                "details": details,
            }
        )

    internal_trace = []
    for item in internal_forces:
        internal_trace.append(
            {
                "name": item["name"],
                "formulae": [
                    {
                        "title": "竖向弯矩",
                        "formula": item["formula_expression"]["moment_vertical"],
                        "substitution": (
                            f"Mv = {support_coeffs.moment_coeff:.6f} × {item['vertical_load_kn_m']:.6f} × "
                            f"{project.geometry.span_m:.6f}²"
                        ),
                        "result": f"{item['moment_vertical_kn_m']:.6f} kN·m",
                    },
                    {
                        "title": "水平弯矩",
                        "formula": item["formula_expression"]["moment_horizontal"],
                        "substitution": (
                            f"Mh = {support_coeffs.moment_coeff:.6f} × {item['horizontal_load_kn_m']:.6f} × "
                            f"{project.geometry.span_m:.6f}²"
                        ),
                        "result": f"{item['moment_horizontal_kn_m']:.6f} kN·m",
                    },
                    {
                        "title": "组合轴力",
                        "formula": item["formula_expression"]["axial_force"],
                        "substitution": f"N = {item['axial_stress_mpa']:.6f} × {area_mm2:.6f} / 1000",
                        "result": f"{item['axial_force_kn']:.6f} kN",
                    },
                ],
            }
        )

    stress_trace = []
    for row in stress_checks["rows"]:
        stress_trace.append(
            {
                "name": row["combo_name"],
                "formulae": [
                    {
                        "title": "弯曲应力",
                        "formula": "σb = M / W",
                        "substitution": (
                            f"σb = {next(item for item in internal_forces if item['name'] == row['combo_name'])['moment_resultant_kn_m']:.6f} × 10^6 / "
                            f"{derived['section_modulus_mm3']:.6f}"
                        ),
                        "result": f"{row['bending_stress_mpa']:.6f} MPa",
                    },
                    {
                        "title": "剪应力",
                        "formula": "τ = 2V / A",
                        "substitution": (
                            f"τ = 2 × {next(item for item in internal_forces if item['name'] == row['combo_name'])['shear_resultant_kn']:.6f} × 1000 / "
                            f"{derived['area_mm2']:.6f}"
                        ),
                        "result": f"{row['shear_stress_mpa']:.6f} MPa",
                    },
                    {
                        "title": "等效应力",
                        "formula": row["formula_expression"],
                        "substitution": (
                            f"σ = sqrt({row['longitudinal_stress_mpa']:.6f}² + {row['hoop_stress_mpa']:.6f}² - "
                            f"{row['longitudinal_stress_mpa']:.6f}×{row['hoop_stress_mpa']:.6f} + 3×{row['shear_stress_mpa']:.6f}²)"
                        ),
                        "result": f"{row['equivalent_stress_mpa']:.6f} MPa <= {row['allowable_stress_mpa']:.6f} MPa",
                    },
                ],
                "status": row["status"],
            }
        )

    stability_trace = [
        {
            "title": "真空稳定",
            "clause": stability_checks["clause"],
            "formula": stability_checks["formula_expression"],
            "substitution": (
                f"Pcr = 3 × {material.elastic_modulus_mpa:.6f} × {support.stiffener_equivalent_inertia_mm4:.6f} / "
                f"({support.shell_centroid_radius_mm:.6f}³ × {support.stiffener_spacing_mm:.6f})"
                if support.stiffener_spacing_mm > 0 and support.stiffener_equivalent_inertia_mm4 > 0 and support.shell_centroid_radius_mm > 0
                else "-"
            ),
            "result": (
                f"Pcr = {stability_checks['critical_pressure_mpa']:.6f} MPa, "
                f"2Fv = {stability_checks['required_pressure_mpa']:.6f} MPa"
            ),
            "status": stability_checks["status"],
        }
    ]

    deflection_trace = [
        {
            "title": "平管挠度",
            "clause": deflection_check["clause"],
            "formula": deflection_check["formula_expression"],
            "substitution": (
                f"W = {support_coeffs.deflection_coeff:.6f} × "
                f"{next((item['vertical_kn_m'] for item in combinations if item['name'] == deflection_check['governing_combo']), 0.0):.6f} × "
                f"{project.geometry.span_m * 1000.0:.6f}⁴ / ({material.elastic_modulus_mpa:.6f} × {derived['inertia_mm4']:.6f})"
            ),
            "result": (
                f"W = {deflection_check['deflection_mm']:.6f} mm <= "
                f"{deflection_check['allowable_mm']:.6f} mm"
            ),
            "status": deflection_check["status"],
        }
    ]

    pier_trace = {}
    for side in ("left_pier", "right_pier"):
        pier_trace[side] = []
        for row in pier_checks["details"][side]:
            pier_trace[side].append(
                {
                    "name": row["combo_name"],
                    "formulae": [
                        {
                            "title": "偏心距",
                            "formula": row["formula_expression"]["eccentricity"],
                            "substitution": (
                                f"ex = {row['moment_y_kn_m']:.6f} / {row['total_vertical_kn']:.6f}, "
                                f"ey = {row['moment_x_kn_m']:.6f} / {row['total_vertical_kn']:.6f}"
                            ),
                            "result": f"ex = {row['eccentricity_x_m']:.6f} m, ey = {row['eccentricity_y_m']:.6f} m",
                        },
                        {
                            "title": "基底压应力",
                            "formula": row["formula_expression"]["bearing"],
                            "substitution": (
                                f"qmax = {row['qmax_kpa']:.6f} kPa, qmin = {row['qmin_kpa']:.6f} kPa"
                            ),
                            "result": f"qmax = {row['qmax_kpa']:.6f} kPa, qmin = {row['qmin_kpa']:.6f} kPa",
                        },
                        {
                            "title": "抗滑稳定",
                            "formula": row["formula_expression"]["sliding"],
                            "substitution": f"kc = {row['sliding_ratio']:.6f}",
                            "result": f"kc = {row['sliding_ratio']:.6f}",
                        },
                    ],
                    "status": row["status"],
                }
            )

    return {
        "section": section_trace,
        "actions": action_trace,
        "combinations": combination_trace,
        "internal_forces": internal_trace,
        "stress": stress_trace,
        "stability": stability_trace,
        "deflection": deflection_trace,
        "piers": pier_trace,
    }


def _format_action_result(item: Dict[str, Any]) -> str:
    parts = []
    if abs(item.get("vertical_kn_m", 0.0)) > 1e-9:
        parts.append(f"竖向 = {item['vertical_kn_m']:.6f} kN/m")
    if abs(item.get("horizontal_kn_m", 0.0)) > 1e-9:
        parts.append(f"水平 = {item['horizontal_kn_m']:.6f} kN/m")
    if abs(item.get("axial_stress_mpa", 0.0)) > 1e-9:
        parts.append(f"轴向应力 = {item['axial_stress_mpa']:.6f} MPa")
    if abs(item.get("hoop_stress_mpa", 0.0)) > 1e-9:
        parts.append(f"环向应力 = {item['hoop_stress_mpa']:.6f} MPa")
    if abs(item.get("vacuum_pressure_mpa", 0.0)) > 1e-9:
        parts.append(f"真空压力 = {item['vacuum_pressure_mpa']:.6f} MPa")
    if abs(item.get("pier_horizontal_x_kn", 0.0)) > 1e-9:
        parts.append(f"X向水平力 = {item['pier_horizontal_x_kn']:.6f} kN")
    if abs(item.get("pier_horizontal_y_kn", 0.0)) > 1e-9:
        parts.append(f"Y向水平力 = {item['pier_horizontal_y_kn']:.6f} kN")
    return "；".join(parts) if parts else "0"
