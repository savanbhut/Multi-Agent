"""
scraper_tool.py
Reader Agent - fetches a URL and extracts readable text content.
This is the part most tutorials underweight: real websites throw
timeouts, 403s, and cookie walls constantly. This handles those
cases explicitly instead of crashing the whole pipeline on one bad URL.
"""

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# Tags that are never useful content - stripped before extracting text
NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "form"]


def scrape_url(url: str, timeout: int = 10, max_chars: int = 4000) -> str:
    """
    Fetches a URL and returns cleaned, truncated text.
    Returns an empty string on failure instead of raising - one dead
    link should not kill the whole research pipeline.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[scraper] failed to fetch {url}: {e}")
        return ""

    soup = BeautifulSoup(resp.content, "lxml")

    for tag in soup(NOISE_TAGS):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # collapse repeated whitespace that get_text tends to leave behind
    text = " ".join(text.split())

    return text[:max_chars]


def scrape_multiple(urls: list[str]) -> list[dict]:
    """Scrapes a list of URLs, skipping any that fail silently (logged, not raised)."""
    results = []
    for url in urls:
        content = scrape_url(url)
        if content:  # skip empty/failed scrapes rather than passing junk downstream
            results.append({"url": url, "content": content})
    return results


if __name__ == "__main__":
    print(scrape_url("https://en.wikipedia.org/wiki/Multi-agent_system")[:500])
