from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Mapping, Type, TypeVar, get_args, get_origin, get_type_hints


class SupportType(str, Enum):
    SIMPLE_SIMPLE = "simple_simple"
    FIXED_SIMPLE = "fixed_simple"
    FIXED_FIXED = "fixed_fixed"

    @property
    def label(self) -> str:
        return {
            SupportType.SIMPLE_SIMPLE: "两端支墩",
            SupportType.FIXED_SIMPLE: "一端锚墩一端支墩",
            SupportType.FIXED_FIXED: "两端锚墩",
        }[self]


class ApplicableAction(str, Enum):
    DEAD = "dead"
    LIVE = "live"
    WIND = "wind"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    VACUUM = "vacuum"
    FLOW_PRESSURE = "flow_pressure"
    ICE_PRESSURE = "ice_pressure"
    DRIFT_IMPACT = "drift_impact"

    @property
    def label(self) -> str:
        return {
            ApplicableAction.DEAD: "永久作用",
            ApplicableAction.LIVE: "活荷载",
            ApplicableAction.WIND: "风荷载",
            ApplicableAction.PRESSURE: "内水压力",
            ApplicableAction.TEMPERATURE: "温度作用",
            ApplicableAction.VACUUM: "真空压力",
            ApplicableAction.FLOW_PRESSURE: "流水压力",
            ApplicableAction.ICE_PRESSURE: "融冰压力",
            ApplicableAction.DRIFT_IMPACT: "漂流物撞击力",
        }[self]


class CheckResultStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"

    @property
    def label(self) -> str:
        return {
            CheckResultStatus.PASS: "满足",
            CheckResultStatus.FAIL: "不满足",
            CheckResultStatus.WARNING: "提示",
        }[self]


@dataclass
class ProjectMeta:
    project_name: str = "平管管桥示例工程"
    project_code: str = "PPB-001"
    designer: str = ""
    notes: str = ""


@dataclass
class GeometryInput:
    span_m: float = 18.0
    outer_diameter_mm: float = 1020.0
    wall_thickness_mm: float = 12.0
    corrosion_allowance_mm: float = 1.0
    insulation_weight_kn_m: float = 0.4
    lining_weight_kn_m: float = 0.0
    attachments_weight_kn_m: float = 0.15
    steel_density_kn_m3: float = 78.5
    water_density_kn_m3: float = 10.0


@dataclass
class MaterialInput:
    steel_grade: str = "Q235"
    elastic_modulus_mpa: float = 2.06e5
    design_strength_mpa: float = 215.0
    thermal_expansion_per_c: float = 12e-6
    poisson_ratio: float = 0.30


@dataclass
class SupportSchemeInput:
    support_type: SupportType = SupportType.SIMPLE_SIMPLE
    support_friction_coefficient: float = 0.15
    has_expansion_joint: bool = False
    stiffener_spacing_mm: float = 3000.0
    stiffener_equivalent_inertia_mm4: float = 4.2e7
    shell_centroid_radius_mm: float = 510.0


@dataclass
class ActionParameters:
    live_load_kn_m: float = 0.8
    wind_load_kn_m: float = 1.2
    design_internal_pressure_mpa: float = 0.90
    working_internal_pressure_mpa: float = 0.60
    vacuum_pressure_mpa: float = 0.05
    closure_temperature_c: float = 10.0
    service_temperature_min_c: float = -5.0
    service_temperature_max_c: float = 35.0
    flow_velocity_m_s: float = 2.5
    water_unit_weight_kn_m3: float = 10.0
    blocking_area_m2: float = 1.80
    flow_coefficient: float = 1.47
    ice_mode: str = "vertical"
    ice_width_m: float = 1.60
    ice_thickness_m: float = 0.15
    ice_strength_kn_m2: float = 750.0
    ice_shape_coefficient: float = 0.90
    ice_breaking_angle_deg: float = 60.0
    drift_weight_kn: float = 12.0
    drift_velocity_m_s: float = 3.0
    drift_time_s: float = 1.0


