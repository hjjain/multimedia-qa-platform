"""Upload router for file processing and storage."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.document import (
    DocumentMetadata,
    UploadResponse,
    FileType,
)
from app.services.pdf_service import PDFService
from app.services.audio_service import AudioService
from app.services.video_service import VideoService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os

router = APIRouter()
settings = get_settings()

# Services
pdf_service = PDFService()
audio_service = AudioService()
video_service = VideoService()
embedding_service = EmbeddingService()
vector_store = VectorStore()
llm_service = LLMService()

# MongoDB
client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.mongodb_db_name]
documents_collection = db.documents


def get_file_type(filename: str) -> FileType:
    """Determine file type from filename extension."""
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        return FileType.PDF
    elif ext in ["mp3", "wav", "m4a"]:
        return FileType.AUDIO
    elif ext in ["mp4", "webm", "mov"]:
        return FileType.VIDEO
    raise HTTPException(400, f"Unsupported file type: {ext}")


@router.post("/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a document or media file.

    Handles PDF, audio, and video files:
    - Extracts text / transcribes content
    - Generates embeddings and stores in vector DB
    - Creates an AI-generated summary
    - Stores metadata in MongoDB
    """
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    file_type = get_file_type(file.filename)
    content = await file.read()

    # Validate file size
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            400,
            f"File too large. Max size: {settings.max_file_size_mb}MB",
        )

    document_id = str(uuid.uuid4())

    # Process based on file type
    if file_type == FileType.PDF:
        full_text, chunks = await pdf_service.process_pdf(content)
        timestamps = None
    elif file_type == FileType.AUDIO:
        full_text, timestamps = (
            await audio_service.transcribe_with_timestamps(
                content, file.filename
            )
        )
        chunks = [seg.text for seg in timestamps]
    else:  # VIDEO
        full_text, timestamps = (
            await video_service.process_video(
                content, file.filename
            )
        )
        chunks = [seg.text for seg in timestamps]

    # Generate embeddings and store in vector DB
    embeddings = await embedding_service.get_embeddings_batch(
        chunks
    )
    chunk_ids = await vector_store.upsert_chunks(
        document_id, chunks, embeddings
    )

    # Generate AI summary
    summary = await llm_service.generate_summary(full_text)

    # Save file to disk
    upload_dir = "/app/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{document_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)

    # Store metadata in MongoDB
    ts_dicts = (
        [ts.model_dump() for ts in timestamps]
        if timestamps
        else None
    )
    doc_metadata = DocumentMetadata(
        _id=document_id,
        filename=file.filename,
        file_type=file_type,
        file_path=file_path,
        summary=summary,
        transcript=(
            full_text if file_type != FileType.PDF else None
        ),
        timestamps=ts_dicts,
        chunk_ids=chunk_ids,
    )

    await documents_collection.insert_one(
        doc_metadata.model_dump(by_alias=True)
    )

    return UploadResponse(
        document_id=document_id,
        filename=file.filename,
        file_type=file_type,
        summary=summary,
        timestamps=timestamps,
        message="File processed successfully",
    )


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get document metadata by ID."""
    doc = await documents_collection.find_one(
        {"_id": document_id}
    )
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document, its vectors, and the stored file."""
    doc = await documents_collection.find_one(
        {"_id": document_id}
    )
    if not doc:
        raise HTTPException(404, "Document not found")

    # Delete from vector store
    await vector_store.delete_document(document_id)

    # Delete file from disk
    if os.path.exists(doc["file_path"]):
        os.remove(doc["file_path"])

    # Delete from MongoDB
    await documents_collection.delete_one({"_id": document_id})

    return {"message": "Document deleted successfully"}
