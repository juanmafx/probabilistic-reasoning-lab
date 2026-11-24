# The report generator must never present earlier results as a new run.
import importlib.util
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[2] / "tools" / "generate_test_report.py"


@pytest.fixture
def report_tool(tmp_path, monkeypatch):
    specification = importlib.util.spec_from_file_location("generate_test_report", TOOL)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    monkeypatch.setattr(module, "REPORT_DIRECTORY", tmp_path)
    monkeypatch.setattr(module, "JUNIT_PATH", tmp_path / "junit.xml")
    monkeypatch.setattr(module, "SUMMARY_PATH", tmp_path / "summary.md")
    return module


def test_failed_run_does_not_republish_previous_results(report_tool, monkeypatch):
    report_tool.JUNIT_PATH.write_text(
        '<testsuites><testsuite tests="9" failures="0" errors="0" skipped="0" time="1"/>'
        "</testsuites>",
        encoding="utf-8",
    )
    report_tool.SUMMARY_PATH.write_text("previous summary", encoding="utf-8")
    monkeypatch.setattr(report_tool, "run_tests", lambda: 4)
    assert report_tool.main() == 4
    assert not report_tool.JUNIT_PATH.exists()
    assert not report_tool.SUMMARY_PATH.exists()
