from backend.production_worker import ProductionWorker


class FakeRunner:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def run_once(self):
        self.calls += 1
        return self.result


class FakeDelivery:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def deliver(self):
        self.calls += 1
        return self.result


def test_worker_runs_scan_then_delivery():
    runner = FakeRunner({"status": "COMPLETED", "runs": []})
    delivery = FakeDelivery({"status": "COMPLETED", "delivered": 1})
    result = ProductionWorker(runner, delivery).run_once()
    assert result["status"] == "COMPLETED"
    assert result["delivery"]["delivered"] == 1
    assert runner.calls == 1
    assert delivery.calls == 1


def test_worker_does_not_deliver_after_scan_failure():
    runner = FakeRunner({"status": "ERROR", "error": "RuntimeError"})
    delivery = FakeDelivery({"status": "COMPLETED", "delivered": 1})
    result = ProductionWorker(runner, delivery).run_once()
    assert result["status"] == "ERROR"
    assert result["delivery"] is None
    assert delivery.calls == 0
