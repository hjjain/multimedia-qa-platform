# Multimedia Q&A Platform

An AI-powered full-stack web application for document and multimedia question-answering. Upload PDFs, audio, or video files and interact with an intelligent chatbot that answers questions based on your content using Retrieval-Augmented Generation (RAG).

## Features

- **Multi-format Upload** - Support for PDF, audio (MP3, WAV, M4A), and video (MP4, WebM) files
- **AI-Powered Q&A** - RAG-based chatbot using LangChain + Llama 3 for accurate, context-aware answers
- **Automatic Summarization** - AI-generated summaries for all uploaded content
- **Timestamp Extraction** - Segment-level timestamps for audio/video via Whisper
- **Click-to-Play** - Navigate to specific timestamps in media files directly from chat responses
- **Semantic Search** - In-memory vector search with cosine similarity for finding relevant content
- **Real-time Streaming** - Server-Sent Events for streaming chat responses
- **Searchable Timestamps** - Search through audio/video timestamps by keyword

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.11) |
| **Frontend** | React 18, Vite, Tailwind CSS |
| **AI/ML** | Replicate (Llama 3 for LLM, Whisper for transcription) |
| **Vector Search** | In-memory cosine similarity (swappable for Pinecone/FAISS) |
| **Database** | MongoDB 7 (document metadata) |
| **Cache** | Redis 7 |
| **Containerization** | Docker & Docker Compose |
| **CI/CD** | GitHub Actions |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React + Vite  │────▶│    FastAPI       │────▶│   Replicate API │
│   Frontend      │◀────│    Backend       │◀────│ Llama 3/Whisper │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                ▼                ▼                ▼
         ┌───────────┐   ┌───────────┐   ┌───────────┐
         │  MongoDB   │   │  Vector   │   │   Redis   │
         │  Metadata  │   │  Store    │   │   Cache   │
         └───────────┘   └───────────┘   └───────────┘
```

### How It Works

1. **Upload** - User uploads a file (PDF/audio/video)
2. **Processing** - Backend extracts text (PDF) or transcribes (audio/video with timestamps via Whisper)
3. **Embedding** - Text chunks are embedded locally and stored in an in-memory vector store
4. **Summarization** - Llama 3 generates a concise summary via Replicate
5. **Q&A** - User asks questions; relevant chunks are retrieved via cosine similarity and passed to Llama 3
6. **Timestamps** - For media files, relevant timestamps are linked to answers with playback support

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Replicate API Token](https://replicate.com/account/api-tokens) (free tier available)

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/hjjain/multimedia-qa-platform.git
   cd multimedia-qa-platform
   ```

2. **Create environment file:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Replicate API token:

   ```env
   REPLICATE_API_TOKEN=r8_your_replicate_token_here
   ```

3. **Start the application:**

   ```bash
   docker compose up --build
   ```

