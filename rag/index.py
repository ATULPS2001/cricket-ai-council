"""Index cricket documents into Chroma for RAG."""
from __future__ import annotations

import json
from pathlib import Path

import chromadb
from chromadb.config import Settings

# ─── Config ───────────────────────────────────────────────────────────────────

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "cricket_docs"
DOCS_DIR = Path(__file__).parent.parent / "data" / "json_scorecards"


# ─── Index ────────────────────────────────────────────────────────────────────


def index_json_scorecards():
    """Index JSON scorecard files into Chroma."""
    # Initialize client
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Create or get collection
    try:
        collection = client.create_collection(COLLECTION_NAME)
    except Exception:
        collection = client.get_collection(COLLECTION_NAME)

    # Find JSON files
    if not DOCS_DIR.exists():
        print(f"Docs directory not found: {DOCS_DIR}")
        return

    json_files = list(DOCS_DIR.glob("*.json"))
    print(f"Found {len(json_files)} JSON files to index")

    # Index each file
    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                data = json.load(f)

            # Extract text (simplified - adjust based on your JSON structure)
            # Assuming JSON has: match_id, teams, venue, innings, scores
            match_id = data.get("match_id", json_file.stem)
            teams = data.get("teams", [])
            venue = data.get("venue", "")
            
            # Create document text
            doc_text = f"Match {match_id}: {' vs '.join(teams)} at {venue}"
            
            # Add innings summaries
            innings = data.get("innings", [])
            for inn in innings:
                batting = inn.get("batting_team", "")
                runs = inn.get("total_runs", 0)
                wickets = inn.get("wickets", 0)
                doc_text += f" | {batting}: {runs}/{wickets}"

            # Store in Chroma
            collection.add(
                documents=[doc_text],
                metadatas=[{"source": json_file.name, "match_id": match_id}],
                ids=[f"match_{match_id}"],
            )

            print(f"Indexed: {json_file.name}")

        except Exception as e:
            print(f"Error indexing {json_file.name}: {e}")

    print(f"Indexing complete. Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    index_json_scorecards()
