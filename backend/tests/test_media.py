"""Tests for the media router endpoints."""

import pytest
from unittest.mock import AsyncMock, patch


class TestMediaEndpoints:
    """Test suite for /api/media/ endpoints."""

    def test_get_timestamps_success(
        self, client, mock_mongodb
    ):
        """Test getting timestamps for a document."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "timestamps": [
                    {
                        "start_time": 0.0,
                        "end_time": 5.0,
                        "text": "First segment",
                    },
                    {
                        "start_time": 5.0,
                        "end_time": 10.0,
                        "text": "Second segment",
                    },
                ],
            }
        )

        response = client.get("/api/media/test-id/timestamps")
        assert response.status_code == 200
        data = response.json()
        assert len(data["timestamps"]) == 2

    def test_get_timestamps_not_found(
        self, client, mock_mongodb
    ):
        """Test timestamps for non-existent document."""
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.get(
            "/api/media/nonexistent/timestamps"
        )
        assert response.status_code == 404

    def test_get_timestamps_no_timestamps(
        self, client, mock_mongodb
    ):
        """Test timestamps for PDF document (no timestamps)."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "timestamps": None,
            }
        )

        response = client.get("/api/media/test-id/timestamps")
        assert response.status_code == 400

    def test_search_timestamps_success(
        self, client, mock_mongodb
    ):
        """Test searching timestamps by keyword."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "timestamps": [
                    {
                        "start_time": 0.0,
                        "end_time": 5.0,
                        "text": "Introduction to Python",
                    },
                    {
                        "start_time": 5.0,
                        "end_time": 10.0,
                        "text": "JavaScript basics",
                    },
                ],
            }
        )

        response = client.get(
            "/api/media/test-id/timestamps/search",
            params={"query": "python"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["timestamps"]) == 1
        assert data["query"] == "python"

    def test_search_timestamps_not_found(
        self, client, mock_mongodb
    ):
        """Test searching timestamps for non-existent doc."""
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.get(
            "/api/media/nonexistent/timestamps/search",
            params={"query": "test"},
        )
        assert response.status_code == 404

    def test_search_timestamps_no_timestamps(
        self, client, mock_mongodb
    ):
        """Test searching timestamps on a PDF document."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "timestamps": None,
            }
        )

        response = client.get(
            "/api/media/test-id/timestamps/search",
            params={"query": "test"},
        )
        assert response.status_code == 400

    def test_get_media_file_not_found(
        self, client, mock_mongodb
    ):
        """Test getting media file for non-existent document."""
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.get("/api/media/nonexistent/file")
        assert response.status_code == 404

    def test_get_media_file_no_disk(
        self, client, mock_mongodb
    ):
        """Test getting media file when file missing from disk."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "file_path": "/nonexistent/path.mp3",
                "filename": "test.mp3",
            }
        )

        with patch("os.path.exists", return_value=False):
            response = client.get("/api/media/test-id/file")
        assert response.status_code == 404

    def test_search_timestamps_no_match(
        self, client, mock_mongodb
    ):
        """Test searching timestamps with no matching results."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "timestamps": [
                    {
                        "start_time": 0.0,
                        "end_time": 5.0,
                        "text": "Hello world",
                    },
                ],
            }
        )

        response = client.get(
            "/api/media/test-id/timestamps/search",
            params={"query": "nonexistent"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["timestamps"]) == 0
