import time
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from openai import OpenAI

from app.core.config import settings
from app.models.document import QueryRequest, QueryResponse
from app.services.document_service import get_document_service
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest) -> QueryResponse:
    """Query documents using semantic search"""
    start_time = time.time()

    try:
        # Generate query embedding
        query_embedding = await embedding_service.generate_single_embedding(request.query)

        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")

        # Search vector store
        search_results = await vector_store.query_vectors(query_embedding, top_k=request.max_results)

        if not search_results:
            return QueryResponse(
                answer="No relevant documents found for your query.",
                sources=[],
                confidence=0.0,
                processing_time=time.time() - start_time,
            )

        # Prepare context from search results
        context_parts = []
        sources = []

        for result in search_results:
            metadata = result.get("metadata", {})
            content = metadata.get("content", "")
            document_id = metadata.get("document_id", "")
            chunk_index = metadata.get("chunk_index", 0)
            page_number = metadata.get("page_number")

            context_parts.append(content)

            # Get document info for source
            if document_id:
                document = await get_document_service().get_document(document_id)
                if document:
                    source_info = {
                        "document_id": document_id,
                        "filename": document.filename,
                        "chunk_index": chunk_index,
                        "score": result.get("score", 0.0),
                    }
                    if page_number:
                        source_info["page_number"] = page_number
                    sources.append(source_info)

        # Combine context
        context = "\n\n".join(context_parts)

        # Generate answer using OpenAI
        client = OpenAI(api_key=settings.openai_api_key)

        prompt = f"""Based on the following context, answer the user's question. 
        If the context doesn't contain enough information to answer the question, 
        say so clearly.

        Context:
        {context}

        Question: {request.query}

        Answer:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that answers questions " "based on provided document context."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        # Handle potential None content
        content = response.choices[0].message.content
        answer = content.strip() if content else "No answer generated"

        # Calculate confidence based on search scores
        if search_results:
            avg_score = sum(r.get("score", 0) for r in search_results) / len(search_results)
        else:
            avg_score = 0.0

        processing_time = time.time() - start_time

        return QueryResponse(
            answer=answer,
            sources=sources if request.include_sources else [],
            confidence=avg_score,
            processing_time=processing_time,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """Get all chunks for a specific document"""
    try:
        chunks = await get_document_service().get_document_chunks(document_id)
        return {"chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chunks: {str(e)}")
