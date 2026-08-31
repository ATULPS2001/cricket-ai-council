"""RAG retrieval for Cricket AI Council."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

# ─── Config ───────────────────────────────────────────────────────────────────

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "cricket_docs"


# ─── Retrieve ─────────────────────────────────────────────────────────────────


def retrieve_docs(query: str, n_results: int = 2) -> list[str]:
    """
    Retrieve top-N documents for a query.
    
    Args:
        query: User query
        n_results: Number of docs to retrieve
    
    Returns:
        List of document texts
    """
    # Check if DB exists
    if not CHROMA_DIR.exists():
        return []

    try:
        # Initialize client
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(COLLECTION_NAME)

        # Query
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas"],
        )

        # Extract documents
        docs = results["documents"][0] if results["documents"] else []
        
        # Format with metadata
        formatted = []
        for i, doc in enumerate(docs):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            source = metadata.get("source", "unknown")
            formatted.append(f"[Source: {source}] {doc}")

        return formatted

    except Exception as e:
        print(f"RAG retrieval error: {e}")
        return []


if __name__ == "__main__":
    # Test
    docs = retrieve_docs("CSK Chepauk home record")
    print(f"Retrieved {len(docs)} docs:")
    for doc in docs:
        print(doc)
