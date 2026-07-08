"""
config.py
Loads environment variables and creates one shared LLM instance
that every agent/chain in the pipeline imports.
"""

import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not MISTRAL_API_KEY:
    raise ValueError(
        "MISTRAL_API_KEY not found. Check that .env exists in the project root "
        "and that load_dotenv() can see it (run scripts from the project root)."
    )

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in .env")

llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0.3,
    api_key=MISTRAL_API_KEY,
    max_retries=2,
    max_tokens=4096,       # raised from default - structured critic output
                           # (score + strengths + two issue lists) can run
                           # long, and truncation mid-JSON causes required
                           # fields declared late in the schema to go
                           # missing entirely (seen firsthand: needs_revision
                           # got cut off on a thin-content topic).
)