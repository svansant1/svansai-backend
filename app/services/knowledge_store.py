from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"


def load_knowledge() -> List[Dict[str, Any]]:
    if not KNOWLEDGE_FILE.exists():
        return []

    try:
        return json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_knowledge(entries: List[Dict[str, Any]]) -> None:
    KNOWLEDGE_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def merge_new_entries(new_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existing = load_knowledge()
    seen = {
        (
            str(item.get("title", "")).strip().lower(),
            str(item.get("topic", "")).strip().lower(),
        )
        for item in existing
    }

    for entry in new_entries:
        key = (
            str(entry.get("title", "")).strip().lower(),
            str(entry.get("topic", "")).strip().lower(),
        )
        if key not in seen:
            existing.insert(0, entry)
            seen.add(key)

    save_knowledge(existing)
    return existing