@dataclass
class CombinationFactorsInput:
    importance_factor: float = 1.0
    permanent_factor: float = 1.2
    variable_factors: Dict[str, float] = field(
        default_factory=lambda: {
            ApplicableAction.LIVE.value: 1.4,
            ApplicableAction.WIND.value: 1.4,
            ApplicableAction.PRESSURE.value: 1.3,
            ApplicableAction.TEMPERATURE.value: 1.3,
            ApplicableAction.FLOW_PRESSURE.value: 1.3,
            ApplicableAction.ICE_PRESSURE.value: 1.3,
            ApplicableAction.DRIFT_IMPACT.value: 1.3,
        }
    )
    accompanying_factors: Dict[str, float] = field(
        default_factory=lambda: {
            ApplicableAction.LIVE.value: 0.7,
            ApplicableAction.WIND.value: 0.6,
            ApplicableAction.PRESSURE.value: 0.7,
            ApplicableAction.TEMPERATURE.value: 0.6,
            ApplicableAction.FLOW_PRESSURE.value: 0.6,
            ApplicableAction.ICE_PRESSURE.value: 0.6,
            ApplicableAction.DRIFT_IMPACT.value: 0.6,
        }
    )
    quasi_permanent_factors: Dict[str, float] = field(
        default_factory=lambda: {
            ApplicableAction.LIVE.value: 0.4,
            ApplicableAction.WIND.value: 0.0,
            ApplicableAction.PRESSURE.value: 0.7,
            ApplicableAction.TEMPERATURE.value: 0.5,
            ApplicableAction.FLOW_PRESSURE.value: 0.0,
            ApplicableAction.ICE_PRESSURE.value: 0.0,
            ApplicableAction.DRIFT_IMPACT.value: 0.0,
        }
    )


@dataclass
class PierFoundationInput:
    base_length_m: float = 3.0
    base_width_m: float = 4.0
    allowable_bearing_kpa: float = 220.0
    friction_coefficient: float = 0.45
    required_sliding_safety: float = 1.20
    foundation_self_weight_kn: float = 500.0
    pier_self_weight_kn: float = 110.0
    buoyancy_kn: float = 0.0
    pipe_reaction_height_m: float = 2.2
    hydraulic_force_height_m: float = 1.4
    drift_force_height_m: float = 1.4
    axial_force_height_m: float = 2.2
    additional_vertical_kn: float = 0.0
    additional_horizontal_x_kn: float = 0.0
    additional_horizontal_y_kn: float = 0.0
    additional_moment_x_kn_m: float = 0.0
    additional_moment_y_kn_m: float = 0.0


@dataclass
class ProjectInput:
    meta: ProjectMeta = field(default_factory=ProjectMeta)
    geometry: GeometryInput = field(default_factory=GeometryInput)
    material: MaterialInput = field(default_factory=MaterialInput)
    support_scheme: SupportSchemeInput = field(default_factory=SupportSchemeInput)
    actions: ActionParameters = field(default_factory=ActionParameters)
    combination_factors: CombinationFactorsInput = field(default_factory=CombinationFactorsInput)
    pier_foundation: PierFoundationInput = field(default_factory=PierFoundationInput)

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(asdict(self))

    def to_json_ready(self) -> Dict[str, Any]:
        return self.to_dict()


@dataclass
class CalculationResult:
    derived_section: Dict[str, Any]
    action_values: List[Dict[str, Any]]
    combinations: List[Dict[str, Any]]
    internal_forces: List[Dict[str, Any]]
    stress_checks: Dict[str, Any]
    stability_checks: Dict[str, Any]
    deflection_check: Dict[str, Any]
    pier_checks: Dict[str, Any]
    formula_trace: Dict[str, Any]
    report_context: Dict[str, Any]
    validation_messages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(asdict(self))


def default_project_input() -> ProjectInput:
    return ProjectInput()


T = TypeVar("T")


def project_input_from_dict(data: Mapping[str, Any]) -> ProjectInput:
    return _coerce_dataclass(ProjectInput, data)


def _serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


def _coerce_dataclass(cls: Type[T], payload: Mapping[str, Any]) -> T:
    values: Dict[str, Any] = {}
    type_hints = get_type_hints(cls)
    for field_info in fields(cls):
        if field_info.name not in payload:
            continue
        raw_value = payload[field_info.name]
        annotation = type_hints.get(field_info.name, field_info.type)
        values[field_info.name] = _coerce_value(annotation, raw_value)
    return cls(**values)


def _coerce_value(annotation: Any, value: Any) -> Any:
    origin = get_origin(annotation)
    if origin is None:
        if is_dataclass(annotation):
            return _coerce_dataclass(annotation, value)
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return annotation(value)
        return value
    if origin in (dict, Dict):
        key_type, value_type = get_args(annotation)
        return {
            _coerce_value(key_type, key): _coerce_value(value_type, item)
            for key, item in value.items()
        }
    if origin in (list, List):
        inner_type = get_args(annotation)[0]
        return [_coerce_value(inner_type, item) for item in value]
    return value
