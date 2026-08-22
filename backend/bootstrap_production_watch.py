import os

from .watchlist_store import WatchlistStore


WATCH_ID = "production-bosch"
DEFAULT_CITIES = ("tehran", "karaj")
DEFAULT_TOOLS = ("bosch_gbh_2_26",)


def bootstrap():
    cities = tuple(x.strip() for x in os.getenv("SCAN_CITIES", ",".join(DEFAULT_CITIES)).split(",") if x.strip())
    tool_ids = tuple(x.strip() for x in os.getenv("SCAN_TOOL_IDS", ",".join(DEFAULT_TOOLS)).split(",") if x.strip())
    interval = int(os.getenv("SCAN_INTERVAL_SECONDS", "1800"))
    top_n = int(os.getenv("SCAN_TOP_N", "10"))
    WatchlistStore().upsert(WATCH_ID, cities, interval_seconds=interval, tool_ids=tool_ids, top_n=top_n, enabled=True)
    print({"watch_id": WATCH_ID, "cities": cities, "tool_ids": tool_ids, "interval_seconds": interval, "top_n": top_n})


if __name__ == "__main__":
    bootstrap()
