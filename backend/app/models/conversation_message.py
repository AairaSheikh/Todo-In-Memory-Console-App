"""Conversation message model for chat history."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.database import Base


class ConversationMessage(Base):
    """Conversation message model for storing chat history."""

    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    sender = Column(String(20), nullable=False)  # 'user' or 'assistant'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="messages")

    def __repr__(self) -> str:
        """Return string representation of conversation message."""
        return f"<ConversationMessage(id={self.id}, user_id={self.user_id}, sender={self.sender})>"
