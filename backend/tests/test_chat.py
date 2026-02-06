"""Tests for the chat router endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestChatEndpoints:
    """Test suite for /api/chat/ endpoints."""

    def test_chat_success(self, client, mock_mongodb):
        """Test successful chat interaction."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "timestamps": None,
            }
        )

        response = client.post(
            "/api/chat/",
            json={
                "document_id": "test-id",
                "question": "What is this about?",
                "conversation_history": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["answer"] == "Test answer"

    def test_chat_document_not_found(
        self, client, mock_mongodb
    ):
        """Test chat with non-existent document returns 404."""
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.post(
            "/api/chat/",
            json={
                "document_id": "nonexistent",
                "question": "Test?",
                "conversation_history": [],
            },
        )

        assert response.status_code == 404

    def test_chat_with_timestamps(self, client, mock_mongodb):
        """Test chat with audio/video timestamps included."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "timestamps": [
                    {
                        "start_time": 0.0,
                        "end_time": 5.0,
                        "text": "Introduction topic",
                    }
                ],
            }
        )

        response = client.post(
            "/api/chat/",
            json={
                "document_id": "test-id",
                "question": "Tell me about the introduction",
                "conversation_history": [],
            },
        )

        assert response.status_code == 200

    def test_chat_with_conversation_history(
        self, client, mock_mongodb
    ):
        """Test chat with previous conversation context."""
        mock_mongodb.find_one = AsyncMock(
            return_value={
                "_id": "test-id",
                "timestamps": None,
            }
        )

        response = client.post(
            "/api/chat/",
            json={
                "document_id": "test-id",
                "question": "Can you elaborate?",
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "What is this?",
                    },
                    {
                        "role": "assistant",
                        "content": "This is a test doc.",
                    },
                ],
            },
        )

        assert response.status_code == 200

    def test_chat_missing_question(self, client):
        """Test chat without question returns 422."""
        response = client.post(
            "/api/chat/",
            json={
                "document_id": "test-id",
            },
        )

        assert response.status_code == 422

    def test_stream_document_not_found(
        self, client, mock_mongodb
    ):
        """Test streaming chat with non-existent document."""
        mock_mongodb.find_one = AsyncMock(return_value=None)

        response = client.post(
            "/api/chat/stream",
            json={
                "document_id": "nonexistent",
                "question": "Test?",
                "conversation_history": [],
            },
        )

        assert response.status_code == 404
