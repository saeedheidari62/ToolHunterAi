from backend.worker import main


class FakeWorker:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def run_once(self):
        self.calls += 1
        return self.result


def test_worker_cli_disabled_is_safe():
    config = type("Config", (), {"worker_enabled": False, "validate": lambda self: {"ok": True}})()
    assert main(config=config) == 0


def test_worker_cli_invalid_config_fails_closed():
    config = type("Config", (), {"worker_enabled": True, "validate": lambda self: {"ok": False, "error": "invalid"}})()
    assert main(config=config) == 1


def test_worker_cli_success_returns_zero():
    config = type("Config", (), {"worker_enabled": True, "validate": lambda self: {"ok": True}})()
    worker = FakeWorker({"status": "COMPLETED"})
    assert main(config=config, worker=worker) == 0
    assert worker.calls == 1


def test_worker_cli_failure_returns_one():
    config = type("Config", (), {"worker_enabled": True, "validate": lambda self: {"ok": True}})()
    worker = FakeWorker({"status": "ERROR"})
    assert main(config=config, worker=worker) == 1
    assert worker.calls == 1
