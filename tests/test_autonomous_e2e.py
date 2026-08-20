from backend.production_worker import ProductionWorker
from backend.autonomous_delivery import AutonomousDelivery
from backend.notification import ConsoleNotificationProvider, NotificationService
from backend.notification_ledger import NotificationLedger
from backend.autonomous_runner import AutonomousRunner


class FakeScheduler:
    def __init__(self):
        self.failed = False
        self.calls = 0

    def run_due(self):
        self.calls += 1
        if self.failed:
            raise RuntimeError("scan failed")
        return [{"status": "COMPLETED", "job_id": "scan-1"}]


class FakeAlerts:
    def __init__(self):
        self.events = [{"event_id": "deal-1", "priority": 90, "event": "NEW_DEAL", "tool_id": "bosch_gbh_2_26", "price": 8500000}]

    def recent(self, limit=10, min_priority=70):
        return [e for e in self.events if e["priority"] >= min_priority][:limit]


def build_worker(tmp_path, scheduler):
    provider = ConsoleNotificationProvider()
    delivery = AutonomousDelivery(
        FakeAlerts(),
        NotificationService(provider),
        NotificationLedger(tmp_path / "delivery.sqlite3"),
    )
    return ProductionWorker(AutonomousRunner(scheduler), delivery), provider


def test_full_autonomous_cycle_delivers_once(tmp_path):
    scheduler = FakeScheduler()
    worker, provider = build_worker(tmp_path, scheduler)

    first = worker.run_once()
    second = worker.run_once()

    assert first["status"] == "COMPLETED"
    assert first["delivery"]["delivered"] == 1
    assert second["delivery"]["delivered"] == 0
    assert len(provider.sent) == 1
    assert scheduler.calls == 2


def test_full_autonomous_cycle_blocks_delivery_after_scan_failure(tmp_path):
    scheduler = FakeScheduler()
    worker, provider = build_worker(tmp_path, scheduler)
    scheduler.failed = True

    result = worker.run_once()

    assert result["status"] == "ERROR"
    assert result["delivery"] is None
    assert provider.sent == []
