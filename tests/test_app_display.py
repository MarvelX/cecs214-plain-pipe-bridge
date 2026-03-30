from cecs214_plain_pipe.models import default_project_input

from app import stringify_display_rows


def test_stringify_display_rows_normalizes_mixed_value_columns() -> None:
    rows = [
        {"项目": "工程名称", "取值": "模板工程", "单位": ""},
        {"项目": "跨径 L", "取值": 24.0, "单位": "m"},
        {"项目": "备注", "取值": None, "单位": ""},
    ]

    display_rows = stringify_display_rows(rows)

    assert display_rows == [
        {"项目": "工程名称", "取值": "模板工程", "单位": ""},
        {"项目": "跨径 L", "取值": "24.0", "单位": "m"},
        {"项目": "备注", "取值": "-", "单位": ""},
    ]
    assert all(isinstance(value, str) for row in display_rows for value in row.values())


def test_stringify_display_rows_handles_factor_summary_blanks_and_numbers() -> None:
    project = default_project_input()
    rows = [
        {"作用": "重要性系数 γ0", "γQ": project.combination_factors.importance_factor, "φ": "", "ψ": ""},
        {"作用": "活荷载", "γQ": 1.4, "φ": 0.7, "ψ": 0.4},
    ]

    display_rows = stringify_display_rows(rows)

    assert display_rows[0]["γQ"] == str(project.combination_factors.importance_factor)
    assert display_rows[0]["φ"] == ""
    assert display_rows[1]["φ"] == "0.7"
    assert display_rows[1]["ψ"] == "0.4"
