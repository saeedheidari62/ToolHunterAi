import sys

from .autonomous_delivery import AutonomousDelivery
from .autonomous_runner import AutonomousRunner
from .notification import NotificationService
from .notification_ledger import NotificationLedger
from .production_config import ProductionConfig
from .production_worker import ProductionWorker
from .telegram_notification import TelegramNotificationProvider
from .worker_execution import run_production_cycle


def build_worker(config):
    from .web_app import alert_engine, monitoring

    runner = AutonomousRunner(monitoring)
    provider = TelegramNotificationProvider(config.telegram_bot_token, config.telegram_chat_id)
    delivery = AutonomousDelivery(alert_engine, NotificationService(provider), NotificationLedger())
    return ProductionWorker(runner, delivery)


def main(config=None, worker=None, lock=None):
    config = config or ProductionConfig()
    validation = config.validate()
    if not validation.get("ok"):
        print(validation.get("error", "invalid production configuration"), file=sys.stderr)
        return 1
    if not config.worker_enabled:
        print("WORKER_DISABLED")
        return 0
    worker = worker or build_worker(config)
    result = run_production_cycle(config=config, worker=worker, lock=lock)
    print(result)
    return 0 if result["status"] in {"COMPLETED", "DISABLED", "LOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
