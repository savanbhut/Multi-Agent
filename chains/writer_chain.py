"""
writer_chain.py
Writer Chain - takes research topic + scraped source content,
produces a structured report using LCEL (prompt | llm | parser).
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import llm

WRITER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a research report writer. Write clear, structured, factual "
     "reports based ONLY on the source material provided. Do not invent "
     "facts not present in the sources. If sources conflict, note the "
     "conflict rather than picking one silently."),
    ("human",
     "Topic: {topic}\n\n"
     "Source material (scraped from {num_sources} web pages):\n"
     "{source_content}\n\n"
     "Write a structured report with these sections:\n"
     "1. Executive Summary (2-3 sentences)\n"
     "2. Key Findings (bulleted)\n"
     "3. Detailed Analysis\n"
     "4. Sources Used (list the URLs provided)")
])

writer_chain = WRITER_PROMPT | llm | StrOutputParser()


def generate_report(topic: str, scraped_sources: list[dict]) -> str:
    """
    scraped_sources: list of {"url": ..., "content": ...} from scraper_tool
    """
    combined_content = "\n\n---\n\n".join(
        f"Source: {s['url']}\n{s['content']}" for s in scraped_sources
    )

    return writer_chain.invoke({
        "topic": topic,
        "num_sources": len(scraped_sources),
        "source_content": combined_content,
    })


REVISION_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are revising a research report based on specific editorial "
     "feedback. Fix EACH listed issue directly - do not just rewrite the "
     "whole report from scratch and hope the issues disappear. Keep every "
     "part of the original report that wasn't flagged as an issue."),
    ("human",
     "Topic: {topic}\n\n"
     "Original report:\n{original_report}\n\n"
     "Source material (for re-checking facts):\n{source_content}\n\n"
     "Specific issues to fix:\n{issues}\n\n"
     "Produce the corrected full report.")
])

revision_chain = REVISION_PROMPT | llm | StrOutputParser()


def revise_report(topic: str, original_report: str, issues: list[str], scraped_sources: list[dict]) -> str:
    """
    Unlike calling generate_report() again with a vague note tacked onto
    the topic, this targets the critic's exact numbered issues against the
    existing draft - so you can actually verify the revision addressed
    something specific rather than just re-rolling the dice on a fresh draft.
    """
    combined_content = "\n\n---\n\n".join(
        f"Source: {s['url']}\n{s['content']}" for s in scraped_sources
    )
    numbered_issues = "\n".join(f"{i+1}. {issue}" for i, issue in enumerate(issues))

    return revision_chain.invoke({
        "topic": topic,
        "original_report": original_report,
        "source_content": combined_content,
        "issues": numbered_issues,
    })