# DocuVerse Worker

This directory contains the Celery async worker for document processing, embedding, and vector storage.

---

## 🚀 Overview

The DocuVerse Worker is a **standalone, decoupled service** responsible for all asynchronous document processing tasks. It is designed for scalability, modularity, and clear separation from the backend API. The worker is monitored by Flower and communicates with the backend **only via REST API calls** (never direct DB writes).

---

## 🧩 Key Responsibilities

- **Document Ingestion & Processing:**
  - Handles PDF, HTML, DOCX, PPT, Markdown, CSV, Excel, PNG, JPEG, JPG uploads
  - Performs text extraction, OCR (for images), and table recognition
  - Uses **LLMSherpa** for structured parsing of complex documents (PDF, HTML, DOCX, PPT, Markdown)
  - Uses **LlamaIndex** for vectorization and other document types
- **Embedding & Vector Storage:**
  - Generates OpenAI embeddings for document chunks
  - Stores vectors in Pinecone
- **Workflow State & Audit:**
  - Maintains its own MongoDB for job tracking, processing stages, logs, and audit records
  - Records all incoming requests, processing stages (start, in-progress, failed, completed), and detailed logs for debugging
- **Inter-Service Communication:**
  - Receives tasks via Celery/Redis from the backend
  - Reports status updates and results to the backend via HTTP POST/PUT endpoints (never writes directly to backend DB)
- **Monitoring:**
  - Exposes metrics and task status via Flower

---

## 🗂️ High-Level Architecture

```
[Backend (FastAPI)] <-> [Redis Broker] <-> [Worker (Celery, LLMSherpa, LlamaIndex, Flower)]
                                         |
                                         |---> [MongoDB (worker, for job tracking & audit)]
                                         |---> [Pinecone (vector storage)]
                                         |---> [LLMSherpa API (document parsing)]
```

---

## ⚙️ Processing Flow

1. **User uploads a document via the frontend.**
2. **Backend** accepts the upload and enqueues a processing task to Celery (via Redis broker).
3. **Worker** receives the task and:
   - Downloads the file (if needed)
   - Detects file type and routes to the appropriate handler:
     - **PDF/HTML/DOCX/PPT/Markdown:** Uses **LLMSherpa** for layout-aware parsing with table and image detection
     - **CSV/Excel:** Extracts text/tables using LlamaIndex readers
     - **Images (PNG/JPEG/JPG):** Runs OCR (pytesseract) to extract text
   - Chunks the document using LlamaIndex
   - Generates embeddings for each chunk (OpenAI)
   - Stores vectors in Pinecone
   - Saves workflow state, logs, and audit info in its own MongoDB
   - Reports progress and results back to the backend via REST API (e.g., task started, page 3 done, embedding complete)
4. **Backend** receives updates and relays them to the frontend via WebSocket.

---

## 🔄 Communication Pattern

- **Task Ingestion:**
  - Celery worker listens for new tasks from the Redis broker
- **Status Updates:**
  - Worker sends HTTP POST/PUT requests to backend endpoints for:
    - Task creation acknowledgment
    - Status/progress updates
    - Final results ready
- **No direct DB writes:**
  - Worker never writes directly to the backend's MongoDB

---

## 📝 Supported Document Types & Dependencies

### LLMSherpa-Powered Parsing (Layout-Aware)
- **PDF:** `llmsherpa` - Layout-aware parsing with table and image detection
- **HTML/HTM:** `llmsherpa` - HTML content extraction
- **DOCX/DOC:** `llmsherpa` - Microsoft Word document parsing
- **PPT/PPTX:** `llmsherpa` - PowerPoint presentation parsing
- **MD/Markdown:** `llmsherpa` - Markdown text parsing

### LlamaIndex-Powered Processing
- **CSV/Excel:** `pandas`, `openpyxl`, `llama-index`
- **Images (PNG, JPEG, JPG):** `pillow`, `pytesseract`, `llama-index`

### Core Dependencies
- **Embeddings:** `openai`
- **Vector Store:** `pinecone`
- **Workflow State:** `pymongo`
- **Document Parsing:** `llmsherpa`

---

## 🛠️ Development & Running

### Install dependencies (locally)
```bash
poetry install
```

### Run the worker (locally)
```bash
poetry run celery -A app.celery_app worker --loglevel=info
```

### Run Flower (monitoring)
```bash
poetry run celery -A app.celery_app flower --port=5555
```

### Test LLMSherpa Integration
```bash
poetry run python test_llmsherpa_imports.py
```

### Docker Compose (recommended for full stack)
```bash
docker compose up worker flower
```

---

## 🔒 Separation of Concerns
- The worker is **completely decoupled** from the backend API and database.
- All communication is via message broker (task ingestion) and REST API (status/results reporting).
- The worker can be scaled independently and monitored via Flower.

---

## 📚 Documentation
- [LLMSherpa Integration](LLMSHERPA_INTEGRATION.md) - Detailed guide on LLMSherpa integration
- [Document Deletion](DOCUMENT_ID_PREFIX_APPROACH.md) - Document deletion implementation
- [Metadata Structure](METADATA_STRUCTURE_IMPROVEMENTS.md) - Metadata storage improvements
- [Hybrid Approach](SINGLE_MONGODB_HYBRID_APPROACH.md) - Hybrid vector/metadata storage

---

## See Also
- [../backend/README.md](../backend/README.md) for backend API details
- [../docker-compose.yml](../docker-compose.yml) for orchestration