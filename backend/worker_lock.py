import os
import sqlite3
import time
import uuid


class WorkerLock:
    """Persistent single-owner lock for one-shot production worker execution."""

    def __init__(self, path=None, stale_after_seconds=900):
        self.path = str(path or os.environ.get("WORKER_LOCK_PATH", "worker_lock.sqlite3"))
        self.stale_after_seconds = stale_after_seconds
        self.owner = uuid.uuid4().hex
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def _init_db(self):
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS worker_lock (id INTEGER PRIMARY KEY CHECK (id = 1), owner TEXT NOT NULL, acquired_at REAL NOT NULL)")

    def acquire(self):
        now = time.time()
        with self._connect() as db:
            row = db.execute("SELECT owner, acquired_at FROM worker_lock WHERE id = 1").fetchone()
            if row and row[0] != self.owner and now - row[1] < self.stale_after_seconds:
                return False
            db.execute("INSERT OR REPLACE INTO worker_lock(id, owner, acquired_at) VALUES(1, ?, ?)", (self.owner, now))
            return True

    def release(self):
        with self._connect() as db:
            db.execute("DELETE FROM worker_lock WHERE id = 1 AND owner = ?", (self.owner,))

    def status(self):
        with self._connect() as db:
            row = db.execute("SELECT owner, acquired_at FROM worker_lock WHERE id = 1").fetchone()
        if not row:
            return {"locked": False, "stale": False}
        age = max(0.0, time.time() - row[1])
        stale = age >= self.stale_after_seconds
        return {"locked": not stale, "stale": stale, "age_seconds": round(age, 3)}
