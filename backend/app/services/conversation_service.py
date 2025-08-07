from datetime import datetime
from typing import Any, Dict, List, Optional

import bson

from app.core.database import get_collection
from app.models.document import ConversationMessage, ConversationSession, ConversationSessionCreate


class ConversationService:
    def __init__(self) -> None:
        self.sessions_collection = get_collection("conversation_sessions")
        self.messages_collection = get_collection("conversation_messages")

    async def create_session(self, session_data: ConversationSessionCreate) -> ConversationSession:
        """Create a new conversation session"""
        session_dict = session_data.model_dump()
        session_dict["_id"] = str(bson.ObjectId())
        session_dict["created_at"] = datetime.utcnow()
        session_dict["updated_at"] = datetime.utcnow()
        session_dict["is_active"] = True
        session_dict["message_count"] = 0

        result = await self.sessions_collection.insert_one(session_dict)
        session_dict["id"] = str(result.inserted_id)

        return ConversationSession(**session_dict)

    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get conversation session by ID"""
        session_dict = await self.sessions_collection.find_one({"_id": session_id})
        if session_dict:
            # Convert _id to id
            session_dict["id"] = str(session_dict["_id"])
            del session_dict["_id"]
            return ConversationSession(**session_dict)
        return None

    async def get_active_sessions(self, user_id: Optional[str] = None) -> List[ConversationSession]:
        """Get all active conversation sessions"""
        filter_query: Dict[str, Any] = {"is_active": True}
        if user_id:
            filter_query["user_id"] = user_id

        cursor = self.sessions_collection.find(filter_query)
        sessions = []

        async for session in cursor:
            session_dict = dict(session)
            session_dict["id"] = str(session_dict["_id"])
            del session_dict["_id"]
            sessions.append(ConversationSession(**session_dict))

        return sessions

    async def update_session_title(self, session_id: str, title: str) -> None:
        """Update session title"""
        await self.sessions_collection.update_one(
            {"_id": session_id}, {"$set": {"title": title, "updated_at": datetime.utcnow()}}
        )

    async def delete_session(self, session_id: str) -> None:
        """Delete conversation session and all its messages"""
        # Mark session as inactive
        await self.sessions_collection.update_one(
            {"_id": session_id}, {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )

        # Delete all messages for this session
        await self.messages_collection.delete_many({"session_id": session_id})

    async def add_message(
        self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Add a message to a conversation session"""
        message_dict = {
            "_id": str(bson.ObjectId()),
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {},
        }

        await self.messages_collection.insert_one(message_dict)

        # Update session message count and timestamp
        await self.sessions_collection.update_one(
            {"_id": session_id}, {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
        )

        # Convert for return
        message_dict["id"] = message_dict["_id"]
        del message_dict["_id"]
        return ConversationMessage(**message_dict)  # type: ignore

    async def get_recent_messages(self, session_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages for a session"""
        cursor = self.messages_collection.find({"session_id": session_id}).sort("timestamp", -1).limit(count)

        messages = []
        async for message in cursor:
            message_dict = dict(message)
            message_dict["id"] = str(message_dict["_id"])
            del message_dict["_id"]
            messages.append(message_dict)

        # Return in chronological order
        return list(reversed(messages))


# Global instance - lazy loaded
_conversation_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    """Get the conversation service instance, creating it if necessary."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
