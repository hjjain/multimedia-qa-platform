"""Document models for file metadata and upload responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """Supported file types."""
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"


class TimestampedSegment(BaseModel):
    """A segment of audio/video with timestamp information."""
    start_time: float
    end_time: float
    text: str


class DocumentMetadata(BaseModel):
    """Metadata stored in MongoDB for each uploaded document."""
    id: str = Field(alias="_id")
    filename: str
    file_type: FileType
    file_path: str
    upload_time: datetime = Field(default_factory=datetime.utcnow)
    summary: Optional[str] = None
    transcript: Optional[str] = None
    timestamps: Optional[List[TimestampedSegment]] = None
    chunk_ids: List[str] = []

    class Config:
        populate_by_name = True


class UploadResponse(BaseModel):
    """Response returned after a successful file upload."""
    document_id: str
    filename: str
    file_type: FileType
    summary: str
    timestamps: Optional[List[TimestampedSegment]] = None
    message: str
