# Multi-Agent AI Research System

An automated research pipeline where specialized agents collaborate to search, read, write, and critique a research report on any topic — built to understand real multi-agent orchestration, not just single-prompt LLM calls.

## Architecture
Search Agent  ->  Reader Agent  ->  Writer Chain  ->  Critic Chain
(Tavily)      (BeautifulSoup)     (Mistral LLM)     (Mistral LLM)
________________
(revises once if critic scores < 7/10)
1. **Search Agent** (`tools/search_tool.py`) — queries Tavily for live web results on the given topic.
2. **Reader Agent** (`tools/scraper_tool.py`) — fetches and cleans text content from each result URL. Fails gracefully per-URL (one dead link doesn't kill the run).
3. **Writer Chain** (`chains/writer_chain.py`) — an LCEL chain (`prompt | llm | parser`) that turns scraped source content into a structured report (Executive Summary, Key Findings, Detailed Analysis, Sources).
4. **Critic Chain** (`chains/critic_chain.py`) — reviews the report using structured output (Pydantic), returning a score (1-10) and specific, actionable issues rather than a vague paragraph.
5. **Revision loop** — if the critic scores below 7, the Writer revises the report targeting the critic's exact listed issues, then gets re-scored. Runs once (not an unbounded loop, to protect API quota).

## Stack

- **LLM**: Mistral (`mistral-large-latest`) via `langchain-mistralai`
- **Search**: Tavily
- **Scraping**: `requests` + `BeautifulSoup4`
- **Backend**: FastAPI, exposing the pipeline as a `/research` endpoint
- **Frontend**: React (Vite) + `react-markdown` for report rendering

## Why Mistral instead of OpenAI

Built specifically against Mistral's API, including handling its stricter rate limit (1 request/second on the dev tier) with explicit throttling between LLM calls in the pipeline — a detail that matters here since Writer + Critic + a possible revision pass means up to 3 sequential LLM calls per run.

## Why FastAPI instead of Flask

Reuses the same Pydantic models (`CritiqueResult`) as both the LangChain structured-output schema *and* the API response schema, with no manual serialization step in between. Also chosen for async-readiness, since the current scraping step runs sequentially and is a natural candidate for concurrency later.

## Setup

```bash
uv venv
.venv\Scripts\Activate.ps1        # Windows
uv pip install -r requirements.txt

cd frontend
npm install
```

Create a `.env` in the project root (see `.env.example`):

## Running

**Backend:**
```bash
uvicorn api:app --reload --port 8000
```

**Frontend** (separate terminal):
```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

**Or run the pipeline directly without any UI**, useful for testing:
```bash
python pipeline.py
```

## Known limitations (honest, not hidden)

- **The critic conflates "unsupported" with "false."** Testing showed the critic sometimes flags claims as needing to be softened when they were actually accurate but just missing an inline citation. A real fix (splitting critic feedback into `citation_gaps` vs `accuracy_concerns`) is in progress — see the schema in `chains/critic_chain.py`.
- **No fact-verification against source text.** The critic evaluates structure, clarity, and plausibility — not literal grounding of every number against the scraped source content. Spot-checking output against source URLs is still manual.
- **No caching.** Re-running the same topic re-searches and re-scrapes from scratch every time, which costs API quota unnecessarily.
- **No real streaming progress.** The frontend's loading stages are a fixed timer, not driven by actual backend pipeline events.
- **Single-topic testing.** The pipeline has been verified end-to-end on a handful of topics, not stress-tested across edge cases (thin source coverage, conflicting sources, non-English content, etc.).

## Project structure
Multi_agent/
├── config.py              # Loads env vars, sets up shared Mistral LLM instance
├── pipeline.py             # Orchestrates the full agent pipeline
├── api.py                  # FastAPI backend
├── tools/
│   ├── search_tool.py       # Search Agent (Tavily)
│   └── scraper_tool.py      # Reader Agent (BeautifulSoup)
├── chains/
│   ├── writer_chain.py      # Writer Chain + revision chain
│   └── critic_chain.py      # Critic Chain (structured output scoring)
└── frontend/                # React (Vite) UI
└── src/
├── App.jsx
├── api.js
└── App.css
