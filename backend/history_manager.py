import json
from pathlib import Path
from datetime import datetime


HISTORY_FILE = Path(__file__).parent / "history.json"


def save_history(result):

    history = []

    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)


    result["date"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    history.append(result)


    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=4
        )


def get_history():

    if HISTORY_FILE.exists():

        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    return []