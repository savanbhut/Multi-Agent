"""
critic_chain.py
Critic Chain - reviews the Writer's report and returns a structured
score + feedback. Uses Pydantic + with_structured_output so you get
a real object back (score: int, feedback: str) instead of parsing
free-form text yourself, which is the fragile way most tutorials do it.
"""

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from config import llm


class CritiqueResult(BaseModel):
    score: int = Field(description="Quality score from 1-10")
    strengths: str = Field(description="What the report does well")
    # A flat string like "unclear structure, weak sourcing" gives the writer
    # nothing concrete to act on. A numbered list of specific issues is what
    # actually lets a revision pass fix particular sentences/sections instead
    # of just regenerating the same report with a vague nudge.
    specific_issues: list[str] = Field(
        description=(
            "3-6 specific, actionable issues, each naming the exact section "
            "or claim affected. Bad: 'sourcing is weak'. Good: 'Key Finding "
            "#3 cites an 80% statistic with no source URL attached - add "
            "attribution or remove the claim.'"
        )
    )
    needs_revision: bool = Field(description="True if score < 7 and should be rewritten")


CRITIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a strict editorial critic reviewing AI-generated research "
     "reports. Check for: factual grounding in the provided sources, "
     "clarity, structure, and whether claims are actually supported by "
     "the source material rather than fabricated. Be genuinely critical - "
     "a mediocre report should score below 7, not 8. Every issue you list "
     "must be specific enough that a writer could fix it without asking "
     "you what you meant."),
    ("human",
     "Original topic: {topic}\n\n"
     "Report to review:\n{report}\n\n"
     "Evaluate it.")
])

# structured_output forces the model's response into the CritiqueResult
# schema - this fails loudly if the model doesn't comply, which is better
# than silently getting malformed JSON back.
critic_chain = CRITIC_PROMPT | llm.with_structured_output(CritiqueResult)


def critique_report(topic: str, report: str) -> CritiqueResult:
    return critic_chain.invoke({"topic": topic, "report": report})

def critique_report(topic: str, report: str) -> CritiqueResult:
    result = critic_chain.invoke({"topic": topic, "report": report})

    # Defensive check: Mistral doesn't always cleanly separate issues into
    # distinct list items - sometimes it dumps one giant blob with nested
    # numbering and stray formatting artifacts (seen this happen once
    # already, non-deterministically, same code). Catch it instead of
    # trusting it silently.
    clean_issues = []
    for issue in result.specific_issues:
        if len(issue) > 300 or any(c in issue for c in ["{", "}", "```"]):
            print(f"[warning] malformed critic issue detected, truncating: {issue[:80]}...")
            clean_issues.append(issue[:150])
        else:
            clean_issues.append(issue)
    result.specific_issues = clean_issues

    return result