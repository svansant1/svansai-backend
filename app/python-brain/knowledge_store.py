from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"
BACKUP_FILE = DATA_DIR / "render_knowledge_backup.json"


def _normalize_entries(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, dict) and isinstance(data.get("entries"), list):
        return data["entries"]
    if isinstance(data, list):
        return data
    return []


def _read_json_file(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    try:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return []
        parsed = json.loads(raw)
        return _normalize_entries(parsed)
    except Exception as e:
        print(f"[SVANSAI] Failed reading {path.name}: {e}")
        return []


def _entries_to_json(entries: List[Dict[str, Any]]) -> str:
    return json.dumps(entries, indent=2, ensure_ascii=False, sort_keys=False)


def _write_json_file(path: Path, entries: List[Dict[str, Any]]) -> None:
    path.write_text(_entries_to_json(entries), encoding="utf-8")


def _entry_key(entry: Dict[str, Any]) -> Tuple[str, str, str]:
    return (
        str(entry.get("title", "")).strip().lower(),
        str(entry.get("topic", "")).strip().lower(),
        str(entry.get("url", "")).strip().lower(),
    )


def _content_hash(entries: List[Dict[str, Any]]) -> str:
    payload = _entries_to_json(entries)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_knowledge() -> List[Dict[str, Any]]:
    """
    Loads the best available knowledge source.
    Prefers the longer file if one is ahead of the other.
    """
    knowledge_entries = _read_json_file(KNOWLEDGE_FILE)
    backup_entries = _read_json_file(BACKUP_FILE)

    if len(backup_entries) > len(knowledge_entries):
        print(
            f"[SVANSAI] Loaded knowledge from backup file "
            f"({len(backup_entries)} entries)"
        )
        return backup_entries

    print(
        f"[SVANSAI] Loaded knowledge from main file "
        f"({len(knowledge_entries)} entries)"
    )
    return knowledge_entries


def save_knowledge(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Saves the exact same final entries to both local files.
    Then attempts GitHub backup only if content actually changed.
    Returns the final saved entries.
    """
    entries = entries or []

    existing_main = _read_json_file(KNOWLEDGE_FILE)
    existing_backup = _read_json_file(BACKUP_FILE)

    old_hash = _content_hash(
        existing_main if len(existing_main) >= len(existing_backup) else existing_backup
    )
    new_hash = _content_hash(entries)

    # Always write both local files so local state stays in sync
    _write_json_file(KNOWLEDGE_FILE, entries)
    _write_json_file(BACKUP_FILE, entries)

    print(f"[SVANSAI] Local knowledge saved: {len(entries)} entries")

    # Only push to GitHub if actual content changed
    if old_hash != new_hash:
        from github_backup import backup_knowledge_to_github

        try:
            result = backup_knowledge_to_github(entries)
            print(f"[SVANSAI] GitHub backup result: {result}")
        except Exception as e:
            print(f"[SVANSAI] GitHub Sync failed: {e}")
    else:
        print("[SVANSAI] GitHub backup skipped: no knowledge changes detected")

    return entries


def merge_new_entries(new_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merges new entries into stored knowledge using title+topic+url dedupe.
    Returns the final saved knowledge list.
    """
    existing = load_knowledge()
    if not new_entries:
        print("[SVANSAI] No new entries passed into merge")
        return existing

    seen = {_entry_key(item) for item in existing}
    added_count = 0

    for entry in new_entries:
        key = _entry_key(entry)
        if key in seen:
            continue

        existing.insert(0, entry)
        seen.add(key)
        added_count += 1

    final_entries = save_knowledge(existing)

    print(f"[SVANSAI] Added {added_count} new entries")
    print(f"[SVANSAI] Total stored entries: {len(final_entries)}")

    return final_entries
