from typing import Dict, Any, List
import os

from ddgs import DDGS

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")


def search_topic(topic: str, count: int = 10) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []

    # Try Brave first
    if BRAVE_API_KEY:
        try:
            import requests

            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": BRAVE_API_KEY,
            }

            trusted_query = f"{topic} site:developer.mozilla.org OR site:docs.python.org OR site:react.dev OR site:nextjs.org OR site:fastapi.tiangolo.com OR site:learn.microsoft.com OR site:ibm.com OR site:techtarget.com OR site:wikipedia.org"
            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params={"q": trusted_query, "count": count},
                timeout=20,
            )

            data = response.json()

            for r in data.get("web", {}).get("results", []):
                results.append(
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "snippet": r.get("description"),
                    }
                )

            if results:
                return {
                    "ok": True,
                    "results": results,
                    "source": "brave",
                }

        except Exception as error:
            print("[SVANSAI Search] Brave failed:", error)

    # Fallback to DDGS
    try:
        with DDGS() as ddgs:
            search_results = ddgs.text(topic, max_results=count)

            for r in search_results:
                results.append(
                    {
                        "title": r.get("title"),
                        "url": r.get("href"),
                        "snippet": r.get("body"),
                    }
                )

        if results:
            return {
                "ok": True,
                "results": results,
                "source": "ddgs",
            }

    except Exception as error:
        print("[SVANSAI Search] DDGS failed:", error)

    return {
        "ok": False,
        "results": [],
        "source": "none",
    }
