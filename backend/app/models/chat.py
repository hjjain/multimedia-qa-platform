"""Chat models for Q&A interactions."""

from pydantic import BaseModel
from typing import List, Optional


class ChatMessage(BaseModel):
    """A single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamps: Optional[List[dict]] = None


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    document_id: str
    question: str
    conversation_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    answer: str
    sources: List[str] = []
    timestamps: Optional[List[dict]] = None
