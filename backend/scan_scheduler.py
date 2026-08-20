import threading
from datetime import datetime, timezone, timedelta


class ScanScheduler:
    """Small dependency-free scheduler for one or more bounded scan jobs."""

    def __init__(self, runner, now=None):
        self.runner = runner
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.jobs = {}
        self._locks = {}
        self._mutex = threading.Lock()

    def add_job(self, job_id, cities, interval_seconds=3600, tool_ids=None, top_n=None):
        if not job_id or not cities:
            raise ValueError("job_id and cities are required")
        interval_seconds = int(interval_seconds)
        if interval_seconds < 60:
            raise ValueError("interval_seconds must be at least 60")
        now = self.now()
        with self._mutex:
            self.jobs[job_id] = {
                "job_id": job_id,
                "cities": list(cities),
                "tool_ids": list(tool_ids) if tool_ids else None,
                "top_n": top_n,
                "interval_seconds": interval_seconds,
                "last_run": None,
                "next_run": now,
                "status": "READY",
                "last_result": None,
                "last_error": None,
            }
            self._locks.setdefault(job_id, threading.Lock())
        return dict(self.jobs[job_id])

    def remove_job(self, job_id):
        with self._mutex:
            return self.jobs.pop(job_id, None) is not None

    def run_job(self, job_id, force=False):
        with self._mutex:
            job = self.jobs.get(job_id)
            lock = self._locks.get(job_id)
        if not job:
            raise KeyError(job_id)
        if not lock.acquire(blocking=False):
            return {"status": "SKIPPED", "reason": "ALREADY_RUNNING", "job_id": job_id}
        try:
            now = self.now()
            if not force and job["next_run"] > now:
                return {"status": "SKIPPED", "reason": "NOT_DUE", "job_id": job_id, "next_run": job["next_run"].isoformat()}
            with self._mutex:
                job["status"] = "RUNNING"
                job["last_error"] = None
            try:
                result = self.runner(
                    job["cities"],
                    tool_ids=job["tool_ids"],
                    top_n=job["top_n"],
                )
                finished = self.now()
                with self._mutex:
                    job["last_run"] = finished
                    job["next_run"] = finished + timedelta(seconds=job["interval_seconds"])
                    job["status"] = "READY"
                    job["last_result"] = result
                return {"status": "COMPLETED", "job_id": job_id, "result": result}
            except Exception as exc:
                finished = self.now()
                with self._mutex:
                    job["last_run"] = finished
                    job["next_run"] = finished + timedelta(seconds=job["interval_seconds"])
                    job["status"] = "ERROR"
                    job["last_error"] = type(exc).__name__
                return {"status": "ERROR", "job_id": job_id, "error": type(exc).__name__}
        finally:
            lock.release()

    def run_due(self):
        with self._mutex:
            due = [job_id for job_id, job in self.jobs.items() if job["next_run"] <= self.now()]
        return [self.run_job(job_id) for job_id in due]

    def status(self):
        with self._mutex:
            return {
                "status": "HEALTHY",
                "active_jobs": sum(job["status"] == "RUNNING" for job in self.jobs.values()),
                "jobs": [
                    {key: (value.isoformat() if isinstance(value, datetime) else value)
                     for key, value in job.items() if key != "last_result"}
                    for job in self.jobs.values()
                ],
            }
