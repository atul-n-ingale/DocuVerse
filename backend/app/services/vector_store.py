import uuid
from typing import Any, Dict, List, Optional

from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings


class VectorStoreService:
    def __init__(self) -> None:
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.dimension = 1536  # OpenAI ada-002 embedding dimension

        # Initialize or get index
        if self.index_name not in self.pc.list_indexes().names():
            self._create_index()

        self.index = self.pc.Index(self.index_name)

    def _create_index(self) -> None:
        """Create Pinecone index if it doesn't exist"""
        self.pc.create_index(
            name=self.index_name,
            dimension=self.dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    async def upsert_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]:
        """Upsert vectors to Pinecone"""
        try:
            # Generate IDs for vectors
            vector_ids = [str(uuid.uuid4()) for _ in vectors]

            # Prepare vectors for upsert
            vectors_to_upsert = []
            for i, (vector, meta) in enumerate(zip(vectors, metadata)):
                vectors_to_upsert.append({"id": vector_ids[i], "values": vector, "metadata": meta})

            # Upsert to Pinecone
            self.index.upsert(vectors=vectors_to_upsert)

            return vector_ids

        except Exception as e:
            print(f"Error upserting vectors: {e}")
            raise

    async def query_vectors(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query vectors from Pinecone"""
        try:
            query_response = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict,
            )

            results = []
            for match in query_response.matches:
                results.append(
                    {
                        "id": match.id,
                        "score": match.score,
                        "metadata": match.metadata,
                    }
                )

            return results

        except Exception as e:
            print(f"Error querying vectors: {e}")
            raise

    async def delete_vectors(self, vector_ids: List[str]) -> None:
        """Delete vectors from Pinecone"""
        try:
            self.index.delete(ids=vector_ids)
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            raise

    async def delete_by_metadata_filter(self, filter_dict: Dict[str, Any]) -> None:
        """Delete vectors by metadata filter"""
        try:
            self.index.delete(filter=filter_dict)
        except Exception as e:
            print(f"Error deleting vectors by filter: {e}")
            raise


# Global instance
vector_store = VectorStoreService()
