"""Local embedding service using hash-based vector generation."""

import hashlib
import math
from typing import List


class EmbeddingService:
    """Generates text embeddings locally using deterministic
    hash-based vectors. No external API needed."""

    DIMENSIONS = 256

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for a single text."""
        return self._hash_embedding(text)

    async def get_embeddings_batch(
        self, texts: List[str]
    ) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        return [self._hash_embedding(t) for t in texts]

    def _hash_embedding(self, text: str) -> List[float]:
        """Create a deterministic embedding from text.

        Uses word-level hashing to build a fixed-size vector.
        Words that appear in both query and document produce
        similar vectors via cosine similarity.
        """
        words = text.lower().split()
        vec = [0.0] * self.DIMENSIONS

        for word in words:
            h = int(
                hashlib.md5(word.encode()).hexdigest(), 16
            )
            for j in range(self.DIMENSIONS):
                vec[j] += math.sin(h * (j + 1))

        # Normalize to unit vector
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
