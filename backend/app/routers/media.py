"""Media router for file serving and timestamp operations."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
import os

router = APIRouter()
settings = get_settings()

client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.mongodb_db_name]
documents_collection = db.documents


@router.get("/{document_id}/file")
async def get_media_file(document_id: str):
    """Serve the media file for browser playback."""
    doc = await documents_collection.find_one(
        {"_id": document_id}
    )
    if not doc:
        raise HTTPException(404, "Document not found")

    file_path = doc["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found on disk")

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=doc["filename"],
    )


@router.get("/{document_id}/timestamps")
async def get_timestamps(document_id: str):
    """Get all timestamps for an audio/video document."""
    doc = await documents_collection.find_one(
        {"_id": document_id}
    )
    if not doc:
        raise HTTPException(404, "Document not found")

    if not doc.get("timestamps"):
        raise HTTPException(
            400, "Document has no timestamps (not audio/video)"
        )

    return {"timestamps": doc["timestamps"]}


@router.get("/{document_id}/timestamps/search")
async def search_timestamps(document_id: str, query: str):
    """Search timestamps for a specific topic using keyword match."""
    doc = await documents_collection.find_one(
        {"_id": document_id}
    )
    if not doc:
        raise HTTPException(404, "Document not found")

    if not doc.get("timestamps"):
        raise HTTPException(400, "Document has no timestamps")

    query_lower = query.lower()
    matching = [
        ts
        for ts in doc["timestamps"]
        if query_lower in ts["text"].lower()
    ]

    return {"timestamps": matching, "query": query}
