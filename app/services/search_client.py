from typing import Dict, Any, List
import os

from ddgs import DDGS

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")


def search_topic(topic: str, count: int = 10) -> Dict[str, Any]:

    results: List[Dict[str, Any]] = []

    # --------------------------
    # Brave Search
    # --------------------------

    if BRAVE_API_KEY:

        try:

            import requests

            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": BRAVE_API_KEY,
            }

            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params={"q": topic, "count": count},
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

                return {"ok": True, "results": results, "source": "brave"}

        except Exception as error:
            print("[SVANSAI] Brave failed:", error)

    # --------------------------
    # SERPAPI fallback
    # --------------------------

    if SERPAPI_API_KEY:

        try:

            import requests

            params = {"q": topic, "api_key": SERPAPI_API_KEY}

            response = requests.get(
                "https://serpapi.com/search", params=params, timeout=20
            )

            data = response.json()

            for r in data.get("organic_results", []):

                results.append(
                    {
                        "title": r.get("title"),
                        "url": r.get("link"),
                        "snippet": r.get("snippet"),
                    }
                )

            if results:

                return {"ok": True, "results": results, "source": "serpapi"}

        except Exception as error:
            print("[SVANSAI] SerpAPI failed:", error)

    # --------------------------
    # DDGS fallback
    # --------------------------

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

            return {"ok": True, "results": results, "source": "ddgs"}

    except Exception as error:
        print("[SVANSAI] DDGS failed:", error)

    return {"ok": False, "results": [], "source": "none"}
