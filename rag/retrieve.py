"""RAG Retrieval - Query Chroma for relevant documents."""
import sys
from pathlib import Path
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

collection = client.get_collection(name=CHROMA_COLLECTION_NAME)


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    query_embedding = embedding_model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    retrieved = []
    if results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            retrieved.append({
                "document": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

    return retrieved


def format_for_prompt(retrieved_docs: list[dict]) -> str:
    if not retrieved_docs:
        return "No relevant documents found."

    formatted = []
    for doc in retrieved_docs:
        source = doc["metadata"].get("source", "unknown")
        formatted.append(f"[source: {source}]\n{doc['document'][:500]}...")

    return "\n\n".join(formatted)


if __name__ == "__main__":
    test_query = "CSK at Chepauk home record"
    print(f"Query: {test_query}")
    print("="*50)

    results = retrieve(test_query, top_k=3)

    for i, doc in enumerate(results, 1):
        print(f"\n{i}. Source: {doc['metadata'].get('source', 'unknown')}")
        print(f"   Distance: {doc['distance']:.4f}")
        print(f"   Content: {doc['document'][:200]}...")
