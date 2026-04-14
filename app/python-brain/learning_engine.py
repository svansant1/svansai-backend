from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import settings
from knowledge_store import merge_new_entries
import random


TRUSTED_DOMAINS = [
    # Education
    "khanacademy.org",
    "coursera.org",
    "edx.org",
    "udemy.com",
    "brilliant.org",
    # Academic
    "mit.edu",
    "harvard.edu",
    "stanford.edu",
    "berkeley.edu",
    "ox.ac.uk",
    "cam.ac.uk",
    # Science
    "nasa.gov",
    "nationalgeographic.com",
    "scientificamerican.com",
    "nature.com",
    "sciencedaily.com",
    # General Education
    "britannica.com",
    "education.com",
    "scholastic.com",
    "howstuffworks.com",
    # Math
    "mathisfun.com",
    "purplemath.com",
    "wolframalpha.com",
    # Programming
    "developer.mozilla.org",
    "w3schools.com",
    "freecodecamp.org",
    "geeksforgeeks.org",
    "stackoverflow.com",
    # Government Education
    "ed.gov",
    "usa.gov",
    "gov.uk",
    # Technology
    "ibm.com",
    "microsoft.com",
    "google.com",
    "cloudflare.com",
    # Learning & Research
    "openai.com",
    "arxiv.org",
    "researchgate.net",
    # General Knowledge
    "bbc.com",
    "history.com",
    "smithsonianmag.com",
]

TOPICS = [
    # =========================
    # MATH - FOUNDATIONS
    # =========================
    "basic addition explained step by step",
    "basic subtraction explained simply",
    "multiplication fundamentals",
    "division explained for beginners",
    "place value basics",
    "rounding numbers explained",
    "fractions for beginners",
    "decimals explained step by step",
    "percentages explained simply",
    "ratios and proportions basics",
    # =========================
    # MATH - INTERMEDIATE
    # =========================
    "pre algebra fundamentals",
    "solving simple equations",
    "variables explained",
    "order of operations explained",
    "negative numbers explained",
    "absolute value explained",
    "linear equations basics",
    "graphing basics explained",
    "basic geometry concepts",
    "area and perimeter explained",
    # =========================
    # MATH - ADVANCED
    # =========================
    "algebra fundamentals",
    "quadratic equations basics",
    "trigonometry basics",
    "calculus introduction",
    "statistics fundamentals",
    "probability basics",
    "functions explained",
    "logarithms explained",
    "polynomials explained",
    "advanced algebra concepts",
    # =========================
    # SCIENCE - GENERAL
    # =========================
    "scientific method explained",
    "basic physics concepts",
    "basic chemistry concepts",
    "basic biology concepts",
    "earth science fundamentals",
    "energy explained",
    "force and motion explained",
    "states of matter explained",
    "atoms explained",
    "chemical reactions explained",
    # =========================
    # SCIENCE - ADVANCED
    # =========================
    "genetics basics",
    "ecosystems explained",
    "cell biology basics",
    "thermodynamics basics",
    "electricity explained",
    "magnetism explained",
    "waves and sound explained",
    "light and optics explained",
    "astronomy basics",
    "space science fundamentals",
    # =========================
    # LANGUAGE ARTS
    # =========================
    "grammar basics",
    "sentence structure explained",
    "reading comprehension strategies",
    "writing fundamentals",
    "paragraph structure explained",
    "essay writing basics",
    "punctuation rules explained",
    "parts of speech explained",
    "vocabulary building strategies",
    "critical reading skills",
    # =========================
    # HISTORY
    # =========================
    "world history basics",
    "american history fundamentals",
    "ancient civilizations explained",
    "modern history basics",
    "government basics",
    "civics fundamentals",
    "geography fundamentals",
    "historical timelines explained",
    "important historical events",
    "history critical thinking skills",
    # =========================
    # COMPUTER SCIENCE
    # =========================
    "computer basics explained",
    "how computers work",
    "programming basics",
    "python programming basics",
    "javascript basics",
    "html basics",
    "css basics",
    "software development basics",
    "algorithms explained",
    "data structures basics",
    # =========================
    # ENGINEERING
    # =========================
    "engineering fundamentals",
    "mechanical engineering basics",
    "electrical engineering basics",
    "civil engineering basics",
    "robotics fundamentals",
    "systems thinking explained",
    "design thinking explained",
    "problem solving engineering methods",
    # =========================
    # FINANCE
    # =========================
    "money basics",
    "budgeting basics",
    "saving money fundamentals",
    "investing basics",
    "interest explained",
    "compound interest explained",
    "credit basics",
    "financial literacy fundamentals",
    # =========================
    # LIFE SKILLS
    # =========================
    "critical thinking skills",
    "problem solving techniques",
    "decision making skills",
    "time management skills",
    "study skills",
    "learning strategies",
    "communication skills",
    "goal setting basics",
    # =========================
    # CREATIVE SUBJECTS
    # =========================
    "art fundamentals",
    "music basics",
    "creative thinking",
    "drawing basics",
    "design fundamentals",
    "visual communication basics",
    # =========================
    # GENERAL KNOWLEDGE
    # =========================
    "how learning works",
    "memory techniques",
    "brain learning strategies",
    "curiosity based learning",
    "educational psychology basics",
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
            all_entries = merge_new_entries(saved_entries)

            print("\n==============================")
            print("SVANSAI SAVED KNOWLEDGE")
            print(f"Entries Saved: {len(saved_entries)}")
            print(f"Total Knowledge Entries: {len(all_entries)}")
            print("==============================\n")
        else:

            print("\nNo new knowledge saved this run\n")

    print("SVANSAI LEARNING COMPLETE\n")

    return {
        "topics_attempted": len(topics),
        "entries_saved": len(saved_entries),
        "entries": saved_entries,
    }
