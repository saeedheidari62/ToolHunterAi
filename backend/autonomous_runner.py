class AutonomousRunner:
    """One-shot runner for production schedulers; intentionally does not own a thread."""

    def __init__(self, scheduler):
        self.scheduler = scheduler

    def run_once(self):
        try:
            return {"status": "COMPLETED", "runs": self.scheduler.run_due()}
        except Exception as exc:
            return {"status": "ERROR", "error": type(exc).__name__}
