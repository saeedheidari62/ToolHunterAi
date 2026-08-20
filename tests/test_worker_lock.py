from backend.worker_lock import WorkerLock


def test_worker_lock_allows_one_owner_and_blocks_second(tmp_path):
    path = tmp_path / "worker.sqlite3"
    first = WorkerLock(path, stale_after_seconds=900)
    second = WorkerLock(path, stale_after_seconds=900)
    assert first.acquire() is True
    assert second.acquire() is False
    first.release()
    assert second.acquire() is True


def test_worker_lock_recovers_stale_owner(tmp_path):
    path = tmp_path / "worker.sqlite3"
    first = WorkerLock(path, stale_after_seconds=0)
    second = WorkerLock(path, stale_after_seconds=0)
    assert first.acquire() is True
    assert second.acquire() is True
    second.release()
