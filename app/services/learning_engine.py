from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.config import settings
from app.services.knowledge_store import merge_new_entries
import random


TRUSTED_DOMAINS = {
    "developer.mozilla.org",
    "docs.python.org",
    "python.org",
    "react.dev",
    "nextjs.org",
    "nodejs.org",
    "fastapi.tiangolo.com",
    "postgresql.org",
    "mysql.com",
    "mongodb.com",
    "kubernetes.io",
    "docker.com",
    "owasp.org",
    "nist.gov",
    "cisa.gov",
    "microsoft.com",
    "learn.microsoft.com",
    "support.microsoft.com",
    "aws.amazon.com",
    "cloud.google.com",
    "azure.microsoft.com",
    "ubuntu.com",
    "kernel.org",
    "gnu.org",
    "mit.edu",
    "stanford.edu",
    "harvard.edu",
    "nasa.gov",
    "nih.gov",
    "who.int",
    "cdc.gov",
    "pubmed.ncbi.nlm.nih.gov",
    "britannica.com",
    "investopedia.com",
    "worldbank.org",
    "imf.org",
    "ibm.com",
    "techtarget.com",
    "wikipedia.org",
}


TOPICS = [
    "Operating systems overview",
    "Kernel architecture",
    "Process management",
    "Memory management",
    "File systems",
    "TCP/IP fundamentals",
    "DNS basics",
    "HTTP and HTTPS",
    "Python basics",
    "Python async programming",
    "JavaScript fundamentals",
    "TypeScript basics",
    "React hooks",
    "Next.js routing",
    "FastAPI basics",
    "SQL fundamentals",
    "Cybersecurity basics",
    "Malware types",
    "Encryption basics",
    "CPU architecture basics",
    "RAM types",
    "GPU basics",
    "Cloud computing basics",
    "Docker containers",
    "Kubernetes basics",
    "Graphic design fundamentals",
    "Typography basics",
    "UI design principles",
    "UX basics",
    "Accessibility basics",
    "Algorithms",
    "Data structures",
    "Debugging techniques",
    "System design basics",
    "REST APIs",
    "Authentication and authorization",
    "Zero trust basics",
    "Firewalls",
    "Linux commands",
    "Windows internals basics",
    "macOS architecture basics",
    "Device drivers",
    "Virtual memory",
    "Thread scheduling",
    "Boot process",
    "Network latency",
    "Wi-Fi standards",
    "Load balancing",
    "CI/CD pipelines",
    "Monitoring and logging",
]


USER_AGENT = "SVANSAI-LearningBot/1.0"


def inside_learning_window() -> bool:
    hour = datetime.now().hour
    return (
        settings.learning_window_start_hour <= hour < settings.learning_window_end_hour
    )


def is_trusted_domain(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return False

    if domain in TRUSTED_DOMAINS:
        return True

    return any(domain.endswith(f".{trusted}") for trusted in TRUSTED_DOMAINS)


def fetch_text(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    return " ".join(text.split())[:15000]


def summarize_for_topic(topic: str, text: str) -> str:
    sentences = text.split(". ")
    topic_words = [w.lower() for w in topic.split() if len(w) > 2]

    ranked: List[str] = []

    for sentence in sentences:
        lower = sentence.lower()

        if len(sentence.strip()) < 40:
            continue

        if any(word in lower for word in topic_words):
            ranked.append(sentence.strip())

    summary = ". ".join(ranked[:6]).strip()

    if summary and not summary.endswith("."):
        summary += "."

    return summary[:2500]


def learn_topics_for_run(search_fn) -> Dict[str, Any]:

    print("\n==============================")
    print("SVANSAI LEARNING STARTED")
    print("==============================\n")

    topics = random.sample(TOPICS, min(settings.topics_per_run, len(TOPICS)))

    saved_entries: List[Dict[str, Any]] = []

    for topic in topics:

        print(f"Learning Topic: {topic}")

        search_result = search_fn(topic, 10)

        if not search_result.get("ok"):
            print("Search failed")
            continue

        for result in search_result.get("results", [])[:5]:

            url = str(result.get("url") or "")
            title = str(result.get("title") or topic)

            if not is_trusted_domain(url):
                continue

            try:

                raw_text = fetch_text(url)
                summary = summarize_for_topic(topic, raw_text)

                if len(summary) < 100:
                    continue

                entry = {
                    "title": title,
                    "content": summary,
                    "topic": topic,
                    "url": url,
                    "source": "trusted_web",
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                    "validation_status": "trusted",
                    "confidence": 0.85,
                }

                saved_entries.append(entry)

                print("\n------------------------------")
                print("SVANSAI LEARNED")
                print(f"Topic: {topic}")
                print(f"Title: {title}")
                print(f"URL: {url}")
                print("------------------------------\n")

                break

            except Exception as e:
                print(f"Error learning {topic}: {e}")
                continue

    if saved_entries:

        merge_new_entries(saved_entries)

        print("\n==============================")
        print("SVANSAI SAVED KNOWLEDGE")
        print(f"Entries Saved: {len(saved_entries)}")
        print("==============================\n")

    else:

        print("\nNo new knowledge saved this run\n")

    print("SVANSAI LEARNING COMPLETE\n")

    return {
        "topics_attempted": len(topics),
        "entries_saved": len(saved_entries),
        "entries": saved_entries,
    }
