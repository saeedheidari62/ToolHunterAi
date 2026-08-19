from pathlib import Path


def test_ci_workflow_keeps_main_triggers_and_regression_suite():
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"
    text = workflow.read_text(encoding="utf-8")
    assert "push:" in text
    assert "branches: [main]" in text
    assert "pull_request:" in text
    assert "python -m pytest -q tests" in text
    assert "python -m compileall -q backend" in text
