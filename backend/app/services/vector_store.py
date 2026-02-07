"""In-memory vector store with cosine similarity search."""

import math
from typing import List, Dict, Any

# In-memory document store: {doc_id: [entry, ...]}
_store: Dict[str, List[dict]] = {}


def init_pinecone():
    """Initialize vector store (in-memory, no external service)."""
    print("Vector store initialized (in-memory mode).")


def _cosine_similarity(
    a: List[float], b: List[float]
) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (norm_a * norm_b)


class VectorStore:
    """In-memory vector store for document chunk retrieval.

    Stores embeddings and performs cosine similarity search.
    In production, swap for Pinecone/FAISS.
    """

    async def upsert_chunks(
        self,
        document_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> List[str]:
        """Store document chunks with embeddings."""
        chunk_ids = []
        entries = []

        for i, (chunk, emb) in enumerate(
            zip(chunks, embeddings)
        ):
            chunk_id = f"{document_id}_{i}"
            chunk_ids.append(chunk_id)
            entries.append(
                {
                    "id": chunk_id,
                    "values": emb,
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk[:1000],
                }
            )

        _store[document_id] = entries
        return chunk_ids

    async def search(
        self,
        query_embedding: List[float],
        document_id: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for relevant chunks by cosine similarity."""
        entries = _store.get(document_id, [])
        scored = []

        for entry in entries:
            score = _cosine_similarity(
                query_embedding, entry["values"]
            )
            scored.append(
                {
                    "text": entry["text"],
                    "score": score,
                    "chunk_index": entry["chunk_index"],
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    async def delete_document(self, document_id: str):
        """Delete all chunks for a document."""
        _store.pop(document_id, None)
