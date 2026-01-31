"""Chat repository for managing conversation message persistence."""

from sqlalchemy.orm import Session
from app.models import ConversationMessage
from uuid import UUID
from datetime import datetime
from typing import List


class ChatRepository:
    """Data access layer for conversation message persistence."""

    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def add_message(self, user_id: UUID, content: str, sender: str) -> ConversationMessage:
        """Persist a message to the database.
        
        Args:
            user_id: ID of the user who sent/received the message
            content: Message content
            sender: 'user' or 'assistant'
            
        Returns:
            ConversationMessage: The persisted message with generated ID and timestamp
            
        Raises:
            ValueError: If sender is not 'user' or 'assistant'
        """
        if sender not in ["user", "assistant"]:
            raise ValueError(f"Invalid sender: {sender}. Must be 'user' or 'assistant'")
        
        message = ConversationMessage(
            user_id=user_id,
            content=content,
            sender=sender,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[ConversationMessage]:
        """Retrieve messages for a user in chronological order.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of messages to retrieve (default 50), None for all
            offset: Number of messages to skip (default 0)
            
        Returns:
            List[ConversationMessage]: Messages in chronological order (oldest first)
        """
        query = self.db.query(ConversationMessage).filter(
            ConversationMessage.user_id == user_id
        ).order_by(
            ConversationMessage.created_at.asc()
        ).offset(offset)
        
        if limit is not None:
            query = query.limit(limit)
        
        return query.all()

    def get_recent_messages(self, user_id: UUID, count: int = 10) -> List[ConversationMessage]:
        """Retrieve the most recent N messages for a user.
        
        Used for AI agent context. Returns messages in chronological order.
        
        Args:
            user_id: ID of the user
            count: Number of recent messages to retrieve (default 10)
            
        Returns:
            List[ConversationMessage]: Most recent messages in chronological order
        """
        return self.db.query(ConversationMessage).filter(
            ConversationMessage.user_id == user_id
        ).order_by(
            ConversationMessage.created_at.desc()
        ).limit(count).all()[::-1]  # Reverse to get chronological order

    def delete_messages(self, user_id: UUID) -> int:
        """Delete all messages for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            int: Number of messages deleted
        """
        count = self.db.query(ConversationMessage).filter(
            ConversationMessage.user_id == user_id
        ).delete()
        self.db.commit()
        return count
