"""Shared configuration for Cricket AI Council."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data" / "processed"
RAG_DIR = ROOT_DIR / "rag"

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

CHROMA_PERSIST_DIR = RAG_DIR / "chroma_db"
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "cricket_docs")

DEFAULT_ROLE = "tactical"
MAX_TOOL_CALLS = 10
CONFIDENCE_THRESHOLD = 0.7

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

UI_PORT = int(os.getenv("UI_PORT", "8501"))


def validate_config() -> bool:
    """Validate that required configuration is present."""
    if not GOOGLE_API_KEY:
        print("⚠️  WARNING: GOOGLE_API_KEY not set. LLM calls will fail.")
        print("   Set it via: export GOOGLE_API_KEY='your-key'")
        return False
    return True


class Config:
    """Config class wrapper for compatibility with module imports."""
    GEMINI_MODEL = GEMINI_MODEL
    GOOGLE_API_KEY = GOOGLE_API_KEY
    DATA_DIR = DATA_DIR
    CHROMA_PERSIST_DIR = CHROMA_PERSIST_DIR
    CHROMA_COLLECTION_NAME = CHROMA_COLLECTION_NAME
    DEFAULT_ROLE = DEFAULT_ROLE
    MAX_TOOL_CALLS = MAX_TOOL_CALLS
    CONFIDENCE_THRESHOLD = CONFIDENCE_THRESHOLD
