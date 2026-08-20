from backend.worker_execution import run_production_cycle


class Config:
    worker_enabled = True

    def validate(self):
        return {"ok": True}


class Worker:
    def __init__(self, status="COMPLETED"):
        self.status = status
        self.calls = 0

    def run_once(self):
        self.calls += 1
        return {"status": self.status}


class Lock:
    def __init__(self, acquired=True):
        self.acquired = acquired
        self.acquire_calls = 0
        self.release_calls = 0

    def acquire(self):
        self.acquire_calls += 1
        return self.acquired

    def release(self):
        self.release_calls += 1


def test_disabled_cycle_is_safe():
    config = Config()
    config.worker_enabled = False
    worker = Worker()
    result = run_production_cycle(config, worker, Lock())
    assert result["status"] == "DISABLED"
    assert worker.calls == 0


def test_locked_cycle_does_not_run_worker():
    worker = Worker()
    lock = Lock(False)
    result = run_production_cycle(Config(), worker, lock)
    assert result["status"] == "LOCKED"
    assert worker.calls == 0
    assert lock.release_calls == 0


def test_successful_cycle_releases_lock():
    worker = Worker()
    lock = Lock(True)
    result = run_production_cycle(Config(), worker, lock)
    assert result["status"] == "COMPLETED"
    assert worker.calls == 1
    assert lock.release_calls == 1


def test_failed_cycle_still_releases_lock():
    worker = Worker("ERROR")
    lock = Lock(True)
    result = run_production_cycle(Config(), worker, lock)
    assert result["status"] == "ERROR"
    assert lock.release_calls == 1
