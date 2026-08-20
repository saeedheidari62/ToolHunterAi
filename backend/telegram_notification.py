import json
import urllib.request


class TelegramNotificationProvider:
    """Provider-neutral Telegram adapter using Bot API over stdlib HTTP."""

    def __init__(self, bot_token=None, chat_id=None, timeout=10):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout

    def send(self, alert):
        if not self.bot_token or not self.chat_id:
            raise ValueError("Telegram notification configuration is missing")
        text = self._format(alert)
        payload = json.dumps({"chat_id": self.chat_id, "text": text, "disable_web_page_preview": True}).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        if not body.get("ok"):
            raise RuntimeError("Telegram API rejected notification")

    @staticmethod
    def _format(alert):
        label = alert.get("label", "ToolHunterAI Alert")
        title = alert.get("title", alert.get("tool_id", "Unknown tool"))
        price = alert.get("price", "-")
        url = alert.get("url", "")
        return f"{label}\n{title}\nPrice: {price}\n{url}".strip()
