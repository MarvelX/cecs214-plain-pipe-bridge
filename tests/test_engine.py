import json

import pytest
from cecs214_plain_pipe import build_html_report
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
    project.geometry.water_density_kn_m3 = 0.0
    project.geometry.steel_density_kn_m3 = 0.0
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
