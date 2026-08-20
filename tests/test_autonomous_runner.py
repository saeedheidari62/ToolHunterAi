from backend.autonomous_runner import AutonomousRunner


class FakeScheduler:
    def __init__(self, result=None, error=None):
        self.result = result if result is not None else []
        self.error = error
        self.calls = 0

    def run_due(self):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def test_runner_executes_due_jobs_once():
    scheduler = FakeScheduler([{"status": "COMPLETED", "job_id": "bosch"}])
    result = AutonomousRunner(scheduler).run_once()
    assert result["status"] == "COMPLETED"
    assert result["runs"][0]["job_id"] == "bosch"
    assert scheduler.calls == 1


def test_runner_contains_scheduler_failure():
    scheduler = FakeScheduler(error=RuntimeError("boom"))
    result = AutonomousRunner(scheduler).run_once()
    assert result == {"status": "ERROR", "error": "RuntimeError"}
    assert scheduler.calls == 1
