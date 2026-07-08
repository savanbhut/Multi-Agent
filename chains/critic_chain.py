"""
critic_chain.py
Critic Chain - reviews the Writer's report and returns a structured
score + feedback, split into two distinct categories so the revision
step knows exactly what kind of fix each issue needs:

- citation_gaps: the claim is likely TRUE but has no source tag attached.
  Fix = add a citation, do NOT change the number/claim itself.
- accuracy_concerns: the claim may be FALSE, exaggerated, or not
  traceable to any provided source at all. Fix = verify against source
  text first, then correct or remove if unverifiable.

Before this split, both categories were dumped into one "weaknesses"
field, which caused the writer to hedge/soften numbers that were
actually correct and just needed attribution (confirmed via manual
spot-check against source URLs - see README "Known limitations").
"""

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from config import llm


class CritiqueResult(BaseModel):
    score: int = Field(description="Quality score from 1-10")
    needs_revision: bool = Field(description="True if score < 7 and should be rewritten")
    strengths: str = Field(description="What the report does well")

    citation_gaps: list[str] = Field(
        default_factory=list,
        description=(
            "Claims that are plausible/likely accurate but have no source "
            "tag attached in the report text. Each item should name the "
            "exact claim and which section it's in. Do NOT include claims "
            "you suspect are actually false here - those go in "
            "accuracy_concerns instead."
        )
    )

    accuracy_concerns: list[str] = Field(
        default_factory=list,
        description=(
            "Claims that may be false, fabricated, exaggerated, or not "
            "traceable to ANY of the provided sources even in principle. "
            "Each item should name the exact claim, which section it's in, "
            "and why it seems unverifiable or implausible."
        )
    )
    needs_revision: bool = Field(description="True if score < 7 and should be rewritten")


CRITIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a strict editorial critic reviewing AI-generated research "
     "reports. Check for: factual grounding in the provided sources, "
     "clarity, structure, and whether claims are supported. Be genuinely "
     "critical - a mediocre report should score below 7, not 8.\n\n"
     "CRITICAL: distinguish between two different problems:\n"
     "1. citation_gaps - the claim is probably true, just missing a "
     "source tag. Do not treat these as accuracy problems.\n"
     "2. accuracy_concerns - the claim itself is suspect (fabricated, "
     "exaggerated, contradicts the sources, or has no plausible source "
     "at all).\n"
     "Putting a true-but-uncited claim into accuracy_concerns is a "
     "mistake - it causes the writer to needlessly weaken correct "
     "numbers instead of just adding a citation."),
    ("human",
     "Original topic: {topic}\n\n"
     "Report to review:\n{report}\n\n"
     "Evaluate it.")
])

critic_chain = CRITIC_PROMPT | llm.with_structured_output(CritiqueResult)


def critique_report(topic: str, report: str) -> CritiqueResult:
    result = critic_chain.invoke({"topic": topic, "report": report})

    # with_structured_output can silently return None if the model's
    # response didn't map to a valid tool call at all (different failure
    # mode than truncation - this is the model not calling the schema in
    # the first place, seen on short/generic topics like "what is llm").
    # Retry once before failing loudly, since this is often a one-off.
    if result is None:
        print("[warning] critic returned no structured output, retrying once")
        result = critic_chain.invoke({"topic": topic, "report": report})

    if result is None:
        raise RuntimeError(
            "Critic Chain failed to produce structured output twice in a row. "
            "This usually means the topic/report combination is too thin or "
            "ambiguous for the model to evaluate - try a more specific topic."
        )

    def clean(items: list[str]) -> list[str]:
        cleaned = []
        for item in items:
            if len(item) > 300 or any(c in item for c in ["{", "}", "```"]):
                print(f"[warning] malformed critic issue detected, truncating: {item[:80]}...")
                cleaned.append(item[:150])
            else:
                cleaned.append(item)
        return cleaned

    result.citation_gaps = clean(result.citation_gaps)
    result.accuracy_concerns = clean(result.accuracy_concerns)

    return result
    