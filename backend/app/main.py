"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import upload, chat, media
from app.services.vector_store import init_pinecone


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: initialize Pinecone vector store
    init_pinecone()
    yield
    # Shutdown: cleanup resources if needed


app = FastAPI(
    title="Panscience Document Q&A API",
    description="AI-powered document and multimedia Q&A application",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(media.router, prefix="/api/media", tags=["Media"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
