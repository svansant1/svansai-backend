from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/browser", tags=["browser"])

LATEST_TABS: dict[str, Any] = {
    "tabs": [],
    "updated_at": None,
}


class BrowserTab(BaseModel):
    id: int | None = None
    title: str | None = None
    url: str | None = None


class BrowserTabsPayload(BaseModel):
    tabs: list[BrowserTab]
    timestamp: str | None = None


@router.post("/tabs")
def update_tabs(payload: BrowserTabsPayload):
    LATEST_TABS["tabs"] = [tab.model_dump() for tab in payload.tabs]
    LATEST_TABS["updated_at"] = (
        payload.timestamp or datetime.now(timezone.utc).isoformat()
    )

    return {
        "ok": True,
        "count": len(LATEST_TABS["tabs"]),
        "updated_at": LATEST_TABS["updated_at"],
    }


@router.get("/tabs")
def get_tabs():
    return {
        "ok": True,
        "tabs": LATEST_TABS["tabs"],
        "updated_at": LATEST_TABS["updated_at"],
    }
