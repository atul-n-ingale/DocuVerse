# DocuVerse Backend

A FastAPI-based backend service for document ingestion and semantic search.

---

## ⚡️ Updated Architecture Overview

DocuVerse is a modular, scalable platform for document ingestion and semantic search, built with clear separation of concerns:

- **Backend (this service):**
  - FastAPI REST API and WebSocket server
  - Handles file uploads, user queries, and real-time status updates
  - Receives status/results from async worker via REST endpoints
  - Stores user/query history and task status in its own MongoDB database
  - Does **not** perform document processing or contain Celery/worker logic

- **Async Worker (separate service):**
  - Celery-based worker for all document processing (PDF, DOCX, CSV, Excel, images)
  - Uses LlamaIndex, OpenAI, Pinecone, OCR, etc.
  - Maintains its own MongoDB for job tracking, logs, and audit
  - Communicates with backend **only via REST API** (never writes directly to backend DB)
  - Monitored by Flower

- **Redis:**
  - Message broker for Celery (backend <-> worker)

- **Pinecone:**
  - Vector storage for semantic search

- **Frontend:**
  - React-based UI for document upload, real-time progress (WebSocket), and semantic search

---

## 🗂️ High-Level Architecture

```
[Frontend] <-> [Backend (FastAPI, WebSocket)] <-> [Redis Broker] <-> [Worker (Celery, LlamaIndex, Flower)]
      |                 |                             |                        |
      |                 |                             |                        |
      |                 |---> [MongoDB (backend)]     |                        |
      |                 |                             |                        |
      |                 |                             |---> [MongoDB (worker)] |
      |                 |                             |                        |
      |                 |                             |---> [Pinecone]         |
```

- **User uploads document via frontend**
- **Backend** accepts upload, enqueues task to Celery via Redis
- **Worker** processes document, updates its own DB, and sends status/results to backend via REST
- **Backend** relays progress to frontend via WebSocket
- **User queries** are handled by backend, which uses Pinecone and metadata for semantic search

---

## Features

- Document upload and processing (via async worker)
- Real-time progress tracking via WebSockets
- Asynchronous document processing with Celery (in worker service)
- Semantic search with OpenAI embeddings
- Vector storage with Pinecone
- Document metadata storage with MongoDB (separate DBs for backend and worker)

## Installation

```bash
poetry install
```

## Running

```bash
poetry run uvicorn main:app --reload
```

## Docker

```bash
docker compose up backend
```

---

## See Also
- [worker/README.md](../worker/README.md) for async worker setup
- [docker-compose.yml](../docker-compose.yml) for service orchestration 