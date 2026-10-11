import json
from pathlib import Path

from ddd_conformance.cli import main


def test_cli_writes_json_report(tmp_path: Path) -> None:
    source = tmp_path / "order.py"
    source.write_text("class Order: pass", encoding="utf-8")
    output = tmp_path / "report.json"

    exit_code = main([str(tmp_path), "--output", str(output)])

    assert exit_code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["summary"]["files_analyzed"] == 1
    assert report["summary"]["classes"] == 1
