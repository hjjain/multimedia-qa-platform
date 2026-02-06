"""Embedding service using OpenAI text-embedding-3-small model."""

from openai import OpenAI
from typing import List
from app.config import get_settings


class EmbeddingService:
    """Generates text embeddings using OpenAI's embedding API."""

    def __init__(self):
        self.client = OpenAI(
            api_key=get_settings().openai_api_key
        )
        self.model = "text-embedding-3-small"

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for a single text.

        Args:
            text: Input text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        response = self.client.embeddings.create(
            model=self.model, input=text
        )
        return response.data[0].embedding

    async def get_embeddings_batch(
        self, texts: List[str]
    ) -> List[List[float]]:
        """Get embeddings for multiple texts in a single API call.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors.
        """
        response = self.client.embeddings.create(
            model=self.model, input=texts
        )
        return [item.embedding for item in response.data]
