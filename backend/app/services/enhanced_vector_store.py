import logging
from typing import Any, Dict, List, Optional

from app.services.document_service import get_document_service
from app.services.vector_store import VectorStoreService

# Configure logging
logger = logging.getLogger(__name__)


class EnhancedVectorStoreService(VectorStoreService):
    def __init__(self) -> None:
        super().__init__()
        # Note: Cross-encoder reranking is disabled due to compatibility issues
        # Will use simple score-based reranking instead
        logger.info("EnhancedVectorStoreService initialized")

    async def query_with_conversation_context(
        self, query: str, conversation_history: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Enhanced query with conversation context"""
        logger.info(
            f"Starting query_with_conversation_context: query='{query[:50]}...', history_length={len(conversation_history)}, top_k={top_k}"
        )

        # 1. Generate conversation-aware query
        enhanced_query = self._enhance_query_with_history(query, conversation_history)
        logger.info(f"Enhanced query: '{enhanced_query[:100]}...'")

        # 2. Get embedding for enhanced query
        from app.services.embedding_service import embedding_service

        logger.info("Generating embedding for enhanced query...")
        query_embedding = await embedding_service.generate_single_embedding(enhanced_query)

        if not query_embedding:
            logger.warning("Failed to generate embedding for enhanced query, trying original query")
            # Fallback to original query
            query_embedding = await embedding_service.generate_single_embedding(query)

        if not query_embedding:
            logger.error("Failed to generate embedding for both enhanced and original query")
            return []

        logger.info(f"Generated embedding successfully, length: {len(query_embedding)}")

        # 3. Multi-vector retrieval
        logger.info(f"Querying vector store with top_k={top_k * 2}")
        semantic_results = await self.query_vectors(query_embedding, top_k * 2)
        logger.info(f"Vector store returned {len(semantic_results)} results")

        # 4. Fetch content from MongoDB for hybrid approach
        enriched_results = await self._enrich_results_with_mongodb_content(semantic_results)
        logger.info(f"Enriched {len(enriched_results)} results with MongoDB content")

        # 5. Rerank results
        reranked_results = self._rerank_results(query, enriched_results, top_k)
        logger.info(f"Reranking completed, returning {len(reranked_results)} results")

        return reranked_results

    async def _enrich_results_with_mongodb_content(self, vector_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich vector search results with content from MongoDB"""
        logger.info(f"Enriching {len(vector_results)} vector results with MongoDB content")

        enriched_results = []
        document_service = get_document_service()

        for result in vector_results:
            metadata = result.get("metadata", {})
            document_id = metadata.get("document_id")
            chunk_index = int(metadata.get("chunk_index", 0))

            logger.debug(f"Processing result: doc_id={document_id}, chunk={chunk_index}")

            if not document_id:
                logger.warning(f"No document_id found in metadata: {metadata}")
                continue

            try:
                # Fetch document from MongoDB
                document = await document_service.get_document(document_id)
                if not document:
                    logger.warning(f"Document not found in MongoDB: {document_id}")
                    continue

                # Get the specific chunk content from the chunks collection
                chunks = await document_service.get_document_chunks(document_id)
                if chunks and chunk_index < len(chunks):
                    content = chunks[chunk_index].get("content", "")
                    logger.debug(f"Retrieved chunk {chunk_index} content, length: {len(content)}")
                else:
                    logger.warning(f"Chunk index {chunk_index} not found for document {document_id}")
                    content = ""

                # Create enriched result
                enriched_result = {
                    "id": result["id"],
                    "score": result["score"],
                    "metadata": {
                        **metadata,
                        "content": content,
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "filename": document.filename,
                        "file_type": document.file_type.value if document.file_type else None,
                    },
                }

                logger.debug(f"Enriched result: content_length={len(content)}, filename={document.filename}")
                enriched_results.append(enriched_result)

            except Exception as e:
                logger.error(f"Error enriching result for document {document_id}: {e}")
                continue

        logger.info(f"Successfully enriched {len(enriched_results)} out of {len(vector_results)} results")
        return enriched_results

    def _enhance_query_with_history(self, query: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Enhance query with conversation history context"""
        logger.info(f"Enhancing query with {len(conversation_history)} history items")

        if not conversation_history:
            logger.info("No conversation history, returning original query")
            return query

        # Extract recent user questions and assistant answers
        recent_context = []
        for message in conversation_history[-4:]:  # Last 4 messages
            if message.get("role") == "user":
                recent_context.append(f"Previous question: {message.get('content', '')}")
            elif message.get("role") == "assistant":
                recent_context.append(f"Previous answer: {message.get('content', '')}")

        if recent_context:
            context_text = " ".join(recent_context)
            enhanced_query = f"{query} [Context from conversation: {context_text}]"
            logger.info(f"Enhanced query created: '{enhanced_query[:100]}...'")
            return enhanced_query

        logger.info("No relevant context found, returning original query")
        return query

    def _rerank_results(self, query: str, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Rerank results using simple score-based approach"""
        logger.info(f"Reranking {len(results)} results for query: '{query[:50]}...'")

        if not results:
            logger.info("No results to rerank")
            return []

        # Use existing scores for reranking (simple approach)
        for i, result in enumerate(results):
            # Use the original score as cross-encoder score for now
            result["cross_encoder_score"] = result.get("score", 0.0)
            content = result.get("metadata", {}).get("content", "")
            logger.debug(f"Result {i}: score={result.get('score', 0.0)}, content_preview='{content[:50]}...'")

        # Sort by score (already sorted by vector store, but ensure consistency)
        results.sort(key=lambda x: x.get("cross_encoder_score", 0), reverse=True)

        top_results = results[:top_k]
        logger.info(f"Reranking completed, top {len(top_results)} results selected")

        return top_results

    async def hybrid_search(
        self, query: str, conversation_history: Optional[List[Dict[str, Any]]] = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword search"""
        logger.info(
            f"Starting hybrid_search: query='{query[:50]}...', has_history={conversation_history is not None}, top_k={top_k}"
        )

        # Use conversation-aware retrieval
        if conversation_history:
            logger.info("Using conversation-aware retrieval")
            return await self.query_with_conversation_context(query, conversation_history, top_k)
        else:
            logger.info("No conversation history, using simple vector search")
            # Get embedding for query
            from app.services.embedding_service import embedding_service

            logger.info("Generating embedding for query...")
            query_embedding = await embedding_service.generate_single_embedding(query)

            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return []

            logger.info(f"Generated embedding successfully, length: {len(query_embedding)}")
            vector_results = await self.query_vectors(query_embedding, top_k)
            logger.info(f"Vector search returned {len(vector_results)} results")

            # Enrich with MongoDB content
            enriched_results = await self._enrich_results_with_mongodb_content(vector_results)
            logger.info(f"Enriched {len(enriched_results)} results with MongoDB content")

            return enriched_results

    async def get_context_for_qa(
        self, query: str, conversation_history: Optional[List[Dict[str, Any]]] = None, max_context_length: int = 4000
    ) -> Dict[str, Any]:
        """Get context optimized for Q&A"""
        logger.info(f"Getting context for Q&A: query='{query[:50]}...', max_length={max_context_length}")

        # Retrieve relevant documents
        search_results = await self.hybrid_search(query, conversation_history, top_k=8)

        logger.info(f"Retrieved {len(search_results)} search results")

        # Prepare context
        context_parts = []
        sources = []
        current_length = 0

        for i, result in enumerate(search_results):
            metadata = result.get("metadata", {})
            content = metadata.get("content", "")

            logger.debug(f"Processing result {i}: content_length={len(content)}, current_total={current_length}")

            # Check if adding this content would exceed limit
            if current_length + len(content) > max_context_length:
                logger.info(f"Stopping at result {i} due to context length limit")
                break

            context_parts.append(content)
            current_length += len(content)

            # Prepare source info
            source_info = {
                "document_id": metadata.get("document_id", ""),
                "chunk_index": metadata.get("chunk_index", 0),
                "page_number": metadata.get("page_number"),
                "score": result.get("score", 0.0),
                "cross_encoder_score": result.get("cross_encoder_score", 0.0),
                "filename": metadata.get("filename", ""),
                "file_type": metadata.get("file_type", ""),
            }
            sources.append(source_info)

            logger.debug(
                f"Added source: doc_id={source_info['document_id']}, chunk={source_info['chunk_index']}, score={source_info['score']}"
            )

        context = "\n\n".join(context_parts)

        logger.info(f"Context preparation completed: {len(sources)} sources, {current_length} characters")
        logger.debug(f"Context preview: '{context[:200]}...'")

        return {
            "context": context,
            "sources": sources,
            "context_length": current_length,
            "total_results": len(search_results),
        }


# Global instance
enhanced_vector_store = EnhancedVectorStoreService()