4. **Access the app:**

   | Service | URL |
   |---------|-----|
   | Frontend | [http://localhost:3000](http://localhost:3000) |
   | Backend API | [http://localhost:8000](http://localhost:8000) |
   | API Documentation | [http://localhost:8000/docs](http://localhost:8000/docs) |
   | Health Check | [http://localhost:8000/health](http://localhost:8000/health) |

## API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/upload/` | Upload and process a file |
| `GET` | `/api/upload/{id}` | Get document metadata |
| `DELETE` | `/api/upload/{id}` | Delete a document |
| `POST` | `/api/chat/` | Send a chat message |
| `POST` | `/api/chat/stream` | Stream chat response (SSE) |
| `GET` | `/api/media/{id}/file` | Serve media file for playback |
| `GET` | `/api/media/{id}/timestamps` | Get all timestamps |
| `GET` | `/api/media/{id}/timestamps/search?query=` | Search timestamps |

### Example: Upload a File

```bash
curl -X POST "http://localhost:8000/api/upload/" \
  -F "file=@document.pdf"
```

**Response:**

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "file_type": "pdf",
  "summary": "This document covers...",
  "message": "File processed successfully"
}
```

### Example: Ask a Question

```bash
curl -X POST "http://localhost:8000/api/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "What are the key findings?",
    "conversation_history": []
  }'
```

**Response:**

```json
{
  "answer": "The key findings include...",
  "sources": ["Chunk 0", "Chunk 2"],
  "timestamps": null
}
```

### Example: Stream a Response

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "Summarize the main points",
    "conversation_history": []
  }'
```

## Testing

### Run Backend Tests

```bash
cd backend
pip install -r requirements.txt
pytest -v --cov=app --cov-report=html --cov-report=term-missing
```

**Coverage: 98%** (target: 95%+)

View the HTML coverage report at `backend/htmlcov/index.html`.

### Run Specific Test Files

```bash
pytest tests/test_upload.py -v      # Upload endpoint tests
pytest tests/test_chat.py -v        # Chat endpoint tests
pytest tests/test_media.py -v       # Media endpoint tests
pytest tests/test_services.py -v    # Service unit tests
pytest tests/test_video.py -v       # Video processing tests
```

## Development (Without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Set environment variables
export REPLICATE_API_TOKEN=your-token
export MONGODB_URL=mongodb://localhost:27017
export REDIS_URL=redis://localhost:6379

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173
```

## Project Structure

```
multimedia-qa-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Settings from environment variables
│   │   ├── models/
│   │   │   ├── document.py      # Document & upload models
│   │   │   └── chat.py          # Chat request/response models
│   │   ├── routers/
│   │   │   ├── upload.py        # File upload & processing endpoints
│   │   │   ├── chat.py          # Q&A and streaming chat endpoints
│   │   │   └── media.py         # Media file serving & timestamps
│   │   ├── services/
│   │   │   ├── pdf_service.py   # PDF text extraction & chunking
│   │   │   ├── audio_service.py # Audio transcription with Whisper
│   │   │   ├── video_service.py # Video audio extraction & transcription
│   │   │   ├── embedding_service.py  # Local hash-based embeddings
│   │   │   ├── vector_store.py  # In-memory vector search
│   │   │   └── llm_service.py   # Replicate Llama summarization & Q&A
│   │   └── utils/
│   │       └── helpers.py       # Utility functions
│   ├── tests/
│   │   ├── conftest.py          # Shared test fixtures
│   │   ├── test_upload.py       # Upload endpoint tests
│   │   ├── test_chat.py         # Chat endpoint tests
│   │   ├── test_media.py        # Media endpoint tests
│   │   ├── test_services.py     # Service unit tests
│   │   └── test_video.py        # Video processing tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.jsx   # Drag-and-drop file upload
│   │   │   ├── ChatInterface.jsx # Chat UI with streaming
│   │   │   ├── MediaPlayer.jsx  # Audio/video player with seek
│   │   │   ├── Summary.jsx      # Document summary display
│   │   │   └── TimestampList.jsx # Searchable timestamp list
│   │   ├── hooks/
│   │   │   └── useChat.js       # Chat state management hook
│   │   ├── services/
│   │   │   └── api.js           # API client with streaming support
│   │   ├── App.jsx              # Main application component
│   │   └── main.jsx             # React entry point
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── .github/
│   └── workflows/
│       └── ci.yml               # CI/CD pipeline
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and PR:

1. **Backend Tests** - Installs dependencies, runs linting, executes tests with 95%+ coverage requirement
2. **Frontend Build** - Installs dependencies and builds the production bundle
3. **Docker Build** - Builds all Docker images (runs on `main` branch only)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REPLICATE_API_TOKEN` | Yes | - | Replicate API token for Llama 3 and Whisper |
| `MONGODB_URL` | No | `mongodb://mongodb:27017` | MongoDB connection string |
| `REDIS_URL` | No | `redis://redis:6379` | Redis connection string |
| `LLM_MODEL` | No | `meta/meta-llama-3-8b-instruct` | Replicate LLM model |
| `WHISPER_MODEL` | No | `openai/whisper` | Replicate Whisper model |
| `MAX_FILE_SIZE_MB` | No | `100` | Maximum upload file size in MB |

## License

MIT
