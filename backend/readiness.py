from .production_config import ProductionConfig


def readiness(config=None):
    config = config or ProductionConfig()
    validation = config.validate()
    return {
        "ready": bool(validation.get("ok")),
        "config_valid": bool(validation.get("ok")),
        "worker_enabled": config.worker_enabled,
        "notification_enabled": config.notification_enabled,
        "error": validation.get("error"),
    }
