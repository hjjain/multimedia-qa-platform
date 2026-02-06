"""Shared test fixtures for mocking external dependencies."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Set test environment variables before any imports
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["PINECONE_API_KEY"] = "test-key"
os.environ["PINECONE_ENVIRONMENT"] = "us-east-1"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["REDIS_URL"] = "redis://localhost:6379"


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB collection with common async operations."""
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    return mock_collection


@pytest.fixture
def mock_pinecone_index():
    """Mock Pinecone index for vector operations."""
    mock_index = MagicMock()
    mock_index.upsert = MagicMock()
    mock_index.query = MagicMock(
        return_value=MagicMock(matches=[])
    )
    mock_index.delete = MagicMock()
    return mock_index


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client with embeddings, chat, and transcription."""
    client = MagicMock()

    # Mock embeddings
    embedding_response = MagicMock()
    embedding_data = MagicMock(embedding=[0.1] * 1536)
    embedding_response.data = [embedding_data]
    client.embeddings.create.return_value = embedding_response

    # Mock chat completions
    chat_response = MagicMock()
    chat_message = MagicMock(content="Test response")
    chat_choice = MagicMock(message=chat_message)
    chat_response.choices = [chat_choice]
    client.chat.completions.create.return_value = chat_response

    # Mock transcriptions
    transcription_response = MagicMock()
    transcription_response.text = "Test transcript"
    transcription_response.segments = [
        {"start": 0.0, "end": 5.0, "text": "Test segment one"},
        {"start": 5.0, "end": 10.0, "text": "Test segment two"},
    ]
    client.audio.transcriptions.create.return_value = (
        transcription_response
    )

    return client


@pytest.fixture
def client(mock_mongodb, mock_pinecone_index, mock_openai_client):
    """Create a FastAPI TestClient with all mocks applied."""
    with patch(
        "app.services.vector_store.init_pinecone"
    ), patch(
        "app.services.vector_store.index",
        mock_pinecone_index,
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
        mock_audio.transcribe_with_timestamps = AsyncMock(
            return_value=(
                "Test transcript",
                [
                    MagicMock(
                        text="Test segment",
                        start_time=0.0,
                        end_time=5.0,
                        model_dump=MagicMock(
                            return_value={
                                "start_time": 0.0,
                                "end_time": 5.0,
                                "text": "Test segment",
                            }
                        ),
                    )
                ],
            )
        )
        mock_video.process_video = AsyncMock(
            return_value=(
                "Test transcript",
                [
                    MagicMock(
                        text="Test segment",
                        start_time=0.0,
                        end_time=5.0,
                        model_dump=MagicMock(
                            return_value={
                                "start_time": 0.0,
                                "end_time": 5.0,
                                "text": "Test segment",
                            }
                        ),
                    )
                ],
            )
        )
        mock_emb.get_embeddings_batch = AsyncMock(
            return_value=[[0.1] * 1536, [0.2] * 1536]
        )
        mock_vs_upload.upsert_chunks = AsyncMock(
            return_value=["chunk_0", "chunk_1"]
        )
        mock_llm.generate_summary = AsyncMock(
            return_value="Test summary"
        )

        # Configure chat service mocks
        mock_chat_emb.get_embedding = AsyncMock(
            return_value=[0.1] * 1536
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
