from __future__ import annotations

from html import escape
from typing import Any, Dict, Iterable, List

from .models import CheckResultStatus, ProjectInput, SupportType


def build_html_report(project: ProjectInput, result: Dict[str, Any]) -> str:
    report = result["report_context"] if "report_context" in result else result
    project_data = report["project"]
    meta = project_data["meta"]
    support_type_label = SupportType(project_data["support_scheme"]["support_type"]).label
    derived = report["derived_section"]
    action_values = report["action_values"]
    combinations = report["combinations"]
    internal_forces = report["internal_forces"]
    stress = report["stress_checks"]
    stability = report["stability_checks"]
    deflection = report["deflection_check"]
    pier = report["pier_checks"]
    formula_trace = report["formula_trace"]
    validations = report["validation_messages"]

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{escape(meta["project_name"])} 计算书</title>
  <style>
    @page {{
      size: A4;
      margin: 14mm 12mm 14mm 12mm;
    }}
    body {{
      font-family: "PingFang SC", "Noto Serif CJK SC", "Noto Sans SC", sans-serif;
      margin: 0;
      color: #18212c;
      line-height: 1.55;
      background:
        radial-gradient(circle at top left, rgba(201, 165, 99, 0.20), transparent 32%),
        linear-gradient(180deg, #efe4d0 0%, #f7f2e9 36%, #f6f3ee 100%);
    }}
    .page {{
      max-width: 960px;
      margin: 24px auto;
      background: #fffdfa;
      padding: 28px 34px 40px;
      box-shadow: 0 22px 60px rgba(21, 28, 35, 0.12);
      border: 1px solid rgba(166, 127, 58, 0.12);
    }}
    h1, h2, h3 {{
      color: #18324a;
    }}
    h1 {{
      margin: 0;
      font-size: 34px;
      letter-spacing: 1px;
    }}
    h2 {{
      margin-top: 28px;
      padding-bottom: 6px;
      border-bottom: 2px solid #d7c29a;
    }}
    h3 {{
      margin-top: 22px;
      margin-bottom: 10px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0 22px;
      font-size: 14px;
    }}
    th, td {{
      border: 1px solid #d8d1c3;
      padding: 8px 10px;
      vertical-align: top;
    }}
    th {{
      background: linear-gradient(180deg, #f5ebd7 0%, #efe1c5 100%);
      text-align: left;
    }}
    tbody tr:nth-child(even) {{
      background: #fcf7ef;
    }}
    .status-pass {{
      color: #16784e;
      font-weight: 700;
    }}
    .status-fail {{
      color: #b22828;
      font-weight: 700;
    }}
    .status-warning {{
      color: #9a6700;
      font-weight: 700;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 18px;
      align-items: stretch;
      margin-bottom: 22px;
    }}
    .card {{
      padding: 14px 16px;
      border: 1px solid #e6d5bc;
      background: linear-gradient(180deg, #fffaf1 0%, #fffcf7 100%);
      border-radius: 12px;
    }}
    .cover {{
      padding: 24px;
      border-radius: 18px;
      color: #fff8ee;
      background:
        linear-gradient(135deg, rgba(196, 144, 58, 0.92), rgba(130, 79, 26, 0.92)),
        linear-gradient(180deg, #1b3245 0%, #0f2435 100%);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.12);
    }}
    .cover small {{
      display: inline-block;
      margin-bottom: 10px;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      opacity: 0.85;
    }}
    .summary-strip {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 18px 0 8px;
    }}
    .summary-chip {{
      padding: 12px 14px;
      border-radius: 12px;
      background: #f8f2e6;
      border: 1px solid #ebdcc0;
    }}
    .summary-chip strong {{
      display: block;
      font-size: 12px;
      color: #6b5c42;
      margin-bottom: 6px;
    }}
    .summary-chip span {{
      font-size: 18px;
      font-weight: 700;
      color: #1b2d3b;
    }}
    .muted {{
      color: #6f7b87;
      font-size: 13px;
    }}
    code {{
      display: inline-block;
      white-space: normal;
      line-height: 1.5;
      padding: 2px 0;
      background: transparent;
      color: #243543;
      font-family: "SF Mono", "Menlo", monospace;
    }}
    .section-break {{
      page-break-before: always;
    }}
    @media print {{
      body {{
        background: #fff;
        margin: 0;
      }}
      .page {{
        box-shadow: none;
        max-width: none;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <div class="hero">
      <div class="cover">
        <small>CECS 214:2006</small>
        <h1>平管管桥计算书</h1>
        <p>本计算书按平管适用条文自动生成，覆盖作用取值、组合、内力、强度、稳定、挠度和支墩基础验算。</p>
      </div>
      <div class="card">
        <strong>工程名称</strong><br />{escape(meta["project_name"])}<br />
        <strong>工程编号</strong><br />{escape(meta["project_code"])}<br />
        <strong>设计人</strong><br />{escape(meta.get("designer", "") or "-")}<br />
        <strong>支承形式</strong><br />{escape(support_type_label)}<br />
        <strong>规范范围</strong><br />CECS 214:2006 第 3、4、5、6.1、7.2、8.1、9.1、10.1-10.2 条<br />
        <strong>说明</strong><br />本计算书适用于平管 V1 版软件自动生成。
      </div>
    </div>
    <div class="summary-strip">
      <div class="summary-chip"><strong>控制应力</strong><span>{_fmt(stress["governing"]["equivalent_stress_mpa"])} MPa</span></div>
      <div class="summary-chip"><strong>控制挠度</strong><span>{_fmt(deflection["deflection_mm"])} mm</span></div>
      <div class="summary-chip"><strong>左支墩 qmax</strong><span>{_fmt(pier["governing"]["left_pier"]["qmax_kpa"])} kPa</span></div>
      <div class="summary-chip"><strong>右支墩 qmax</strong><span>{_fmt(pier["governing"]["right_pier"]["qmax_kpa"])} kPa</span></div>
    </div>
    {_render_validation(validations)}
    <h2>1. 截面参数</h2>
    { _render_kv_table([
      ("有效壁厚 t (mm)", derived["effective_thickness_mm"]),
      ("内径 Di (mm)", derived["inner_diameter_mm"]),
      ("截面面积 A (mm²)", derived["area_mm2"]),
      ("惯性矩 I (mm4)", derived["inertia_mm4"]),
      ("抵抗矩 W (mm3)", derived["section_modulus_mm3"]),
      ("回转半径 r (mm)", derived["radius_of_gyration_mm"]),
      ("钢管自重 (kN/m)", derived["steel_weight_kn_m"]),
      ("管内水重 (kN/m)", derived["water_weight_kn_m"]),
      ("总永久荷载 (kN/m)", derived["total_dead_load_kn_m"]),
    ])}
    <p class="muted">依据 4.2.1，按构件实际尺寸与材料单位体积自重计算永久作用。</p>

    <h2>2. 作用与取值</h2>
    {_render_table(
      ["作用", "类别", "竖向线荷载(kN/m)", "水平线荷载(kN/m)", "轴向应力(MPa)", "环向应力(MPa)", "水平力X(kN)", "水平力Y(kN)", "条文/说明"],
      [
        [
          row["label"],
          row["category"],
          _fmt(row.get("vertical_kn_m", 0.0)),
          _fmt(row.get("horizontal_kn_m", 0.0)),
          _fmt(row.get("axial_stress_mpa", 0.0)),
          _fmt(row.get("hoop_stress_mpa", 0.0)),
          _fmt(row.get("pier_horizontal_x_kn", 0.0)),
          _fmt(row.get("pier_horizontal_y_kn", 0.0)),
          row["formula"],
        ]
        for row in action_values
      ],
    )}

    <h2>3. 作用组合</h2>
    {_render_table(
      ["组合名", "类型", "验算目的", "条文", "主导可变作用", "竖向线荷载(kN/m)", "水平线荷载(kN/m)", "轴向应力(MPa)", "环向应力(MPa)", "X向水平力(kN)", "Y向水平力(kN)"],
      [
        [
          row["name"],
          row["combo_type"],
          row["description"],
          row["clause"],
          row.get("lead_action_label") or "-",
          _fmt(row["vertical_kn_m"]),
          _fmt(row["horizontal_kn_m"]),
          _fmt(row["axial_stress_mpa"]),
          _fmt(row["hoop_stress_mpa"]),
          _fmt(row["pier_horizontal_x_kn"]),
          _fmt(row["pier_horizontal_y_kn"]),
        ]
        for row in combinations
      ],
    )}
    <p class="muted">承载力组合按 5.2.2 的永久作用与可变作用主从组合思想实现；正常使用组合给出短期和长期两类结果。</p>

    <h2>4. 平管内力计算</h2>
    {_render_table(
      ["组合名", "弯矩 Mv(kN·m)", "弯矩 Mh(kN·m)", "合成弯矩(kN·m)", "剪力 Vv(kN)", "剪力 Vh(kN)", "合成剪力(kN)", "轴力 N(kN)", "左支座竖向反力(kN)", "右支座竖向反力(kN)"],
      [
        [
          row["name"],
          _fmt(row["moment_vertical_kn_m"]),
          _fmt(row["moment_horizontal_kn_m"]),
          _fmt(row["moment_resultant_kn_m"]),
          _fmt(row["shear_vertical_kn"]),
          _fmt(row["shear_horizontal_kn"]),
          _fmt(row["shear_resultant_kn"]),
          _fmt(row["axial_force_kn"]),
          _fmt(row["left_reaction_vertical_kn"]),
          _fmt(row["right_reaction_vertical_kn"]),
        ]
        for row in internal_forces
      ],
    )}
    <p class="muted">平管内力按第 6.1 节常用支承形式系数计算，三种边界条件分别对应两端支墩、一端锚墩一端支墩、两端锚墩。</p>

    <h2>5. 强度与稳定</h2>
    {_render_table(
      ["控制组合", "纵向应力(MPa)", "环向应力(MPa)", "剪应力(MPa)", "等效应力(MPa)", "设计强度(MPa)", "状态"],
      [[
        stress["governing"]["combo_name"] or "-",
        _fmt(stress["governing"]["longitudinal_stress_mpa"]),
        _fmt(stress["governing"]["hoop_stress_mpa"]),
        _fmt(stress["governing"]["shear_stress_mpa"]),
        _fmt(stress["governing"]["equivalent_stress_mpa"]),
        _fmt(stress["governing"]["allowable_stress_mpa"]),
        _status_label(stress["governing"]["status"]),
      ]],
    )}
    {_render_table(
      ["项目", "取值", "要求", "状态", "条文"],
      [
        [
          "真空稳定临界压力 Pcr (MPa)",
          _fmt(stability["critical_pressure_mpa"]),
          _fmt(stability["required_pressure_mpa"]),
          _status_label(stability["status"]),
          stability["clause"],
        ]
      ],
    )}
    <p class="muted">强度按第 7.2 节计算，采用纵向应力、环向应力和剪应力合成的等效应力进行判别。稳定按 8.1.2 的 Pcr ≥ 2Fv 校核。</p>

    <h2>6. 挠度验算</h2>
    {_render_table(
      ["控制组合", "计算挠度(mm)", "允许挠度(mm)", "状态", "条文"],
      [[
        deflection["governing_combo"] or "-",
        _fmt(deflection["deflection_mm"]),
        _fmt(deflection["allowable_mm"]),
        _status_label(deflection["status"]),
        deflection["clause"],
      ]],
    )}

    <h2>7. 支墩基础验算</h2>
    <h3>7.1 左支墩</h3>
    {_render_pier_table(pier["details"]["left_pier"])}
    <h3>7.2 右支墩</h3>
    {_render_pier_table(pier["details"]["right_pier"])}
    <p class="muted">基础偏心按 10.2.5 校核，抗滑稳定按 10.2.6 校核。支墩底面最大压应力与允许承载力特征值进行比较。</p>

    <h2 class="section-break">8. 公式追溯</h2>
    {_render_formula_trace(formula_trace)}

    <h2>9. 结论</h2>
    {_render_table(
      ["验算项目", "控制值", "状态"],
      [
        ["钢管强度", _fmt(stress["governing"]["equivalent_stress_mpa"]) + " MPa", _status_label(stress["status"])],
        ["真空稳定", _fmt(stability["critical_pressure_mpa"]) + " / " + _fmt(stability["required_pressure_mpa"]) + " MPa", _status_label(stability["status"])],
        ["使用挠度", _fmt(deflection["deflection_mm"]) + " / " + _fmt(deflection["allowable_mm"]) + " mm", _status_label(deflection["status"])],
        ["左支墩", _fmt(pier["governing"]["left_pier"]["qmax_kpa"]) + " kPa", _status_label(pier["governing"]["left_pier"]["status"])],
        ["右支墩", _fmt(pier["governing"]["right_pier"]["qmax_kpa"]) + " kPa", _status_label(pier["governing"]["right_pier"]["status"])],
      ],
    )}
  </div>
</body>
</html>"""
    return html


def _render_validation(validations: List[str]) -> str:
    if not validations:
        return ""
    items = "".join(f"<li>{escape(item)}</li>" for item in validations)
    return f"""
    <div class="card">
      <strong>输入校验提示</strong>
      <ul>{items}</ul>
    </div>
    """


def _render_pier_table(rows: Iterable[Dict[str, Any]]) -> str:
    return _render_table(
        ["组合", "竖向总力(kN)", "X向水平力(kN)", "Y向水平力(kN)", "偏心 ex(m)", "偏心 ey(m)", "qmax(kPa)", "qmin(kPa)", "抗滑系数", "状态"],
        [
            [
                row["combo_name"],
                _fmt(row["total_vertical_kn"]),
                _fmt(row["horizontal_x_kn"]),
                _fmt(row["horizontal_y_kn"]),
                _fmt(row["eccentricity_x_m"]),
                _fmt(row["eccentricity_y_m"]),
                _fmt(row["qmax_kpa"]),
                _fmt(row["qmin_kpa"]),
                _fmt(row["sliding_ratio"]),
                _status_label(row["status"]),
            ]
            for row in rows
        ],
    )


def _render_formula_trace(trace: Dict[str, Any]) -> str:
    blocks: List[str] = []
    blocks.append("<h3>8.1 截面参数</h3>" + _render_formula_items(trace["section"]))
    blocks.append("<h3>8.2 作用取值</h3>" + _render_formula_items(trace["actions"]))
    blocks.append("<h3>8.3 作用组合</h3>" + "".join(_render_combo_formula(item) for item in trace["combinations"]))
    blocks.append("<h3>8.4 内力计算</h3>" + "".join(_render_formula_group(item) for item in trace["internal_forces"]))
    blocks.append("<h3>8.5 强度验算</h3>" + "".join(_render_formula_group(item) for item in trace["stress"]))
    blocks.append("<h3>8.6 稳定与挠度</h3>" + _render_formula_items(trace["stability"]) + _render_formula_items(trace["deflection"]))
    blocks.append("<h3>8.7 支墩验算</h3>")
    blocks.append("<h4>左支墩</h4>" + "".join(_render_formula_group(item) for item in trace["piers"]["left_pier"]))
    blocks.append("<h4>右支墩</h4>" + "".join(_render_formula_group(item) for item in trace["piers"]["right_pier"]))
    return "".join(blocks)


def _render_formula_items(items: Iterable[Dict[str, Any]]) -> str:
    return "".join(
        f"""
        <div class="card">
          <strong>{escape(item["title"])}</strong><br />
          <span class="muted">{escape(item.get("clause", ""))}</span><br />
          <code>公式: {escape(item["formula"])}</code><br />
          <code>代入: {escape(item["substitution"])}</code><br />
          <code>结果: {escape(item["result"])}</code>
        </div>
        """
        for item in items
    )


def _render_combo_formula(item: Dict[str, Any]) -> str:
    detail_table = _render_table(
        ["分项", "系数", "竖向贡献(kN/m)", "水平贡献(kN/m)", "轴向应力贡献(MPa)", "环向应力贡献(MPa)"],
        [
            [
                row["action"],
                _fmt(row["factor"]),
                _fmt(row["vertical_kn_m"]),
                _fmt(row["horizontal_kn_m"]),
                _fmt(row["axial_mpa"]),
                _fmt(row["hoop_mpa"]),
            ]
            for row in item["details"]
        ],
    )
    return (
        f"""
        <div class="card">
          <strong>{escape(item["name"])}</strong><br />
          <code>公式: {escape(item["formula"])}</code><br />
          <code>代入: {escape(item["substitution"])}</code><br />
          <code>结果: {escape(item["result"])}</code>
        </div>
        {detail_table}
        """
    )


def _render_formula_group(item: Dict[str, Any]) -> str:
    pieces = [f"<div class=\"card\"><strong>{escape(item['name'])}</strong>"]
    if "status" in item:
        pieces.append(f"<br />状态: {_status_label(item['status'])}")
    for formula in item["formulae"]:
        pieces.append(
            f"<br /><code>{escape(formula['title'])}</code>"
            f"<br /><code>公式: {escape(formula['formula'])}</code>"
            f"<br /><code>代入: {escape(formula['substitution'])}</code>"
            f"<br /><code>结果: {escape(formula['result'])}</code>"
        )
    pieces.append("</div>")
    return "".join(pieces)


def _render_kv_table(rows: Iterable[tuple[str, Any]]) -> str:
    return _render_table(["项目", "取值"], [[name, _fmt(value)] for name, value in rows])


def _render_table(headers: List[str], rows: List[List[Any]]) -> str:
    head_html = "".join(f"<th>{escape(str(header))}</th>" for header in headers)
    row_html = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>"
        for cells in rows
    )
    return f"<table><thead><tr>{head_html}</tr></thead><tbody>{row_html}</tbody></table>"


def _status_label(status: str) -> str:
    enum = CheckResultStatus(status)
    return f'<span class="status-{escape(enum.value)}">{escape(enum.label)}</span>'


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.3f}"
    return escape(str(value))
