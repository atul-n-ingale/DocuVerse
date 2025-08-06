# DocuVerse Setup Guide

This guide will help you set up and run the DocuVerse document ingestion and semantic search system.

---

Before you begin, make sure you have the following installed:

DocuVerse is a modular, scalable platform with clear separation of concerns:

- **Backend (FastAPI):**
  - REST API and WebSocket server
  - Handles file uploads, user queries, and real-time status updates
  - Receives status/results from async worker via REST endpoints
  - Stores user/query history and task status in its own MongoDB database
  - Does **not** perform document processing or contain Celery/worker logic

- **Async Worker (Celery, LlamaIndex, Flower):**
  - Handles all document processing (PDF, DOCX, CSV, Excel, images)
  - Uses LlamaIndex, OpenAI, Pinecone, OCR, etc.
  - Maintains its own MongoDB for job tracking, logs, and audit
  - Communicates with backend **only via REST API** (never writes directly to backend DB)
  - Monitored by Flower

- **Redis:**
  - Message broker for Celery (backend <-> worker)

- **Pinecone:**
  - Vector storage for semantic search

- **Frontend (React):**
  - UI for document upload, real-time progress (WebSocket), and semantic search

---

## 🗂️ High-Level Architecture Diagram

```
[Frontend] <-> [Backend (FastAPI, WebSocket)] <-> [Redis Broker] <-> [Worker (Celery, LlamaIndex, Flower)]
      |                 |                             |                        |
      |                 |---> [MongoDB (backend)]     |                        |
      |                 |                             |                        |
      |                 |                             |---> [MongoDB (worker)] |
      |                 |                             |                        |
      |                 |                             |---> [Pinecone]         |
```

---

## 🚀 Quick Start with Docker (Recommended)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd DocuVerse
```

### 2. Configure Environment Variables

Copy the example environment file and configure your API keys:

```bash
cp env.example .env
```

Edit the `.env` file with your actual API keys. **For Docker Compose, make sure:**
- `REDIS_URL=redis://redis:6379/0`
- `MONGODB_URI=mongodb://mongodb:27017/docuverse` (for backend)
- The worker service uses its own MongoDB URI (see worker/README.md)

### 3. Start the System

Use the provided startup script:

```bash
./start.sh
```

Or manually with Docker Compose:

```bash
docker compose up --build -d
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Flower (Celery Monitor)**: http://localhost:5555

---

## 🛠️ Local Development Setup

### Backend Setup

1. **Create Python Virtual Environment**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**

```bash
poetry install
```

3. **Configure Environment**

Create a `.env` file in the backend directory with your API keys and correct MongoDB/Redis URIs.

4. **Start MongoDB and Redis**

```bash
# Using Docker
# (Recommended for local dev)
docker run -d -p 27017:27017 --name mongodb mongo:6.0
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

5. **Run the Backend**

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Worker Setup

1. **Create Python Virtual Environment**

```bash
cd worker
python -m venv venv
source venv/bin/activate
```

2. **Install Dependencies**

```bash
poetry install
```

3. **Configure Environment**

Create a `.env` file in the worker directory with correct MongoDB URI (for worker DB), Redis URL, and API keys.

4. **Run the Worker**

```bash
poetry run celery -A app.celery_app worker --loglevel=info
```

5. **Run Flower (monitoring)**

```bash
poetry run celery -A app.celery_app flower --port=5555
```

### Frontend Setup

1. **Install Dependencies**

```bash
cd frontend
npm install
```

2. **Configure Environment Variables**

- Copy the example file to the appropriate environment file:
  - For development:
    ```bash
    cp .env.development .env
    ```
  - For production build:
    ```bash
    cp .env.production .env
    ```
- Edit the `.env` file as needed. All variables must be prefixed with `REACT_APP_`.

3. **Start Development Server**

```bash
npm start
```

The frontend will be available at http://localhost:3000

4. **Build for Production**

```bash
npm run build
```

- The build will use the variables from `.env` at build time. For different environments, copy the appropriate file to `.env` before building.

---

## 🔄 Processing & Communication Flow

1. **User uploads a document via the frontend.**
2. **Backend** accepts the upload and enqueues a processing task to Celery (via Redis broker).
3. **Worker** receives the task and processes the document (text extraction, OCR, chunking, embedding, vector storage, audit logging).
4. **Worker** sends status/progress/results to backend via REST API.
5. **Backend** relays progress to frontend via WebSocket.
6. **User queries** are handled by backend, which uses Pinecone and metadata for semantic search.

---

## 🔒 Separation of Concerns
- **Backend**: API, WebSocket, orchestration, user/query history, receives worker updates, never does document processing.
- **Worker**: All document processing, embedding, vector storage, workflow state, audit, never writes directly to backend DB, only communicates via REST.
- **Frontend**: UI for upload, progress, and search.
- **Redis**: Message broker only.
- **MongoDB**: Separate DBs for backend and worker.
- **Pinecone**: Vector storage only.

---

## Monitoring and Management

- **Flower**: http://localhost:5555 (Celery/worker monitoring)
- **Docker Compose**: Orchestrates all services
- **Logs**: Use `docker compose logs -f <service>`

---

## API Keys Setup

- **OpenAI**: [OpenAI Platform](https://platform.openai.com/)
- **Pinecone**: [Pinecone Console](https://app.pinecone.io/)
- **Set keys in your .env files**

---

## Troubleshooting

- **Docker Services Not Starting**: Check Docker is running, ports are free, use `docker compose logs`
- **API Key Errors**: Verify keys in `.env`, check permissions/quotas
- **Document Processing Failures**: Check worker logs, verify file format support, check MongoDB connection
- **WebSocket Issues**: Ensure backend is running, check CORS, verify WebSocket endpoint

---

## Production Deployment

- Use secure environment variable management
- Configure HTTPS for all endpoints
- Use managed MongoDB and Pinecone
- Add logging/monitoring
- Scale Celery workers as needed
- Set up regular database backups

---

## Support

- Check troubleshooting section
- Review API docs at `/docs`
- Check service logs for error details
- Verify all prerequisites are met

---

## License

This project is licensed under the MIT License. 