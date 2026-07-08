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
     "feedback, split into two categories that require DIFFERENT fixes:\n\n"
     "CITATION GAPS: these claims are likely accurate but missing a "
     "source tag. Fix = add an inline citation like [Source Name] right "
     "next to the claim. Do NOT change, soften, or remove the number or "
     "fact itself - it was judged as probably true, just uncited.\n\n"
     "ACCURACY CONCERNS: these claims may be false or unverifiable. Fix = "
     "check the source material provided below. If you find direct "
     "support for the claim, add a citation and keep it. If you find NO "
     "support at all, either remove the claim or rephrase it as a "
     "clearly-hedged statement (e.g. 'some reports suggest...').\n\n"
     "Keep every part of the original report that wasn't flagged in "
     "either list."),
    ("human",
     "Topic: {topic}\n\n"
     "Original report:\n{original_report}\n\n"
     "Source material (use this to verify accuracy_concerns claims):\n"
     "{source_content}\n\n"
     "CITATION GAPS (add citation only, do not change the claim):\n"
     "{citation_gaps}\n\n"
     "ACCURACY CONCERNS (verify against sources above before deciding):\n"
     "{accuracy_concerns}\n\n"
     "Produce the corrected full report.")
])

revision_chain = REVISION_PROMPT | llm | StrOutputParser()


def revise_report(
    topic: str,
    original_report: str,
    citation_gaps: list[str],
    accuracy_concerns: list[str],
    scraped_sources: list[dict],
) -> str:
    """
    Targets the critic's two distinct feedback categories with different
    instructions - citation_gaps get a citation added without touching the
    claim, accuracy_concerns get checked against source text before being
    kept, softened, or removed. This replaces the earlier version that
    treated all feedback as one undifferentiated list, which caused
    correct-but-uncited numbers to get needlessly hedged.
    """
    combined_content = "\n\n---\n\n".join(
        f"Source: {s['url']}\n{s['content']}" for s in scraped_sources
    )

    def format_list(items: list[str]) -> str:
        if not items:
            return "(none)"
        return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))

    return revision_chain.invoke({
        "topic": topic,
        "original_report": original_report,
        "source_content": combined_content,
        "citation_gaps": format_list(citation_gaps),
        "accuracy_concerns": format_list(accuracy_concerns),
    })