from datetime import datetime, timezone

from .deal_events import DealEventLedger
from .deal_store import DealStore


class DealTracker:
    """Track opportunity snapshots and emit meaningful deal-change events."""

    def __init__(self, store=None, event_ledger=None):
        self.store = store or DealStore()
        self.event_ledger = event_ledger or DealEventLedger(self.store.db_path)

    @staticmethod
    def _key(item):
        return item.get("token") or item.get("url") or item.get("id")

    @staticmethod
    def _snapshot(item):
        return {
            "listing_id": item.get("token") or item.get("id") or item.get("url"),
            "url": item.get("url", ""),
            "tool_id": item.get("tool_id", ""),
            "tool_name": item.get("tool_name", ""),
            "city": item.get("city", ""),
            "price": item.get("price"),
            "market_price": item.get("market_price"),
            "buy_score": item.get("buy_score"),
            "risk_score": item.get("risk_score"),
            "decision": item.get("decision") or item.get("buyer_decision"),
            "opportunity_score": item.get("opportunity_score"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def observe(self, item):
        key = self._key(item)
        if not key:
            return {"event": "IGNORED", "snapshot": None}
        current = self._snapshot(item)
        previous = self.store.get(key)
        self.store.save(current)
        if previous is None:
            result = {"event": "NEW_DEAL", "events": ["NEW_DEAL"], "snapshot": current, "previous": None}
            result["alert"] = self.event_ledger.record(result)
            return result
        events = []
        old_price, new_price = previous.get("price"), current.get("price")
        if isinstance(old_price, (int, float)) and isinstance(new_price, (int, float)) and old_price != new_price:
            events.append("PRICE_DROP" if new_price < old_price else "PRICE_RISE")
        if previous.get("decision") != current.get("decision"):
            events.append("DECISION_UPGRADE" if current.get("decision") == "BUY" else "DECISION_CHANGE")
        if previous.get("risk_score") != current.get("risk_score"):
            events.append("RISK_CHANGE")
        event = events[0] if events else "UNCHANGED"
        result = {"event": event, "events": events, "snapshot": current, "previous": previous}
        if event != "UNCHANGED":
            result["alert"] = self.event_ledger.record(result)
        return result

    def observe_many(self, items):
        changes = []
        for item in items:
            result = self.observe(item)
            if result["event"] != "UNCHANGED":
                changes.append(result)
        return changes

    def get(self, listing_id):
        return self.store.get(listing_id)
