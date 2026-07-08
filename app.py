"""
api.py
FastAPI backend - wraps the existing multi-agent pipeline as an HTTP API
for the React frontend to call.

Run with: uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from pipeline import run_research_pipeline

app = FastAPI(title="Multi-Agent Research API")

# React dev server runs on localhost:5173 by default (Vite). Without this,
# the browser blocks every request from React to this API with a CORS
# error - not a bug in your code, just the browser enforcing same-origin
# rules between two different ports.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=3, description="Research topic to investigate")
    max_sources: int = Field(default=5, ge=3, le=8)


class ResearchResponse(BaseModel):
    topic: str
    sources: list[str]
    report: str
    score_before_revision: int
    score_after_revision: Optional[int]
    score: int
    strengths: str
    specific_issues: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
def research(req: ResearchRequest):
    """
    Runs the full pipeline synchronously. This request will hang for
    20-40 seconds because of Mistral's 1 req/sec rate limit plus scraping
    time - the React side needs a loading state that accounts for this,
    not a spinner tuned for a 2-second API call.
    """
    try:
        result = run_research_pipeline(req.topic, max_sources=req.max_sources)
    except RuntimeError as e:
        # search returned nothing, or all scrapes failed - user-facing,
        # not a server bug
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # anything else (API key issues, Mistral errors, etc.) - don't
        # leak raw exception internals to the client, but don't swallow
        # it either
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)