from __future__ import annotations

import threading
import time

from fastapi import FastAPI

from app.config import settings
from app.services.learning_alerts import send_alert_email
from app.services.learning_engine import inside_learning_window, learn_topics_for_run
from app.services.learning_status import (
    load_learning_status,
    mark_learning_completed,
    mark_learning_error,
    mark_learning_started,
)
from app.services.search_client import search_topic

app = FastAPI(title=settings.app_name)


def learning_loop():
    while True:
        try:
            if inside_learning_window():
                mark_learning_started()
                result = learn_topics_for_run(search_topic)
                mark_learning_completed(
                    topics_attempted=result["topics_attempted"],
                    entries_saved=result["entries_saved"],
                )
            else:
                status = load_learning_status()
                if status.get("running"):
                    mark_learning_completed(
                        topics_attempted=status.get("topics_attempted_today", 0),
                        entries_saved=status.get("entries_saved_today", 0),
                    )
        except Exception as error:
            mark_learning_error(str(error))
            send_alert_email(
                subject="SVANSAI Learning Error",
                body=f"SVANSAI learning failed:\n\n{error}",
            )

        time.sleep(settings.run_interval_minutes * 60)


@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=learning_loop, daemon=True)
    thread.start()


@app.get("/")
def root():
    return {"ok": True, "app": settings.app_name}


@app.get("/learning/status")
def learning_status():
    return {"ok": True, "status": load_learning_status()}


@app.get("/test-alert")
def test_alert():
    send_alert_email(
        subject="SVANSAI Test Alert",
        body="SVANSAI email alerts are working.",
    )
    return {"ok": True, "message": "Test alert attempted."}


@app.get("/test-search")
def test_search():
    return search_topic("Operating systems overview", 5)


@app.get("/api")
def api_root():
    return {"ok": True, "service": "SVANSAI API"}


@app.get("/learning/data")
def get_learning_data():
    from app.services.knowledge_store import load_knowledge

    return {"ok": True, "entries": load_knowledge()}
