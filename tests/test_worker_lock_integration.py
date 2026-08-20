from backend.worker import main


class FakeConfig:
    worker_enabled = True
    telegram_bot_token = "token"
    telegram_chat_id = "chat"

    def validate(self):
        return {"ok": True}


class FakeWorker:
    def __init__(self):
        self.calls = 0

    def run_once(self):
        self.calls += 1
        return {"status": "COMPLETED"}


class FakeLock:
    def __init__(self, acquired):
        self.acquired = acquired
        self.acquire_calls = 0
        self.release_calls = 0

    def acquire(self):
        self.acquire_calls += 1
        return self.acquired

    def release(self):
        self.release_calls += 1


def test_worker_cli_skips_when_lock_is_owned():
    worker = FakeWorker()
    lock = FakeLock(False)
    assert main(FakeConfig(), worker=worker, lock=lock) == 0
    assert worker.calls == 0
    assert lock.release_calls == 0


def test_worker_cli_releases_lock_after_success():
    worker = FakeWorker()
    lock = FakeLock(True)
    assert main(FakeConfig(), worker=worker, lock=lock) == 0
    assert worker.calls == 1
    assert lock.acquire_calls == 1
    assert lock.release_calls == 1
