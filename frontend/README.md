# DocuVerse Frontend

A modern React-based frontend for the DocuVerse platform, providing a user-friendly interface for document upload, real-time processing status, semantic search, and document management.

The DocuVerse frontend enables users to:
- Upload documents (PDF, DOCX, CSV, Excel, PNG, JPEG, JPG)
- Track real-time processing status via WebSocket
- Query ingested documents using natural language (semantic search)
- View and manage uploaded documents
- Delete documents with real-time progress tracking

---

## ✨ Features
- **Multi-format document upload** with drag-and-drop
- **Real-time progress bar** for document processing
- **Semantic search** interface for natural language queries
- **Document management**: view, delete, and inspect document chunks
- **Real-time document deletion** with progress tracking via WebSocket
- **System status dashboard** (API, worker, MongoDB, Redis, Flower)
- **Responsive UI** built with Tailwind CSS

---

## 🏗️ Architecture Overview

- **React 18** (functional components, hooks)
- **React Router** for navigation
- **React Query** for data fetching and caching
- **Axios** for API requests
- **WebSocket** for real-time updates
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Docker** for containerized builds and deployment

---

## ⚙️ Environment Variables

All environment variables must be prefixed with `REACT_APP_`.

- `REACT_APP_API_URL` — Base URL for backend API (e.g., `http://localhost:8000/api`)

Use `.env`, `.env.development`, and `.env.production` in the `frontend/` directory to manage environment-specific settings. See `.env.example` for a template.

---

## 🛠️ Local Development

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```
2. **Configure environment:**
   ```bash
   cp .env.development .env
   # Edit .env if needed
   ```
3. **Start the development server:**
   ```bash
   npm start
   ```
   The app will be available at [http://localhost:3000](http://localhost:3000)

---

## 🏭 Production Build

1. **Set environment variables:**
   ```bash
   cp .env.production .env
   # Edit .env if needed
   ```
2. **Build the app:**
   ```bash
   npm run build
   ```
3. **Serve the build:**
   - Use `serve -s build` or deploy the `build/` directory with your preferred static hosting.
   - In Docker, the build is served automatically.

---

## 🔗 Backend/API Integration

- All API calls use the base URL from `REACT_APP_API_URL`.
- WebSocket progress updates connect to the backend at `ws://<backend-host>:8000/ws/progress`.
- Document deletion events are handled via WebSocket:
  - `document_deletion_started` - Deletion process initiated
  - `document_deleted_success` - Document successfully deleted
  - `document_deleted_failed` - Document deletion failed with error
- Ensure the backend is running and accessible from the frontend container or local environment.

---

## 🧑‍💻 Tech Stack
- React 18
- React Router
- React Query
- Axios
- Tailwind CSS
- Lucide React
- Docker

---

## 📁 Directory Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── Navbar.js
│   │   └── SystemStatus.js
│   ├── pages/
│   │   ├── Dashboard.js
│   │   ├── Documents.js
│   │   ├── Query.js
│   │   └── Upload.js
│   ├── api.js
│   ├── App.js
│   ├── App.css
│   ├── index.js
│   └── index.css
├── tests/
│   ├── unit/
│   │   ├── hooks/
│   │   ├── components/
│   │   └── pages/
│   ├── integration/
│   │   ├── api/
│   │   ├── components/
│   │   └── pages/
│   └── e2e/
│       ├── flows/
│       └── scenarios/
├── public/
├── .env.example
├── .env.development
├── .env.production
├── Dockerfile
├── package.json
├── postcss.config.js
├── tailwind.config.js
└── README.md
```

---

## 🧪 Testing

The frontend includes a comprehensive testing suite:

- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test component interactions and API integration
- **E2E Tests**: Test complete user workflows

Run tests with:
```bash
npm test
```

---

## 📄 License
MIT 