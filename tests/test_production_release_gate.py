from backend.production_config import ProductionConfig
from backend.readiness import readiness
from backend.web_app import app
from backend.worker import main
from backend.worker_execution import run_production_cycle


class GateWorker:
    def run_once(self):
        return {"status": "COMPLETED"}


class GateLock:
    def acquire(self):
        return True

    def release(self):
        return None


def test_production_release_gate_contract():
    client = app.test_client()
    health = client.get("/health")
    assert health.status_code == 200
    health_payload = health.get_json()
    assert health_payload["status"] == "ok"
    assert health_payload["service"] == "ToolHunterAI Web"
    assert isinstance(health_payload["ai_discovery_enabled"], bool)

    config = ProductionConfig({})
    ready = readiness(config)
    assert ready["config_valid"] is True
    assert main(config=config) == 0

    enabled = ProductionConfig({"WORKER_ENABLED": "true"})
    cycle = run_production_cycle(enabled, GateWorker(), GateLock())
    assert cycle["status"] == "COMPLETED"
