import os
import base64
import requests
import json


def backup_knowledge_to_github(entries):
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")  # format: "username/repo"
    file_path = "data/knowledge.json"

    if not token or not repo or not os.getenv("RENDER"):
        return "Backup skipped: Missing credentials or not on Render."

    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # 1. Get the current file's SHA (required by GitHub to update)
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        remote_data = json.loads(
            base64.b64decode(res.json()["content"]).decode("utf-8")
        )
        sha = res.json().get("sha")

    # 2. Prepare the new content
    content_str = json.dumps(entries, indent=2, ensure_ascii=False)
    encoded_content = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    if len(entries) <= len(remote_data):
        return f"Skipped: GitHub already has {len(remote_data)} entries (Local has {len(entries)})"

    # 3. Push to GitHub
    payload = {
        "message": f"SVANSAI Memory Update: {len(entries)} entries",
        "content": encoded_content,
        "sha": sha,
    }

    put_res = requests.put(url, json=payload, headers=headers)
    if put_res.status_code in [200, 201]:
        return "Success: Synced to GitHub."
    else:
        return f"Failed: {put_res.text}"
