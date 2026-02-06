"""Tests for backend services (PDF, embedding, LLM, etc.)."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.pdf_service import PDFService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStore
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
        """Test PDF text extraction from bytes."""
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
        """Test extraction from multi-page PDF."""
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
        """Test extraction when page returns None."""
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
        """Test text chunking creates proper sized chunks."""
        service = PDFService()
        text = "This is a test sentence. " * 100

        chunks = await service.chunk_text(text)
        assert len(chunks) > 0
        assert all(len(chunk) <= 1000 for chunk in chunks)

    @pytest.mark.asyncio
    async def test_process_pdf(self):
        """Test full PDF processing pipeline."""
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
    """Tests for embedding generation."""

    @pytest.mark.asyncio
    async def test_get_embedding(self):
        """Test single embedding generation."""
        with patch("app.services.embedding_service.OpenAI") as m:
            mock_client = MagicMock()
            embed_resp = MagicMock()
            embed_resp.data = [
                MagicMock(embedding=[0.1] * 1536)
            ]
            mock_client.embeddings.create.return_value = (
                embed_resp
            )
            m.return_value = mock_client

            service = EmbeddingService()
            embedding = await service.get_embedding("Test text")
            assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_get_embeddings_batch(self):
        """Test batch embedding generation."""
        with patch("app.services.embedding_service.OpenAI") as m:
            mock_client = MagicMock()
            embed_resp = MagicMock()
            embed_resp.data = [
                MagicMock(embedding=[0.1] * 1536),
                MagicMock(embedding=[0.2] * 1536),
            ]
            mock_client.embeddings.create.return_value = (
                embed_resp
            )
            m.return_value = mock_client

            service = EmbeddingService()
            embeddings = await service.get_embeddings_batch(
                ["Text 1", "Text 2"]
            )
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 1536


class TestLLMService:
    """Tests for LLM summarization and Q&A."""

    @pytest.mark.asyncio
    async def test_generate_summary(self):
        """Test summary generation."""
        with patch("app.services.llm_service.OpenAI") as m:
            mock_client = MagicMock()
            chat_resp = MagicMock()
            chat_resp.choices = [
                MagicMock(
                    message=MagicMock(content="Test summary")
                )
            ]
            mock_client.chat.completions.create.return_value = (
                chat_resp
            )
            m.return_value = mock_client

            service = LLMService()
            summary = await service.generate_summary(
                "Long document text..."
            )
            assert summary == "Test summary"

    @pytest.mark.asyncio
    async def test_answer_question(self):
        """Test question answering without timestamps."""
        with patch("app.services.llm_service.OpenAI") as m:
            mock_client = MagicMock()
            chat_resp = MagicMock()
            chat_resp.choices = [
                MagicMock(
                    message=MagicMock(content="Test answer")
                )
            ]
            mock_client.chat.completions.create.return_value = (
                chat_resp
            )
            m.return_value = mock_client

            service = LLMService()
            answer, ts = await service.answer_question(
                "What is this?",
                ["Context chunk 1", "Context chunk 2"],
            )
            assert answer == "Test answer"
            assert ts is None

    @pytest.mark.asyncio
    async def test_answer_question_with_timestamps(self):
        """Test Q&A with timestamp context."""
        with patch("app.services.llm_service.OpenAI") as m:
            mock_client = MagicMock()
            chat_resp = MagicMock()
            chat_resp.choices = [
                MagicMock(
                    message=MagicMock(
                        content="The introduction covers basics"
                    )
                )
            ]
            mock_client.chat.completions.create.return_value = (
                chat_resp
            )
            m.return_value = mock_client

            service = LLMService()
            timestamps = [
                TimestampedSegment(
                    start_time=0.0,
                    end_time=5.0,
                    text="Introduction covers basics",
                )
            ]
            answer, relevant = await service.answer_question(
                "What is the intro about?",
                ["Context"],
                timestamps,
            )
            assert answer is not None
            assert relevant is not None

    @pytest.mark.asyncio
    async def test_answer_question_with_history(self):
        """Test Q&A with conversation history."""
        with patch("app.services.llm_service.OpenAI") as m:
            mock_client = MagicMock()
            chat_resp = MagicMock()
            chat_resp.choices = [
                MagicMock(
                    message=MagicMock(content="Elaboration")
                )
            ]
            mock_client.chat.completions.create.return_value = (
                chat_resp
            )
            m.return_value = mock_client

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
        """Test timestamp relevance matching."""
        with patch("app.services.llm_service.OpenAI"):
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
                    text="Short text",
                ),
            ]

            result = service._find_relevant_timestamps(
                "python programming is great", timestamps
            )
            assert len(result) >= 1

    def test_find_relevant_timestamps_empty(self):
        """Test timestamp matching with no matches."""
        with patch("app.services.llm_service.OpenAI"):
            service = LLMService()
            timestamps = [
                TimestampedSegment(
                    start_time=0.0,
                    end_time=5.0,
                    text="abc",
                ),
            ]

            result = service._find_relevant_timestamps(
                "xyz completely different", timestamps
            )
            assert len(result) == 0


class TestVectorStore:
    """Tests for Pinecone vector store operations."""

    @pytest.mark.asyncio
    async def test_upsert_chunks(self, mock_pinecone_index):
        """Test storing chunks in vector store."""
        with patch(
            "app.services.vector_store.index",
            mock_pinecone_index,
        ):
            store = VectorStore()
            store.index = mock_pinecone_index

            chunk_ids = await store.upsert_chunks(
                "doc-1",
                ["chunk 1", "chunk 2"],
                [[0.1] * 1536, [0.2] * 1536],
            )

            assert len(chunk_ids) == 2
            assert chunk_ids[0] == "doc-1_0"
            mock_pinecone_index.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_search(self, mock_pinecone_index):
        """Test searching for relevant chunks."""
        mock_match = MagicMock()
        mock_match.metadata = {
            "text": "Test text",
            "chunk_index": 0,
        }
        mock_match.score = 0.95
        mock_pinecone_index.query.return_value = MagicMock(
            matches=[mock_match]
        )

        with patch(
            "app.services.vector_store.index",
            mock_pinecone_index,
        ):
            store = VectorStore()
            store.index = mock_pinecone_index

            results = await store.search(
                [0.1] * 1536, "doc-1", top_k=5
            )

            assert len(results) == 1
            assert results[0]["text"] == "Test text"
            assert results[0]["score"] == 0.95

    @pytest.mark.asyncio
    async def test_delete_document(self, mock_pinecone_index):
        """Test deleting document vectors."""
        with patch(
            "app.services.vector_store.index",
            mock_pinecone_index,
        ):
            store = VectorStore()
            store.index = mock_pinecone_index

            await store.delete_document("doc-1")
            mock_pinecone_index.delete.assert_called_once()


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
