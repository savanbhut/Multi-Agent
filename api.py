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
    citation_gaps: list[str]
    accuracy_concerns: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
def research(req: ResearchRequest):
    try:
        result = run_research_pipeline(req.topic, max_sources=req.max_sources)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)