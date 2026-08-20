from .production_config import ProductionConfig
from .worker_lock import WorkerLock


def run_production_cycle(config=None, worker=None, lock=None):
    config = config or ProductionConfig()
    validation = config.validate()
    if not validation["ok"]:
        return {"status": "CONFIG_ERROR", "error": validation["error"]}
    if not config.worker_enabled:
        return {"status": "DISABLED"}

    lock = lock or WorkerLock()
    if not lock.acquire():
        return {"status": "LOCKED"}
    try:
        result = worker.run_once()
        return {"status": result.get("status", "ERROR"), "result": result}
    finally:
        lock.release()
