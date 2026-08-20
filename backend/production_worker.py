from .autonomous_delivery import AutonomousDelivery


class ProductionWorker:
    """One-shot production cycle: scan due jobs, then deliver eligible alerts."""

    def __init__(self, runner, delivery):
        self.runner = runner
        self.delivery = delivery

    def run_once(self):
        scan_result = self.runner.run_once()
        if scan_result.get("status") != "COMPLETED":
            return {"status": "ERROR", "scan": scan_result, "delivery": None}
        delivery_result = self.delivery.deliver()
        return {"status": delivery_result["status"], "scan": scan_result, "delivery": delivery_result}
