"""Tests for the upload router endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import io


class TestUploadEndpoints:
    """Test suite for /api/upload/ endpoints."""

    def test_upload_pdf_success(self, client, mock_mongodb):
        """Test successful PDF upload and processing."""
        mock_mongodb.insert_one = AsyncMock()

        with patch("app.routers.upload.os.makedirs"), patch(
            "builtins.open", MagicMock()
        ):
            response = client.post(
                "/api/upload/",
                files={
                    "file": (
                        "test.pdf",
                        io.BytesIO(b"%PDF-1.4 test"),
                        "application/pdf",
                    )
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["filename"] == "test.pdf"
        assert data["file_type"] == "pdf"
        assert data["summary"] == "Test summary"
        assert data["message"] == "File processed successfully"

    def test_upload_audio_success(self, client, mock_mongodb):
        """Test successful audio file upload."""
        mock_mongodb.insert_one = AsyncMock()

        with patch("app.routers.upload.os.makedirs"), patch(
            "builtins.open", MagicMock()
        ):
            response = client.post(
                "/api/upload/",
                files={
                    "file": (
                        "test.mp3",
                        io.BytesIO(b"audio data"),
                        "audio/mpeg",
                    )
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["file_type"] == "audio"

    def test_upload_video_success(self, client, mock_mongodb):
        """Test successful video file upload."""
        mock_mongodb.insert_one = AsyncMock()

        with patch("app.routers.upload.os.makedirs"), patch(
            "builtins.open", MagicMock()
        ):
            response = client.post(
                "/api/upload/",
                files={
                    "file": (
                        "test.mp4",
                        io.BytesIO(b"video data"),
                        "video/mp4",
                    )
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["file_type"] == "video"

    def test_upload_unsupported_file(self, client):
        """Test upload of unsupported file type returns 400."""
        response = client.post(
            "/api/upload/",
            files={
                "file": (
                    "test.exe",
                    io.BytesIO(b"content"),
                    "application/exe",
                )
            },
        )
        assert response.status_code == 400

    def test_upload_no_file(self, client):
        """Test upload with no file returns 422."""
        response = client.post("/api/upload/")
        assert response.status_code == 422

    def test_get_document_success(self, client, mock_mongodb):
        """Test retrieving document metadata."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "filename": "test.pdf",
                "file_type": "pdf",
            }
        )

        response = client.get("/api/upload/test-id")
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"

    def test_get_document_not_found(self, client, mock_mongodb):
        """Test getting non-existent document returns 404."""
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.get("/api/upload/nonexistent")
        assert response.status_code == 404

    def test_delete_document_success(
        self, client, mock_mongodb
    ):
        """Test successful document deletion."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "file_path": "/tmp/test.pdf",
            }
        )

        with patch(
            "app.routers.upload.vector_store"
        ) as mock_vs, patch(
            "os.path.exists", return_value=True
        ), patch(
            "os.remove"
        ):
            mock_vs.delete_document = AsyncMock()
            response = client.delete("/api/upload/test-id")

        assert response.status_code == 200

    def test_delete_document_not_found(
        self, client, mock_mongodb
    ):
        """Test deleting non-existent document returns 404."""
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.delete("/api/upload/nonexistent")
        assert response.status_code == 404


class TestGetFileType:
    """Test file type detection logic."""

    def test_pdf_type(self):
        from app.routers.upload import get_file_type

        assert get_file_type("test.pdf") == "pdf"

    def test_audio_types(self):
        from app.routers.upload import get_file_type

        assert get_file_type("test.mp3") == "audio"
        assert get_file_type("test.wav") == "audio"
        assert get_file_type("test.m4a") == "audio"

    def test_video_types(self):
        from app.routers.upload import get_file_type

        assert get_file_type("test.mp4") == "video"
        assert get_file_type("test.webm") == "video"
        assert get_file_type("test.mov") == "video"

    def test_unsupported_type(self):
        from fastapi import HTTPException
        from app.routers.upload import get_file_type

        with pytest.raises(HTTPException):
            get_file_type("test.exe")
