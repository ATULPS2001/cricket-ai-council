"""RAG Indexing Script - Index cricket documents into Chroma."""
import sys
from pathlib import Path
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(
    path=str(CHROMA_PERSIST_DIR),
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


def index_json_scorecards(json_dir: Path):
    if not json_dir.exists():
        print(f"⚠️  JSON directory not found: {json_dir}")
        return

    json_files = list(json_dir.glob("*.json"))
    print(f"Found {len(json_files)} JSON files to index...")

    documents = []
    metadatas = []
    ids = []

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            text_content = json.dumps(data, indent=2)[:4000]

            metadata = {
                "source": json_file.name,
                "source_type": "scorecard",
                "file_path": str(json_file)
            }

            documents.append(text_content)
            metadatas.append(metadata)
            ids.append(f"scorecard_{json_file.stem}")

        except Exception as e:
            print(f"⚠️  Error indexing {json_file.name}: {e}")

    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✅ Indexed {len(documents)} documents into Chroma")
    else:
        print("⚠️  No documents to index")


def index_csv_matches(csv_path: Path):
    if not csv_path.exists():
        print(f"⚠️  CSV not found: {csv_path}")
        return

    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read()[:10000]

    collection.add(
        documents=[content],
        metadatas=[{"source": csv_path.name, "source_type": "matches_csv"}],
        ids=["matches_csv"]
    )
    print(f"✅ Indexed matches CSV")


if __name__ == "__main__":
    print("🏏 Cricket AI Council - RAG Indexing")
    print("="*50)

    json_dir = ROOT / "data" / "json"
    index_json_scorecards(json_dir)

    matches_csv = ROOT / "data" / "processed" / "matches.csv"
    index_csv_matches(matches_csv)

    print("="*50)
    print(f"Collection: {collection.name}")
    print(f"Total documents: {collection.count()}")
    print(f"Persist directory: {CHROMA_PERSIST_DIR}")
