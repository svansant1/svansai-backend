from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from learning_status import load_learning_status
from search_client import search_topic

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "ok": True,
        "app": settings.app_name,
        "status": "running",
        "mode": "intelligent",
    }


# =========================
# INTERNAL HELPERS
# =========================
def score_entry(message: str, entry: dict) -> int:
    msg = message.lower().strip()
    title = str(entry.get("title", "")).lower()
    topic = str(entry.get("topic", "")).lower()
    content = str(entry.get("content", "")).lower()

    score = 0

    if msg in topic:
        score += 4
    if msg in title:
        score += 4
    if msg in content:
        score += 2

    words = [w for w in msg.split() if len(w) > 2]
    overlap = sum(1 for w in words if w in title or w in topic or w in content)
    score += min(overlap, 4)

    return score


def find_knowledge_matches(
    message: str, knowledge: list[dict], limit: int = 3
) -> list[dict]:
    scored: list[tuple[int, dict]] = []

    for entry in knowledge:
        score = score_entry(message, entry)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored[:limit]]


async def synthesize_answer_from_knowledge(message: str, matches: list[dict]) -> str:
    """
    Behind the scenes:
    - takes raw matched knowledge
    - turns it into one simple answer
    - user does NOT see the raw chunks
    """
    if not matches:
        return ""

    try:
        from openai import OpenAI
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # fallback to a simple local summary if OpenAI is unavailable
            best = matches[0]
            content = str(best.get("content", "")).strip()
            return content[:500].strip()

        client = OpenAI(api_key=api_key)

        knowledge_text = "\n\n".join(
            f"Title: {m.get('title','')}\n"
            f"Topic: {m.get('topic','')}\n"
            f"Content: {str(m.get('content',''))[:1500]}"
            for m in matches
        )

        prompt = f"""
User question:
{message}

Internal knowledge:
{knowledge_text}

Instructions:
Answer the user in one direct, simple, natural response.
Do not dump article text.
Do not list sources.
Do not say "based on my knowledge base".
Do not mention internal retrieval.
Just answer like a smart assistant.
Keep it concise but complete.
"""

        result = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": "You are SVANSAI. Answer clearly, naturally, and directly.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        text = (
            result.choices[0].message.content.strip()
            if result and result.choices and result.choices[0].message.content
            else ""
        )

        return text

    except Exception:
        best = matches[0]
        content = str(best.get("content", "")).strip()
        return content[:500].strip()


async def fallback_answer_and_learn(
    message: str, knowledge: list[dict]
) -> tuple[str, str]:
    """
    If knowledge is weak:
    - search behind the scenes
    - return one simple answer
    - save what was learned quietly
    """
    try:
        from knowledge_store import save_knowledge

        search = search_topic(message, 5)

        if not search["ok"] or not search["results"]:
            return (
                "I do not have a strong answer for that yet, but I’ve marked it as something I should learn next.",
                "fallback",
            )

        snippets = [
            r.get("snippet", "") for r in search["results"][:3] if r.get("snippet")
        ]
        urls = [r.get("url", "") for r in search["results"][:3]]
        titles = [r.get("title", "") for r in search["results"][:3]]

        combined = "\n\n".join(snippets).strip()

        # Use AI to turn fallback snippets into one clean answer
        answer = combined
        try:
            from openai import OpenAI
            import os

            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and combined:
                client = OpenAI(api_key=api_key)
                prompt = f"""
User question:
{message}

Search snippets:
{combined}

Instructions:
Give one clean, direct answer.
Do not mention search results.
Do not list sources unless necessary.
Keep it simple and natural.
"""

                result = client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0.3,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are SVANSAI. Answer clearly, naturally, and directly.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                )

                text = (
                    result.choices[0].message.content.strip()
                    if result and result.choices and result.choices[0].message.content
                    else ""
                )

                if text:
                    answer = text

        except Exception:
            pass

        # Quietly learn in the background
        new_entries = []
        for i, snippet in enumerate(snippets):
            new_entries.append(
                {
                    "title": titles[i] if i < len(titles) else message,
                    "topic": message,
                    "content": snippet,
                    "url": urls[i] if i < len(urls) else "",
                    "source": f"fallback_{search.get('source', 'search')}",
                }
            )

        if new_entries:
            knowledge.extend(new_entries)
            save_knowledge(knowledge)

        if not answer.strip():
            answer = "I found related information, but I still need a better learning pass on this topic."

        return answer, search.get("source", "fallback")

    except Exception as error:
        return f"Error processing request: {error}", "error"


# =========================
# CHAT API (HIDDEN LOGIC, CLEAN OUTPUT)
# =========================
@app.post("/api")
async def chat(request: ChatRequest):
    message = request.message.strip()

    try:
        from knowledge_store import load_knowledge

        knowledge = load_knowledge()

        # 1. Search own knowledge first
        matches = find_knowledge_matches(message, knowledge, limit=3)

        # 2. If knowledge exists, synthesize one clean answer behind the scenes
        if matches:
            answer = await synthesize_answer_from_knowledge(message, matches)
            if answer.strip():
                return {
                    "response": answer,
                    "source": "knowledge",
                    "matches": len(matches),
                }

        # 3. If not enough knowledge, fallback silently, then learn it
        answer, source = await fallback_answer_and_learn(message, knowledge)
        return {
            "response": answer,
            "source": source,
            "learned": source != "knowledge",
        }

    except Exception as error:
        return {"response": f"Error processing request: {error}"}


# =========================
# MANUAL LEARNING TRIGGER
# =========================
@app.post("/learning/trigger")
def manual_learn():
    from learning_engine import learn_topics_for_run
    from learning_status import (
        mark_learning_started,
        mark_learning_completed,
    )

    try:
        mark_learning_started()

        result = learn_topics_for_run(search_topic)

        mark_learning_completed(
            topics_attempted=result["topics_attempted"],
            entries_saved=result["entries_saved"],
        )

        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =========================
# DATA & MAINTENANCE ENDPOINTS
# =========================
@app.get("/learning/status")
def learning_status():
    return {"ok": True, "status": load_learning_status()}


@app.get("/learning/data")
def get_learning_data():
    from knowledge_store import load_knowledge

    entries = load_knowledge()
    return {"ok": True, "count": len(entries), "entries": entries[:50]}


@app.post("/learning/backup")
def backup_learning():
    from knowledge_store import load_knowledge
    from github_backup import backup_knowledge_to_github

    data = load_knowledge()
    result = backup_knowledge_to_github(data)
    return {"ok": True, "result": result}


@app.get("/test-search")
def test_search():
    return search_topic("Operating systems overview", 5)
