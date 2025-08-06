from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, query, upload, worker
from app.core.database import close_mongo_connection, connect_to_mongo
from app.core.websocket_manager import WebSocketManager

app = FastAPI(title="DocuVerse API", description="Document Universe - Semantic Search System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager
websocket_manager = WebSocketManager()


# Include API routes
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(query.router, prefix="/api", tags=["query"])

# Pass WebSocket manager to documents router
documents.router.websocket_manager = websocket_manager
app.include_router(documents.router, prefix="/api", tags=["documents"])

# Pass WebSocket manager to worker router
worker.router.websocket_manager = websocket_manager
app.include_router(worker.router, prefix="/api", tags=["worker"])


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await close_mongo_connection()


# WebSocket endpoint for real-time progress
@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


@app.get("/")
async def root():
    return {"message": "Welcome to DocuVerse API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "DocuVerse API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
