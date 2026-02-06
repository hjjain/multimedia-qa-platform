"""Chat router for document Q&A and streaming responses."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse
from app.models.document import TimestampedSegment
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
import json

router = APIRouter()
settings = get_settings()

embedding_service = EmbeddingService()
vector_store = VectorStore()
llm_service = LLMService()

client = AsyncIOMotorClient(settings.mongodb_url)
db = client[settings.mongodb_db_name]
documents_collection = db.documents


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Answer a question about an uploaded document.

    Uses RAG (Retrieval-Augmented Generation) to find relevant
    context from the document and generate an answer.
    """
    # Get document metadata from MongoDB
    doc = await documents_collection.find_one(
        {"_id": request.document_id}
    )
    if not doc:
        raise HTTPException(404, "Document not found")

    # Get query embedding for semantic search
    query_embedding = await embedding_service.get_embedding(
        request.question
    )

    # Search for relevant chunks in Pinecone
    results = await vector_store.search(
        query_embedding, request.document_id, top_k=5
    )

    context_chunks = [r["text"] for r in results]
    sources = [f"Chunk {r['chunk_index']}" for r in results]

    # Get timestamps if document is audio/video
    timestamps = None
    if doc.get("timestamps"):
        timestamps = [
            TimestampedSegment(**ts)
            for ts in doc["timestamps"]
        ]

    # Generate answer using LLM
    answer, relevant_timestamps = (
        await llm_service.answer_question(
            request.question,
            context_chunks,
            timestamps,
            request.conversation_history,
        )
    )

    return ChatResponse(
        answer=answer,
        sources=sources,
        timestamps=relevant_timestamps,
    )


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream answer tokens for real-time chat response.

    Uses Server-Sent Events (SSE) format for streaming.
    """
    doc = await documents_collection.find_one(
        {"_id": request.document_id}
    )
    if not doc:
        raise HTTPException(404, "Document not found")

    query_embedding = await embedding_service.get_embedding(
        request.question
    )
    results = await vector_store.search(
        query_embedding, request.document_id, top_k=5
    )
    context_chunks = [r["text"] for r in results]

    async def generate():
        async for chunk in llm_service.stream_answer(
            request.question,
            context_chunks,
            request.conversation_history,
        ):
            data = json.dumps({"content": chunk})
            yield f"data: {data}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(), media_type="text/event-stream"
    )
