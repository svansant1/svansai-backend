from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")  # example: svansant1/svansai-backend
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_BACKUP_PATH = os.getenv(
    "GITHUB_BACKUP_PATH",
    "data/render_knowledge_backup.json",
)


def _github_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


def backup_knowledge_to_github(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return {
            "ok": False,
            "error": "Missing GITHUB_TOKEN or GITHUB_REPO",
        }

    api_url = (
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_BACKUP_PATH}"
    )

    payload_data = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(entries),
        "entries": entries,
    }

    encoded_content = base64.b64encode(
        json.dumps(payload_data, indent=2, ensure_ascii=False).encode("utf-8")
    ).decode("utf-8")

    sha: Optional[str] = None

    get_resp = requests.get(
        api_url,
        headers=_github_headers(),
        params={"ref": GITHUB_BRANCH},
        timeout=30,
    )

    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")

    body = {
        "message": f"Backup SVANSAI knowledge ({len(entries)} entries)",
        "content": encoded_content,
        "branch": GITHUB_BRANCH,
    }

    if sha:
        body["sha"] = sha

    put_resp = requests.put(
        api_url,
        headers=_github_headers(),
        json=body,
        timeout=30,
    )

    if put_resp.status_code not in (200, 201):
        return {
            "ok": False,
            "error": put_resp.text,
            "status_code": put_resp.status_code,
        }

    return {
        "ok": True,
        "path": GITHUB_BACKUP_PATH,
        "count": len(entries),
    }
