# DocuVerse - Document Universe

A modular, scalable document ingestion and semantic search system built with FastAPI, Celery, LlamaIndex, OpenAI embeddings, and Pinecone vector store.

## Features

- **Multi-format Document Support**: PDF, DOCX, CSV, Excel, PNG, JPEG, JPG
- **Real-time Processing**: WebSocket-based progress tracking
- **Async Processing**: Celery workers for document processing
- **Semantic Search**: OpenAI embeddings with Pinecone vector store
- **Source Tracking**: MongoDB for anchor metadata
- **Modern Frontend**: React with real-time progress and query interface

## Technology Stack

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com/) — REST API & WebSocket server
- [MongoDB](https://www.mongodb.com/) — Document database
- [Redis](https://redis.io/) — Message broker (Celery)
- [Pydantic](https://docs.pydantic.dev/) — Data validation
- [Uvicorn](https://www.uvicorn.org/) — ASGI server

**Async Worker:**
- [Celery](https://docs.celeryq.dev/) — Distributed task queue
- [LlamaIndex](https://www.llamaindex.ai/) — Document parsing & chunking
- [OpenAI](https://platform.openai.com/docs/api-reference) — Embeddings
- [Pinecone](https://www.pinecone.io/) — Vector database
- [PyMuPDF](https://pymupdf.readthedocs.io/), [pdfplumber](https://github.com/jsvine/pdfplumber), [python-docx](https://python-docx.readthedocs.io/), [openpyxl](https://openpyxl.readthedocs.io/), [pytesseract](https://pypi.org/project/pytesseract/), [Pillow](https://python-pillow.org/) — File & OCR support
- [Flower](https://flower.readthedocs.io/) — Celery monitoring

**Frontend:**
- [React](https://react.dev/) 18 — UI framework
- [React Router](https://reactrouter.com/) — Routing
- [React Query](https://tanstack.com/query/latest) — Data fetching/caching
- [Axios](https://axios-http.com/) — HTTP client
- [Tailwind CSS](https://tailwindcss.com/) — Styling
- [Lucide React](https://lucide.dev/) — Icons
- [Docker](https://www.docker.com/) — Containerization

---

## Architecture

```
DocuVerse/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── workers/
│   ├── main.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── README.md
├── worker/
│   ├── app/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── tasks.py
│   │   └── celery_app.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── start-flower.sh
│   ├── flower_config.py
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api.js
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   └── .dockerignore
├── docker-compose.yml
├── SETUP.md
├── env.example
└── README.md
```

## Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository>
   cd DocuVerse
   ```

2. **Environment Setup**:
   ```bash
   cp env.example .env
   # Edit .env with your API keys and service URLs
   ```

3. **Start All Services (Recommended)**:
   ```bash
   docker compose up --build
   ```
   - This will start backend, worker, flower, redis, mongodb, pinecone, and frontend.

4. **Manual Development (Advanced)**:
   - See SETUP.md for detailed manual setup instructions for each service.

## Environment Variables

Create a `.env` file in the root directory (see `env.example`):

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX=docuverse

# MongoDB
MONGODB_URI=mongodb://localhost:27017/docuverse

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Backend
BACKEND_URL=http://localhost:8000

# Frontend
REACT_APP_API_URL=http://backend:8000/api
```

## API Endpoints

- `POST /api/upload` - Upload documents
- `GET /api/documents` - List uploaded documents
- `POST /api/query` - Semantic search query
- `WS /ws/progress` - Real-time progress updates

## Monitoring

- **Flower**: http://localhost:5555 - Celery task monitoring and management

## License

MIT 