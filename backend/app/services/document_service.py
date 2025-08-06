from typing import Any, Dict, List, Optional

import bson

from app.core.database import get_collection
from app.models.document import Document, DocumentCreate, ProcessingStatus


class DocumentService:
    def __init__(self) -> None:
        self.documents_collection = get_collection("documents")
        self.chunks_collection = get_collection("chunks")

    async def create_document(self, document_data: DocumentCreate) -> Document:
        """Create a new document record"""
        document_dict = document_data.model_dump()
        document_dict["_id"] = str(bson.ObjectId())

        result = await self.documents_collection.insert_one(document_dict)
        document_dict["id"] = str(result.inserted_id)

        return Document(**document_dict)

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        document_dict = await self.documents_collection.find_one({"_id": document_id})
        if document_dict:
            # Explicitly convert _id to id for frontend compatibility
            doc_dict = dict(document_dict)
            if "_id" in doc_dict:
                doc_dict["id"] = str(doc_dict["_id"])
                del doc_dict["_id"]
            return Document(**doc_dict)
        return None

    async def update_document_status(self, document_id: str, status: ProcessingStatus, **kwargs: Any) -> None:
        """Update document status and other fields"""
        update_data = {"status": status}
        update_data.update(kwargs)

        await self.documents_collection.update_one({"_id": document_id}, {"$set": update_data})

    async def mark_document_deleting(self, document_id: str) -> None:
        """Mark document as deleting"""
        await self.update_document_status(document_id, ProcessingStatus.DELETING)

    async def mark_document_delete_error(self, document_id: str, error_message: str) -> None:
        """Mark document deletion as failed with error message"""
        await self.update_document_status(document_id, ProcessingStatus.DELETE_ERROR, error_message=error_message)

    async def get_all_documents(self) -> List[Document]:
        """Get all documents"""
        cursor = self.documents_collection.find()
        documents = []

        async for doc in cursor:
            # Explicitly convert _id to id for frontend compatibility
            doc_dict = dict(doc)
            if "_id" in doc_dict:
                doc_dict["id"] = str(doc_dict["_id"])
                del doc_dict["_id"]
            documents.append(Document(**doc_dict))

        return documents

    async def save_chunks(self, document_id: str, chunks: List[Dict[str, Any]]) -> None:
        """Save document chunks to database"""
        for chunk in chunks:
            chunk["_id"] = str(bson.ObjectId())
            chunk["document_id"] = document_id

        if chunks:
            await self.chunks_collection.insert_many(chunks)

    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document"""
        cursor = self.chunks_collection.find({"document_id": document_id})
        chunks = []

        async for chunk in cursor:
            chunk["id"] = chunk.pop("_id")
            chunks.append(chunk)

        return chunks

    async def delete_document(self, document_id: str) -> None:
        """Delete document and its chunks"""
        # Delete document
        await self.documents_collection.delete_one({"_id": document_id})

        # Delete chunks
        await self.chunks_collection.delete_many({"document_id": document_id})


# Global instance - lazy loaded
_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    """Get the document service instance, creating it if necessary."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
