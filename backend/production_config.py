import os


class ProductionConfig:
    """Environment-backed production configuration without hard-coded secrets."""

    def __init__(self, environ=None):
        env = environ or os.environ
        self.telegram_bot_token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_chat_id = env.get("TELEGRAM_CHAT_ID", "").strip()
        self.notification_enabled = env.get("NOTIFICATION_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.worker_enabled = env.get("WORKER_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}

    def validate(self):
        if self.notification_enabled and (not self.telegram_bot_token or not self.telegram_chat_id):
            return {"ok": False, "error": "Telegram notification configuration is incomplete"}
        return {"ok": True}
