from pathlib import Path

from cecs214_plain_pipe.ui.template_store import (
    build_builtin_template,
    load_shared_template,
    save_shared_template,
)


def test_load_shared_template_reads_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "shared_template.json"
    path.write_text(
        """
        {
          "ui_preferences": {
            "results_tab": "formula",
            "preview_height": 720,
            "show_formula_trace_expanded": true,
            "sidebar_tips_expanded": false
          },
          "project_defaults": {
            "meta": {"project_name": "模板工程"}
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    template, status = load_shared_template(path)

    assert status["source"] == "disk"
    assert template["ui_preferences"]["preview_height"] == 720
    assert template["project_defaults"]["meta"]["project_name"] == "模板工程"
    assert "geometry" in template["project_defaults"]


def test_load_shared_template_falls_back_when_missing(tmp_path: Path) -> None:
    template, status = load_shared_template(tmp_path / "missing.json")

    assert status["source"] == "builtin"
    assert "ui_preferences" in template
    assert template["project_defaults"]["meta"]["project_name"] == "平管管桥示例工程"


def test_load_shared_template_falls_back_when_json_is_invalid(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not-json}", encoding="utf-8")

    template, status = load_shared_template(path)

    assert status["source"] == "builtin"
    assert "error" in status


def test_save_shared_template_writes_normalized_json(tmp_path: Path) -> None:
    path = tmp_path / "shared_template.json"
    template = build_builtin_template()
    template["project_defaults"]["meta"]["project_name"] = "归档模板"

    save_shared_template(path, template)

    written = path.read_text(encoding="utf-8")
    assert '"project_name": "归档模板"' in written
    assert written.endswith("\n")
