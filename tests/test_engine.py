import json

import pytest
from cecs214_plain_pipe import CalculationInputError, build_html_report
from cecs214_plain_pipe.engine import calculate_project
from cecs214_plain_pipe.models import SupportType, default_project_input, project_input_from_dict


def test_section_properties_are_positive() -> None:
    project = default_project_input()
    result = calculate_project(project)

    derived = result.derived_section
    assert derived["effective_thickness_mm"] == 11.0
    assert derived["inner_diameter_mm"] == 998.0
    assert derived["area_mm2"] > 0
    assert derived["inertia_mm4"] > 0
    assert derived["section_modulus_mm3"] > 0


def test_flow_pressure_formula_matches_manual_calculation() -> None:
    project = default_project_input()
    result = calculate_project(project)

    flow_row = next(item for item in result.action_values if item["action"] == "flow_pressure")
    expected = 1.47 * 10.0 * (2.5**2) / (2.0 * 9.81) * 1.8
    assert flow_row["pier_horizontal_x_kn"] == pytest.approx(expected)


def test_internal_force_coefficients_for_support_types() -> None:
    project = default_project_input()
    project.geometry.span_m = 10.0
    project.geometry.insulation_weight_kn_m = 0.0
    project.geometry.lining_weight_kn_m = 0.0
    project.geometry.attachments_weight_kn_m = 0.0
    project.geometry.water_density_kn_m3 = 1e-12
    project.geometry.steel_density_kn_m3 = 1e-12
    project.actions.live_load_kn_m = 2.0
    project.actions.wind_load_kn_m = 0.0
    project.actions.design_internal_pressure_mpa = 0.0
    project.actions.working_internal_pressure_mpa = 0.0
    project.actions.vacuum_pressure_mpa = 0.0
    project.actions.flow_velocity_m_s = 0.0
    project.actions.ice_strength_kn_m2 = 0.0
    project.actions.drift_weight_kn = 0.0
    project.combination_factors.permanent_factor = 1.0
    project.combination_factors.variable_factors["live"] = 1.0
    project.combination_factors.accompanying_factors["live"] = 0.0

    expected_moments = {
        SupportType.SIMPLE_SIMPLE: 25.0,
        SupportType.FIXED_SIMPLE: 25.0,
        SupportType.FIXED_FIXED: 16.6666666667,
    }

    for support_type, expected_moment in expected_moments.items():
        project.support_scheme.support_type = support_type
        result = calculate_project(project)
        combo = next(item for item in result.internal_forces if item["code"] == "ULS-STRENGTH-LIVE")
        assert combo["moment_vertical_kn_m"] == pytest.approx(expected_moment)


def test_support_scenarios_produce_results() -> None:
    for support_type in SupportType:
        project = default_project_input()
        project.support_scheme.support_type = support_type
        result = calculate_project(project)

        assert result.stress_checks["governing"]["equivalent_stress_mpa"] >= 0
        assert result.deflection_check["allowable_mm"] > 0
        assert result.pier_checks["governing"]["left_pier"]["qmax_kpa"] >= 0


def test_json_roundtrip_is_stable() -> None:
    project = default_project_input()
    payload = json.loads(json.dumps(project.to_dict(), ensure_ascii=False))
    reconstructed = project_input_from_dict(payload)

    result1 = calculate_project(project).to_dict()
    result2 = calculate_project(reconstructed).to_dict()
    assert result1 == result2


def test_formula_trace_and_report_are_generated() -> None:
    project = default_project_input()
    result = calculate_project(project)
    html = build_html_report(project, result.to_dict())

    assert "actions" in result.formula_trace
    assert "combinations" in result.formula_trace
    assert "公式追溯" in html
    assert any(combo["purpose"] == "pipe_strength" for combo in result.combinations)


def test_invalid_drift_time_raises_input_error() -> None:
    project = default_project_input()
    project.actions.drift_time_s = 0.0

    with pytest.raises(CalculationInputError) as exc_info:
        calculate_project(project)

    assert "漂流物撞击时间必须大于零。" in exc_info.value.errors


def test_invalid_geometry_raises_input_error() -> None:
    project = default_project_input()
    project.geometry.outer_diameter_mm = 10.0
    project.geometry.wall_thickness_mm = 8.0
    project.geometry.corrosion_allowance_mm = 1.0

    with pytest.raises(CalculationInputError) as exc_info:
        calculate_project(project)

    assert "截面几何无效：内径必须大于零。" in exc_info.value.errors


def test_backend_rejects_out_of_range_poisson_ratio() -> None:
    project = default_project_input()
    project.material.poisson_ratio = 0.9

    with pytest.raises(CalculationInputError) as exc_info:
        calculate_project(project)

    assert "泊松比必须在 0 到 0.5 之间。" in exc_info.value.errors


def test_json_loader_rejects_null_and_invalid_enum() -> None:
    payload = default_project_input().to_dict()
    payload["material"]["poisson_ratio"] = None

    with pytest.raises(TypeError):
        project_input_from_dict(payload)

    payload = default_project_input().to_dict()
    payload["support_scheme"]["support_type"] = "unsupported"

    with pytest.raises(ValueError):
        project_input_from_dict(payload)


def test_stability_branch_without_vacuum_returns_pass_warning_message() -> None:
    project = default_project_input()
    project.actions.vacuum_pressure_mpa = 0.0
    result = calculate_project(project)

    assert result.stability_checks["status"] == "pass"
    assert result.stability_checks["note"] == "未考虑真空压力，按满足处理。"
    assert "未启用真空压力" in result.stability_checks["formula_expression"]


def test_stability_branch_missing_stiffener_returns_warning() -> None:
    project = default_project_input()
    project.support_scheme.stiffener_spacing_mm = 0.0
    result = calculate_project(project)

    assert result.stability_checks["status"] == "warning"
    assert result.stability_checks["required_pressure_mpa"] == pytest.approx(2.0 * project.actions.vacuum_pressure_mpa)


def test_combination_factor_for_pressure_lead_uses_accompanying_factor_for_wind() -> None:
    project = default_project_input()
    result = calculate_project(project)

    combo = next(item for item in result.combinations if item["code"] == "ULS-STRENGTH-PRESSURE")
    wind_contributor = next(item for item in combo["contributors"] if item["action"] == "wind")

    expected_factor = (
        project.combination_factors.variable_factors["wind"]
        * project.combination_factors.accompanying_factors["wind"]
    )
    assert wind_contributor["factor"] == pytest.approx(expected_factor)


def test_long_term_combination_uses_quasi_permanent_pressure_value() -> None:
    project = default_project_input()
    result = calculate_project(project)

    combo = next(item for item in result.combinations if item["code"] == "SLS-LONG")
    expected = (
        project.actions.working_internal_pressure_mpa
        * result.derived_section["inner_radius_mm"]
        / (2.0 * result.derived_section["effective_thickness_mm"])
        * project.combination_factors.quasi_permanent_factors["pressure"]
    )
    assert combo["axial_stress_mpa"] == pytest.approx(expected)
