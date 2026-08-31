"""Shared configuration for Cricket AI Council."""
import os
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data" / "processed"
CHROMA_DIR = ROOT_DIR / "data" / "chroma_db"

# ─── API Keys ─────────────────────────────────────────────────────────────────

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ─── LLM Config ───────────────────────────────────────────────────────────────

LLM_MODEL = "gemini-2.0-flash"
LLM_TEMPERATURE = 0.7

# ─── RAG Config ───────────────────────────────────────────────────────────────

RAG_N_RESULTS = 2
RAG_COLLECTION_NAME = "cricket_docs"

# ─── Workflow Config ──────────────────────────────────────────────────────────

WORKFLOW_TIMEOUT = 60  # seconds
MAX_TOOL_CALLS = 5

# ─── Guardrails ───────────────────────────────────────────────────────────────

CONFIDENCE_THRESHOLD = 0.7
ESCALATE_ON_LOW_CONFIDENCE = True
