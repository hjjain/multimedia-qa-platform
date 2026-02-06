"""Vector store service using Pinecone for semantic search."""

from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any
from app.config import get_settings

settings = get_settings()
pc = None
index = None


def init_pinecone():
    """Initialize the Pinecone client and create index if needed."""
    global pc, index
    pc = Pinecone(api_key=settings.pinecone_api_key)

    # Create index if it does not exist
    if settings.pinecone_index_name not in pc.list_indexes().names():
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=1536,  # text-embedding-3-small dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws", region="us-east-1"
            ),
        )

    index = pc.Index(settings.pinecone_index_name)


class VectorStore:
    """Manages document chunk storage and retrieval in Pinecone."""

    def __init__(self):
        self.index = index

    async def upsert_chunks(
        self,
        document_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> List[str]:
        """Store document chunks with their embeddings.

        Args:
            document_id: Unique document identifier.
            chunks: List of text chunks.
            embeddings: Corresponding embedding vectors.

        Returns:
            List of chunk IDs stored in Pinecone.
        """
        chunk_ids = []
        vectors = []

        for i, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            chunk_id = f"{document_id}_{i}"
            chunk_ids.append(chunk_id)
            vectors.append(
                {
                    "id": chunk_id,
                    "values": embedding,
                    "metadata": {
                        "document_id": document_id,
                        "chunk_index": i,
                        "text": chunk[:1000],
                    },
                }
            )

        # Upsert in batches of 100
        for i in range(0, len(vectors), 100):
            batch = vectors[i : i + 100]
            self.index.upsert(vectors=batch)

        return chunk_ids

    async def search(
        self,
        query_embedding: List[float],
        document_id: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for relevant chunks using vector similarity.

        Args:
            query_embedding: Query vector.
            document_id: Filter results to this document.
            top_k: Number of results to return.

        Returns:
            List of matching chunks with text, score, and index.
        """
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter={"document_id": {"$eq": document_id}},
        )

        return [
            {
                "text": match.metadata.get("text", ""),
                "score": match.score,
                "chunk_index": match.metadata.get("chunk_index"),
            }
            for match in results.matches
        ]

    async def delete_document(self, document_id: str):
        """Delete all chunks for a document from Pinecone."""
        self.index.delete(
            filter={"document_id": {"$eq": document_id}}
        )
