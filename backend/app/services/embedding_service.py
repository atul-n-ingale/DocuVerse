from typing import List

from openai import OpenAI

from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "text-embedding-ada-002"

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            # Create embeddings
            response = self.client.embeddings.create(model=self.model, input=texts)

            # Extract embedding vectors
            embeddings = [embedding.embedding for embedding in response.data]
            return embeddings

        except Exception as e:
            print(f"Error generating embeddings: {e}")
            raise

    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # If this isn't the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in ".!?":
                        end = i + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap
            if start >= len(text):
                break

        return chunks

    def prepare_text_for_embedding(self, text: str) -> str:
        """Clean and prepare text for embedding"""
        # Remove extra whitespace
        text = " ".join(text.split())

        # Truncate if too long (OpenAI has a limit)
        max_tokens = 8000  # Conservative limit
        # Rough estimate: 4 chars per token
        char_limit = max_tokens * 4
        if len(text) > char_limit:
            text = text[:char_limit]

        return text


# Global instance
embedding_service = EmbeddingService()
