"""
search_tool.py
Search Agent - retrieves live web results for a query using Tavily.
Returns a list of {title, url, content_snippet} dicts.
"""

from tavily import TavilyClient
from config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Runs a Tavily search and returns normalized results.
    Raises the underlying exception on failure - the caller decides
    whether to retry or abort, rather than silently swallowing errors.
    """
    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",  # "basic" is faster but noticeably shallower
    )

    results = []
    for r in response.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content_snippet": r.get("content", ""),
        })
    return results


if __name__ == "__main__":
    # quick manual test - run `python tools/search_tool.py` from project root
    for item in search_web("latest advancements in multi-agent AI systems"):
        print(item["title"], "-", item["url"])
