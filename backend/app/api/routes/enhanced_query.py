import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from app.models.document import (
    ConversationSession,
    ConversationSessionCreate,
    ConversationSessionResponse,
    EnhancedQueryRequest,
    EnhancedQueryResponse,
)
from app.services.conversation_service import get_conversation_service
from app.services.document_service import get_document_service
from app.services.qa_graph_service import qa_graph_service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query/enhanced", response_model=EnhancedQueryResponse)
async def enhanced_query(request: EnhancedQueryRequest) -> EnhancedQueryResponse:
    """Enhanced query using LangGraph with conversation management"""
    start_time = time.time()
    logger.info(
        f"Enhanced query request received: query='{request.query[:50]}...', session_id={request.session_id}, max_results={request.max_results}"
    )

    try:
        conversation_service = get_conversation_service()

        # Get or create conversation session
        session_id = request.session_id
        if not session_id:
            logger.info("No session_id provided, creating new session")
            # Create new session
            session_data = ConversationSessionCreate(
                title=f"Conversation: {request.query[:50]}...", user_id=None  # TODO: Add user management
            )
            session = await conversation_service.create_session(session_data)
            session_id = session.id
            logger.info(f"Created new session: {session_id}")
        else:
            logger.info(f"Using existing session: {session_id}")

        # Get conversation history
        logger.info(f"Loading conversation history for session: {session_id}")
        conversation_history = await conversation_service.get_recent_messages(session_id, count=10)
        logger.info(f"Loaded {len(conversation_history)} conversation history items")

        # Process query using LangGraph
        logger.info("Starting LangGraph query processing")
        result = await qa_graph_service.process_query(
            query=request.query, session_id=session_id, conversation_history=conversation_history
        )
        logger.info(f"LangGraph processing completed, answer length: {len(result['answer'])}")

        # Add user message to conversation
        logger.info("Adding user message to conversation")
        await conversation_service.add_message(session_id=session_id, role="user", content=request.query)

        # Add assistant response to conversation
        logger.info("Adding assistant response to conversation")
        await conversation_service.add_message(
            session_id=session_id,
            role="assistant",
            content=result["answer"],
            metadata={
                "sources": result["sources"],
                "confidence": result["confidence"],
                "reasoning_steps": result["reasoning_steps"],
            },
        )

        # Update session title if it's a generic title
        current_session: Optional[ConversationSession] = await conversation_service.get_session(session_id)
        if current_session is not None and current_session.title.startswith("Conversation:"):
            new_title = f"Conversation: {request.query[:30]}..."
            await conversation_service.update_session_title(session_id, new_title)
            logger.info(f"Updated session title to: {new_title}")

        # Enrich sources with document information
        logger.info(f"Enriching {len(result['sources'])} sources with document information")
        enriched_sources = []
        for source in result["sources"]:
            document_id = source.get("document_id")
            if document_id:
                document = await get_document_service().get_document(document_id)
                if document:
                    source["filename"] = document.filename
                    source["file_type"] = document.file_type.value
                    logger.debug(f"Enriched source: {document.filename}")
            enriched_sources.append(source)

        processing_time = time.time() - start_time
        logger.info(f"Enhanced query processing completed in {processing_time:.2f}s")

        return EnhancedQueryResponse(
            answer=result["answer"],
            sources=enriched_sources if request.include_sources else [],
            confidence=result["confidence"],
            processing_time=processing_time,
            session_id=session_id,
            reasoning_steps=result["reasoning_steps"] if request.include_reasoning else [],
            conversation_history=conversation_history,
        )

    except Exception as e:
        error_msg = f"Error processing enhanced query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/conversations", response_model=ConversationSessionResponse)
async def create_conversation(session_data: ConversationSessionCreate) -> ConversationSessionResponse:
    """Create a new conversation session"""
    try:
        conversation_service = get_conversation_service()
        session = await conversation_service.create_session(session_data)

        return ConversationSessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=session.message_count,
            is_active=session.is_active,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationSessionResponse])
async def get_conversations(user_id: Optional[str] = None) -> List[ConversationSessionResponse]:
    """Get all conversation sessions for a user"""
    try:
        conversation_service = get_conversation_service()
        sessions = await conversation_service.get_active_sessions(user_id)

        return [
            ConversationSessionResponse(
                id=session.id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=session.message_count,
                is_active=session.is_active,
            )
            for session in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{session_id}", response_model=ConversationSessionResponse)
async def get_conversation(session_id: str) -> ConversationSessionResponse:
    """Get a specific conversation session"""
    try:
        conversation_service = get_conversation_service()
        session = await conversation_service.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Conversation session not found")

        return ConversationSessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=session.message_count,
            is_active=session.is_active,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/conversations/{session_id}")
async def update_conversation(session_id: str, title: str) -> Dict[str, str]:
    """Update conversation session title"""
    try:
        conversation_service = get_conversation_service()
        await conversation_service.update_session_title(session_id, title)
        return {"message": "Conversation updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{session_id}")
async def delete_conversation(session_id: str) -> Dict[str, str]:
    """Delete a conversation session"""
    try:
        conversation_service = get_conversation_service()
        await conversation_service.delete_session(session_id)
        return {"message": "Conversation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
