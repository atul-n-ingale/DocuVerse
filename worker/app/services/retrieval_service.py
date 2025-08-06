"""
RetrievalService: Single MongoDB hybrid retrieval combining Pinecone vectors with backend metadata.
Provides rich context for RAG applications with full metadata augmentation.
"""

import logging
from typing import Any, Dict, List, Optional, cast

from llama_index.core import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore

from app.config import BACKEND_URL, OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX
from app.services.document_ingestor import DocumentIngestor


class RetrievalService:
    """
    Single MongoDB hybrid retrieval service that combines Pinecone vector search with backend metadata.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.embedder = OpenAIEmbedding(
            model="text-embedding-3-small", api_key=OPENAI_API_KEY
        )
        self.vector_store = PineconeVectorStore(
            index_name=PINECONE_INDEX, api_key=PINECONE_API_KEY
        )

    def search_with_metadata(
        self,
        query: str,
        top_k: int = 5,
        document_filter: Optional[str] = None,
        file_type_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks with full metadata augmentation.

        Args:
            query: Search query
            top_k: Number of results to return
            document_filter: Filter by specific document ID
            file_type_filter: Filter by file type (e.g., '.pdf', '.csv')

        Returns:
            List of augmented search results with full metadata
        """
        try:
            # 1. Create vector store index
            index = VectorStoreIndex.from_vector_store(
                self.vector_store, embed_model=self.embedder
            )

            # 2. Build query filters for Pinecone
            pinecone_filters = {}
            if document_filter:
                pinecone_filters["document_id"] = document_filter
            if file_type_filter:
                pinecone_filters["file_type"] = file_type_filter

            # 3. Perform vector search
            retriever = index.as_retriever(
                similarity_top_k=top_k,
                filters=pinecone_filters if pinecone_filters else None,
            )

            vector_results = retriever.retrieve(query)

            # 4. Augment with backend metadata
            augmented_results = DocumentIngestor.augment_vectors_with_metadata(
                vector_results
            )

            self.logger.info(
                f"Retrieved {len(augmented_results)} results for query: {query}"
            )

            return augmented_results

        except Exception as e:
            self.logger.error(f"Error during retrieval: {str(e)}", exc_info=True)
            raise

    def search_by_document(
        self, document_id: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search within a specific document.
        """
        return self.search_with_metadata(
            query=query, top_k=top_k, document_filter=document_id
        )

    def search_by_file_type(
        self, file_type: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search within documents of a specific file type.
        """
        return self.search_with_metadata(
            query=query, top_k=top_k, file_type_filter=file_type
        )

    def get_document_chunks(
        self, document_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document with metadata from backend.
        """
        try:
            # Use backend API to get document chunks
            import requests

            response = requests.get(
                f"{BACKEND_URL}/documents/{document_id}/chunks",
                params={"limit": limit},
                timeout=10,
            )

            if response.status_code == 200:
                chunks = response.json()
                self.logger.info(
                    f"Retrieved {len(chunks)} chunks for document {document_id}"
                )
                return cast(List[Dict[str, Any]], chunks)
            else:
                self.logger.error(
                    f"Failed to get document chunks: {response.status_code}"
                )
                return []

        except Exception as e:
            self.logger.error(f"Error getting document chunks: {str(e)}", exc_info=True)
            raise

    def get_document_summary(self, document_id: str) -> Dict[str, Any]:
        """
        Get summary information about a document from backend.
        """
        try:
            # Use backend API to get document summary
            import requests

            response = requests.get(
                f"{BACKEND_URL}/documents/{document_id}", timeout=10
            )

            if response.status_code == 200:
                document = response.json()
                chunks = self.get_document_chunks(document_id)

                # Calculate additional statistics
                total_text_length = sum(
                    chunk.get("metadata", {}).get("text_length", 0) for chunk in chunks
                )

                summary = {
                    "document_id": document_id,
                    "file_path": document.get("filename", "Unknown"),
                    "file_type": document.get("file_type", "Unknown"),
                    "file_size": document.get("file_size", 0),
                    "total_chunks": len(chunks),
                    "total_text_length": total_text_length,
                    "average_chunk_length": (
                        total_text_length / len(chunks) if chunks else 0
                    ),
                    "created_at": document.get("upload_date"),
                    "status": document.get("status"),
                    "chunks": chunks,
                }

                return summary
            else:
                return {"error": "Document not found"}

        except Exception as e:
            self.logger.error(
                f"Error getting document summary: {str(e)}", exc_info=True
            )
            raise
