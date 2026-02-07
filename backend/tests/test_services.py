"""Tests for backend services (PDF, embedding, LLM, vector store)."""

import pytest
import math
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.pdf_service import PDFService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore, _store
from app.models.document import TimestampedSegment
from app.models.chat import ChatMessage
from app.utils.helpers import (
    get_file_extension,
    format_timestamp,
    ensure_upload_dir,
)


class TestPDFService:
    """Tests for PDF text extraction and chunking."""

    @pytest.mark.asyncio
    async def test_extract_text(self):
        service = PDFService()
        with patch(
            "app.services.pdf_service.PdfReader"
        ) as mock_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = (
                "Test content from page"
            )
            mock_reader.return_value.pages = [mock_page]
            text = await service.extract_text(b"%PDF-1.4")
            assert text == "Test content from page"

    @pytest.mark.asyncio
    async def test_extract_text_multiple_pages(self):
        service = PDFService()
        with patch(
            "app.services.pdf_service.PdfReader"
        ) as mock_reader:
            page1 = MagicMock()
            page1.extract_text.return_value = "Page 1"
            page2 = MagicMock()
            page2.extract_text.return_value = " Page 2"
            mock_reader.return_value.pages = [page1, page2]
            text = await service.extract_text(b"%PDF-1.4")
            assert text == "Page 1 Page 2"

    @pytest.mark.asyncio
    async def test_extract_text_empty_page(self):
        service = PDFService()
        with patch(
            "app.services.pdf_service.PdfReader"
        ) as mock_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = None
            mock_reader.return_value.pages = [mock_page]
            text = await service.extract_text(b"%PDF-1.4")
            assert text == ""

    @pytest.mark.asyncio
    async def test_chunk_text(self):
        service = PDFService()
        text = "This is a test sentence. " * 100
        chunks = await service.chunk_text(text)
        assert len(chunks) > 0
        assert all(len(c) <= 1000 for c in chunks)

    @pytest.mark.asyncio
    async def test_process_pdf(self):
        service = PDFService()
        with patch(
            "app.services.pdf_service.PdfReader"
        ) as mock_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = (
                "Test content " * 50
            )
            mock_reader.return_value.pages = [mock_page]
            text, chunks = await service.process_pdf(
                b"%PDF-1.4"
            )
            assert "Test content" in text
            assert len(chunks) > 0


