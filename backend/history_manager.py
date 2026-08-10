import json
from pathlib import Path
from datetime import datetime, timezone


HISTORY_FILE = Path(__file__).parent / "history.json"


def _load_history():

    if not HISTORY_FILE.exists():
        return []

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except (json.JSONDecodeError, OSError):
        pass

    return []


def _normalize_record(item):

    if not isinstance(item, dict):
        return None

    # Already V2
    if "analysis_id" in item:

        normalized = dict(item)

        normalized.setdefault(
            "created_at",
            datetime.now(timezone.utc).isoformat()
        )

        normalized.setdefault(
            "service",
            "ToolHunterAI API"
        )

        normalized.setdefault(
            "version",
            "2.0"
        )

        normalized.setdefault(
            "total_ads",
            len(normalized.get("ranking", []))
        )

        normalized.setdefault(
            "errors",
            []
        )

        return normalized

    # Legacy record
    normalized = {
        "analysis_id": None,
        "created_at": item.get("date"),
        "service": "ToolHunterAI API",
        "version": "1.0",
        "total_ads": 1,
        "best_choice": {
            "tool": item.get("tool_name"),
            "buy_score": item.get("buy_score", 0),
            "risk_score": item.get("risk_score", 0),
            "decision": item.get("decision"),
            "price": item.get("price"),
            "ad_score": item.get("ad_score")
        },
        "ranking": [],
        "explanation": None,
        "errors": []
    }

    return normalized


def save_history(result):

    if not isinstance(result, dict):
        return None

    if not result.get("analysis_id"):
        return None

    history = _load_history()

    item = _normalize_record(result)

    if item is None:
        return None

    history.append(item)

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=4
        )

    return item


def get_history():

    history = _load_history()

    normalized = []

    for item in history:

        record = _normalize_record(item)

        if record is not None:
            normalized.append(record)

    return normalized


def get_history_by_id(analysis_id):

    history = _load_history()

    for item in history:

        if item.get("analysis_id") == analysis_id:
            return _normalize_record(item)

    return None