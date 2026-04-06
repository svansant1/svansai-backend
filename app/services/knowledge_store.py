from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"
BACKUP_FILE = DATA_DIR / "render_knowledge_backup.json"


def _read_json_file(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "entries" in data:
            return data["entries"]
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _write_json_file(path: Path, entries: List[Dict[str, Any]]) -> None:
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def load_knowledge() -> List[Dict[str, Any]]:
    knowledge_entries = _read_json_file(KNOWLEDGE_FILE)
    backup_entries = _read_json_file(BACKUP_FILE)

    if len(backup_entries) > len(knowledge_entries):
        return backup_entries

    return knowledge_entries


def save_knowledge(entries: List[Dict[str, Any]]) -> None:
    # 1. Save locally (immediate access for the current session)
    _write_json_file(KNOWLEDGE_FILE, entries)
    _write_json_file(BACKUP_FILE, entries)

    # 2. Trigger the GitHub Backup immediately
    from app.services.github_backup import backup_knowledge_to_github

    try:
        # We pass the entries directly to the backup service
        backup_knowledge_to_github(entries)
        print(f"[SVANSAI] Syncing {len(entries)} entries to GitHub...")
    except Exception as e:
        print(f"[SVANSAI] GitHub Sync failed: {e}")


def merge_new_entries(new_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existing = load_knowledge()

    seen = {
        (
            str(item.get("title", "")).strip().lower(),
            str(item.get("topic", "")).strip().lower(),
        )
        for item in existing
    }

    added_count = 0

    for entry in new_entries:
        key = (
            str(entry.get("title", "")).strip().lower(),
            str(entry.get("topic", "")).strip().lower(),
        )

        if key not in seen:
            existing.insert(0, entry)
            seen.add(key)
            added_count += 1

    save_knowledge(existing)

    print(f"[SVANSAI] Added {added_count} new entries")
    print(f"[SVANSAI] Total stored entries: {len(existing)}")

    return existing