class TestEmbeddingService:
    """Tests for local hash-based embeddings."""

    @pytest.mark.asyncio
    async def test_get_embedding(self):
        service = EmbeddingService()
        emb = await service.get_embedding("Hello world")
        assert len(emb) == 256
        assert isinstance(emb[0], float)

    @pytest.mark.asyncio
    async def test_embedding_deterministic(self):
        service = EmbeddingService()
        e1 = await service.get_embedding("Hello world")
        e2 = await service.get_embedding("Hello world")
        assert e1 == e2

    @pytest.mark.asyncio
    async def test_embedding_different_texts(self):
        service = EmbeddingService()
        e1 = await service.get_embedding("Hello world")
        e2 = await service.get_embedding("Goodbye moon")
        assert e1 != e2

    @pytest.mark.asyncio
    async def test_embeddings_batch(self):
        service = EmbeddingService()
        embs = await service.get_embeddings_batch(
            ["Text 1", "Text 2"]
        )
        assert len(embs) == 2
        assert len(embs[0]) == 256

    @pytest.mark.asyncio
    async def test_embedding_normalized(self):
        service = EmbeddingService()
        emb = await service.get_embedding("test normalization")
        norm = math.sqrt(sum(v * v for v in emb))
        assert abs(norm - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_empty_text_embedding(self):
        service = EmbeddingService()
        emb = await service.get_embedding("")
        assert len(emb) == 256


class TestLLMService:
    """Tests for Replicate LLM service."""

    @pytest.mark.asyncio
    async def test_generate_summary(self):
        with patch(
            "app.services.llm_service.replicate"
        ) as mock_rep:
            mock_rep.run.return_value = iter(
                ["This is ", "a summary."]
            )
            from app.services.llm_service import LLMService

            service = LLMService()
            summary = await service.generate_summary(
                "Long document text..."
            )
            assert summary == "This is a summary."
            mock_rep.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_answer_question(self):
        with patch(
            "app.services.llm_service.replicate"
        ) as mock_rep:
            mock_rep.run.return_value = iter(
                ["The answer ", "is 42."]
            )
            from app.services.llm_service import LLMService

            service = LLMService()
            answer, ts = await service.answer_question(
                "What is the answer?",
                ["Context chunk"],
            )
            assert answer == "The answer is 42."
            assert ts is None

    @pytest.mark.asyncio
    async def test_answer_with_timestamps(self):
        with patch(
            "app.services.llm_service.replicate"
        ) as mock_rep:
            mock_rep.run.return_value = iter(
                ["The introduction covers basics"]
            )
            from app.services.llm_service import LLMService

            service = LLMService()
            timestamps = [
                TimestampedSegment(
                    start_time=0.0,
                    end_time=5.0,
                    text="Introduction covers basics",
                )
            ]
            answer, relevant = await service.answer_question(
                "What is the intro?",
                ["Context"],
                timestamps,
            )
            assert answer is not None
            assert relevant is not None

    @pytest.mark.asyncio
    async def test_answer_with_history(self):
        with patch(
            "app.services.llm_service.replicate"
        ) as mock_rep:
            mock_rep.run.return_value = iter(["Elaboration"])
            from app.services.llm_service import LLMService

            service = LLMService()
            history = [
                ChatMessage(
                    role="user", content="What is this?"
                ),
                ChatMessage(
                    role="assistant", content="A document."
                ),
            ]
            answer, _ = await service.answer_question(
                "Elaborate", ["Context"], None, history
            )
            assert answer == "Elaboration"

    def test_find_relevant_timestamps(self):
        with patch("app.services.llm_service.replicate"):
            from app.services.llm_service import LLMService

            service = LLMService()
            timestamps = [
                TimestampedSegment(
                    start_time=0.0,
                    end_time=5.0,
                    text="Python programming language",
                ),
                TimestampedSegment(
                    start_time=5.0,
                    end_time=10.0,
                    text="Short",
                ),
            ]
            result = service._find_relevant_timestamps(
                "python programming is great", timestamps
            )
            assert len(result) >= 1

    def test_find_relevant_timestamps_empty(self):
        with patch("app.services.llm_service.replicate"):
            from app.services.llm_service import LLMService

            service = LLMService()
            timestamps = [
                TimestampedSegment(
                    start_time=0.0,
                    end_time=5.0,
                    text="abc",
                ),
            ]
            result = service._find_relevant_timestamps(
                "xyz different", timestamps
            )
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_stream_answer(self):
        with patch(
            "app.services.llm_service.replicate"
        ) as mock_rep:
            mock_rep.run.return_value = iter(
                ["chunk1", "chunk2"]
            )
            from app.services.llm_service import LLMService

            service = LLMService()
            chunks = []
            async for c in service.stream_answer(
                "Question?", ["Context"]
            ):
                chunks.append(c)
            assert "".join(chunks) == "chunk1chunk2"


class TestVectorStore:
    """Tests for in-memory vector store."""

    @pytest.mark.asyncio
    async def test_upsert_chunks(self):
        store = VectorStore()
        ids = await store.upsert_chunks(
            "doc-1",
            ["chunk A", "chunk B"],
            [[1.0] + [0.0] * 255, [0.0, 1.0] + [0.0] * 254],
        )
        assert len(ids) == 2
        assert ids[0] == "doc-1_0"
        assert "doc-1" in _store

    @pytest.mark.asyncio
    async def test_search(self):
        store = VectorStore()
        await store.upsert_chunks(
            "doc-2",
            ["Python rocks", "Java ok"],
            [[1.0] + [0.0] * 255, [0.0, 1.0] + [0.0] * 254],
        )
        results = await store.search(
            [1.0] + [0.0] * 255, "doc-2", top_k=2
        )
        assert len(results) == 2
        assert results[0]["text"] == "Python rocks"
        assert results[0]["score"] > results[1]["score"]

    @pytest.mark.asyncio
    async def test_search_empty(self):
        store = VectorStore()
        results = await store.search(
            [0.1] * 256, "nonexistent", top_k=5
        )
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_delete_document(self):
        store = VectorStore()
        await store.upsert_chunks(
            "doc-3", ["chunk"], [[0.1] * 256]
        )
        assert "doc-3" in _store
        await store.delete_document("doc-3")
        assert "doc-3" not in _store

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        store = VectorStore()
        await store.delete_document("never-existed")


class TestAudioService:
    """Tests for audio service with mocked Replicate."""

    @pytest.mark.asyncio
    async def test_transcribe(self):
        with patch(
            "app.services.audio_service.replicate"
        ) as mock_rep:
            mock_rep.run.return_value = {
                "transcription": "Hello world",
                "segments": [
                    {
                        "start": 0.0,
                        "end": 5.0,
                        "text": "Hello world",
                    }
                ],
            }
            from app.services.audio_service import (
                AudioService,
            )

            service = AudioService()
            text, segs = (
                await service.transcribe_with_timestamps(
                    b"audio-bytes", "test.mp3"
                )
            )
            assert text == "Hello world"
            assert len(segs) == 1
            assert segs[0].start_time == 0.0

    @pytest.mark.asyncio
    async def test_transcribe_no_segments(self):
        with patch(
            "app.services.audio_service.replicate"
        ) as mock_rep:
            mock_rep.run.return_value = {
                "transcription": "Some text",
                "segments": [],
            }
            from app.services.audio_service import (
                AudioService,
            )

            service = AudioService()
            text, segs = (
                await service.transcribe_with_timestamps(
                    b"audio-bytes", "test.mp3"
                )
            )
            assert text == "Some text"
            assert len(segs) == 1

    @pytest.mark.asyncio
    async def test_get_timestamps_for_topic(self):
        from app.services.audio_service import AudioService

        service = AudioService()
        segments = [
            TimestampedSegment(
                start_time=0.0,
                end_time=5.0,
                text="Introduction to Python",
            ),
            TimestampedSegment(
                start_time=5.0,
                end_time=10.0,
                text="JavaScript basics",
            ),
        ]
        results = await service.get_timestamps_for_topic(
            segments, "Python"
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_timestamps_no_match(self):
        from app.services.audio_service import AudioService

        service = AudioService()
        segments = [
            TimestampedSegment(
                start_time=0.0,
                end_time=5.0,
                text="Hello",
            ),
        ]
        results = await service.get_timestamps_for_topic(
            segments, "quantum"
        )
        assert len(results) == 0


class TestCosineHelper:
    """Test cosine similarity helper."""

    def test_identical(self):
        from app.services.vector_store import (
            _cosine_similarity,
        )

        assert (
            abs(_cosine_similarity([1, 0], [1, 0]) - 1.0)
            < 0.001
        )

    def test_orthogonal(self):
        from app.services.vector_store import (
            _cosine_similarity,
        )

        assert (
            abs(_cosine_similarity([1, 0], [0, 1])) < 0.001
        )

    def test_opposite(self):
        from app.services.vector_store import (
            _cosine_similarity,
        )

        assert (
            abs(_cosine_similarity([1, 0], [-1, 0]) + 1.0)
            < 0.001
        )


class TestHelpers:
    """Tests for utility helper functions."""

    def test_get_file_extension(self):
        assert get_file_extension("test.pdf") == "pdf"
        assert get_file_extension("file.MP3") == "mp3"
        assert get_file_extension("no_ext") is None
        assert get_file_extension("") is None

    def test_format_timestamp(self):
        assert format_timestamp(0) == "0:00"
        assert format_timestamp(65) == "1:05"
        assert format_timestamp(3661) == "61:01"

    def test_ensure_upload_dir(self):
        with patch("os.makedirs") as mock_mkdir:
            result = ensure_upload_dir("/test/dir")
            mock_mkdir.assert_called_once_with(
                "/test/dir", exist_ok=True
            )
            assert result == "/test/dir"


class TestHealthCheck:
    """Test the health check endpoint."""

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
