"""Shared test fixtures for mocking external dependencies."""

import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Mock replicate module before any app imports
# (avoids Pydantic V1 issues on Python 3.14)
mock_replicate = MagicMock()
mock_replicate.run = MagicMock(return_value=iter(["test"]))
sys.modules["replicate"] = mock_replicate

import pytest
from app.models.document import TimestampedSegment

# Set test environment variables before any imports
os.environ["REPLICATE_API_TOKEN"] = "test-token"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["REDIS_URL"] = "redis://localhost:6379"

# Clear settings cache so test env vars are picked up
from app.config import get_settings
get_settings.cache_clear()


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB collection with common async operations."""
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    return mock_collection


@pytest.fixture
def client(mock_mongodb):
    """Create a FastAPI TestClient with all mocks applied."""
    with patch(
        "app.services.vector_store.init_pinecone"
    ), patch(
        "app.routers.upload.vector_store"
    ) as mock_vs_upload, patch(
        "app.routers.upload.documents_collection",
        mock_mongodb,
    ), patch(
        "app.routers.upload.embedding_service"
    ) as mock_emb, patch(
        "app.routers.upload.llm_service"
    ) as mock_llm, patch(
        "app.routers.upload.pdf_service"
    ) as mock_pdf, patch(
        "app.routers.upload.audio_service"
    ) as mock_audio, patch(
        "app.routers.upload.video_service"
    ) as mock_video, patch(
        "app.routers.chat.documents_collection",
        mock_mongodb,
    ), patch(
        "app.routers.chat.embedding_service"
    ) as mock_chat_emb, patch(
        "app.routers.chat.vector_store"
    ) as mock_chat_vs, patch(
        "app.routers.chat.llm_service"
    ) as mock_chat_llm, patch(
        "app.routers.media.documents_collection",
        mock_mongodb,
    ):
        # Configure upload service mocks
        mock_pdf.process_pdf = AsyncMock(
            return_value=("Test PDF text", ["chunk1", "chunk2"])
        )
        test_segment = TimestampedSegment(
            start_time=0.0,
            end_time=5.0,
            text="Test segment",
        )
        mock_audio.transcribe_with_timestamps = AsyncMock(
            return_value=(
                "Test transcript",
                [test_segment],
            )
        )
        mock_video.process_video = AsyncMock(
            return_value=(
                "Test transcript",
                [test_segment],
            )
        )
        mock_emb.get_embeddings_batch = AsyncMock(
            return_value=[[0.1] * 256, [0.2] * 256]
        )
        mock_vs_upload.upsert_chunks = AsyncMock(
            return_value=["chunk_0", "chunk_1"]
        )
        mock_llm.generate_summary = AsyncMock(
            return_value="Test summary"
        )

        # Configure chat service mocks
        mock_chat_emb.get_embedding = AsyncMock(
            return_value=[0.1] * 256
        )
        mock_chat_vs.search = AsyncMock(
            return_value=[
                {
                    "text": "Test context",
                    "score": 0.9,
                    "chunk_index": 0,
                }
            ]
        )
        mock_chat_llm.answer_question = AsyncMock(
            return_value=("Test answer", None)
        )

        from fastapi.testclient import TestClient
        from app.main import app

        yield TestClient(app)
