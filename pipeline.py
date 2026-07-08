"""
pipeline.py
Orchestrates the full multi-agent flow:
  Search Agent -> Reader Agent -> Writer Chain -> Critic Chain
                                       ^________________|
                                    (revises once if critic scores it low)

Rate limiting note: your Mistral account is capped at 1 request/second
(check admin.mistral.ai/plateforme/limits). Writer + Critic + possible
revision = up to 3 LLM calls per run. time.sleep(1.1) between calls is
the honest fix for a hard rate limit.
"""

import time
from tools.search_tool import search_web
from tools.scraper_tool import scrape_multiple
from chains.writer_chain import generate_report, revise_report
from chains.critic_chain import critique_report

RATE_LIMIT_DELAY = 1.1  # seconds between LLM calls


def run_research_pipeline(topic: str, max_sources: int = 5) -> dict:
    print(f"[1/4] Searching for: {topic}")
    search_results = search_web(topic, max_results=max_sources)
    if not search_results:
        raise RuntimeError("Search Agent returned zero results - check TAVILY_API_KEY and query.")

    urls = [r["url"] for r in search_results]

    print(f"[2/4] Scraping {len(urls)} URLs")
    scraped = scrape_multiple(urls)
    if not scraped:
        raise RuntimeError("Reader Agent could not extract content from any URL - all scrapes failed.")

    print(f"[3/4] Writing report from {len(scraped)} usable sources")
    report = generate_report(topic, scraped)
    time.sleep(RATE_LIMIT_DELAY)

    print("[4/4] Critiquing report")
    critique = critique_report(topic, report)
    time.sleep(RATE_LIMIT_DELAY)

    score_before = critique.score
    score_after = None

    if critique.needs_revision:
        print(f"[revision] Critic scored it {score_before}/10")
        print(f"    Citation gaps ({len(critique.citation_gaps)}):")
        for issue in critique.citation_gaps:
            print(f"      - {issue}")
        print(f"    Accuracy concerns ({len(critique.accuracy_concerns)}):")
        for issue in critique.accuracy_concerns:
            print(f"      - {issue}")

        report = revise_report(
            topic, report,
            critique.citation_gaps,
            critique.accuracy_concerns,
            scraped,
        )
        time.sleep(RATE_LIMIT_DELAY)

        critique = critique_report(topic, report)
        score_after = critique.score
        time.sleep(RATE_LIMIT_DELAY)

        if score_after > score_before:
            print(f"[revision] Improved: {score_before}/10 -> {score_after}/10")
        elif score_after == score_before:
            print(f"[revision] No measurable change: stayed at {score_after}/10")
        else:
            print(f"[revision] Got WORSE: {score_before}/10 -> {score_after}/10 - investigate")

    return {
        "topic": topic,
        "sources": [s["url"] for s in scraped],
        "report": report,
        "score_before_revision": score_before,
        "score_after_revision": score_after,
        "score": critique.score,
        "strengths": critique.strengths,
        "citation_gaps": critique.citation_gaps,
        "accuracy_concerns": critique.accuracy_concerns,
    }


if __name__ == "__main__":
    result = run_research_pipeline("current state of multi-agent AI systems in 2026")
    print("\n" + "=" * 60)
    print(result["report"])
    print("=" * 60)
    print(f"Critic score: {result['score']}/10")