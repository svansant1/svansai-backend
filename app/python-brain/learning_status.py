from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATUS_FILE = DATA_DIR / "learning_status.json"


DEFAULT_STATUS: Dict[str, Any] = {
    "running": False,
    "last_started_at": None,
    "last_completed_at": None,
    "last_error_at": None,
    "last_error_message": "",
    "topics_attempted_today": 0,
    "entries_saved_today": 0,
    "mode": "training",
    "message": "Please wait — I am still learning.",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_learning_status() -> Dict[str, Any]:
    if not STATUS_FILE.exists():
        return DEFAULT_STATUS.copy()

    try:
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_STATUS.copy()


def save_learning_status(status: Dict[str, Any]) -> None:
    STATUS_FILE.write_text(json.dumps(status, indent=2), encoding="utf-8")


def mark_learning_started() -> None:
    status = load_learning_status()
    status["running"] = True
    status["last_started_at"] = _now()
    status["message"] = "Please wait — I am still learning."
    save_learning_status(status)


def mark_learning_completed(topics_attempted: int, entries_saved: int) -> None:
    status = load_learning_status()
    status["running"] = False
    status["last_completed_at"] = _now()
    status["topics_attempted_today"] = topics_attempted
    status["entries_saved_today"] = entries_saved
    status["message"] = "Learning cycle complete."
    save_learning_status(status)


def mark_learning_error(message: str) -> None:
    status = load_learning_status()
    status["running"] = False
    status["last_error_at"] = _now()
    status["last_error_message"] = message
    status["message"] = "Learning encountered an error."
    save_learning_status(status)
