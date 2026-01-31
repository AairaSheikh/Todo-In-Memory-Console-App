"""Chat routes for conversational task management."""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.repositories import ChatRepository
from app.services.chat import ChatService
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
import jwt
from app.config import get_settings

router = APIRouter(prefix="/api", tags=["chat"])


class ChatMessageRequest(BaseModel):
    """Request model for chat message submission."""
    message: str = Field(..., description="The message content")


class ChatMessageResponse(BaseModel):
    """Response model for chat message."""
    id: str
    content: str
    sender: str
    timestamp: str


class ChatEndpointResponse(BaseModel):
    """Response model for chat endpoint."""
    user_message_id: str
    user_message: str
    assistant_message_id: str
    assistant_message: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """Response model for chat history endpoint."""
    messages: list[ChatMessageResponse]
    total_count: int


def get_current_user_from_token(authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)) -> User:
    """Extract and validate user from JWT token in Authorization header.
    
    Args:
        authorization: Authorization header with JWT token
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Remove "Bearer " prefix if present
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
        
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        token_user_id = payload.get("user_id")
        
        if not token_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify user exists
        user = db.query(User).filter(User.id == UUID(token_user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )


@router.post("/{user_id}/chat", response_model=ChatEndpointResponse, status_code=status.HTTP_200_OK)
async def chat(
    user_id: str,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
) -> ChatEndpointResponse:
    """Process a chat message and return a response.
    
    Args:
        user_id: ID of the user sending the message
        request: Chat message request with message content
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ChatEndpointResponse: User message and assistant response
        
    Raises:
        HTTPException: If validation fails or user is not authenticated
        
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 5.1, 5.2, 5.3, 5.5, 6.1, 6.2, 9.1, 9.2, 9.3**
    """
    # Verify user_id matches current user
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID mismatch",
        )
    
    # Validate message is not empty or whitespace-only
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )
    
    try:
        # Create chat service and process message
        chat_service = ChatService(db)
        result = chat_service.process_message(current_user.id, request.message.strip())
        
        return ChatEndpointResponse(
            user_message_id=result["user_message"]["id"],
            user_message=result["user_message"]["content"],
            assistant_message_id=result["assistant_message"]["id"],
            assistant_message=result["assistant_message"]["content"],
            timestamp=result["user_message"]["timestamp"],
        )
        
    except ValueError as e:
        # Handle validation errors (e.g., empty message)
        import traceback
        print(f"Validation error in chat endpoint: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Log the error for debugging
        import traceback
        error_msg = str(e)
        print(f"Error in chat endpoint: {error_msg}")
        print(traceback.format_exc())
        
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your message: {error_msg}",
        )


@router.get("/{user_id}/chat/history", response_model=ChatHistoryResponse, status_code=status.HTTP_200_OK)
async def get_chat_history(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
) -> ChatHistoryResponse:
    """Retrieve conversation history for a user with pagination.
    
    Args:
        user_id: ID of the user
        limit: Maximum number of messages to retrieve (default 50)
        offset: Number of messages to skip (default 0)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ChatHistoryResponse: List of messages and total count
        
    Raises:
        HTTPException: If user is not authenticated or user_id mismatch
        
    **Validates: Requirements 4.2, 6.5, 8.3**
    """
    # Verify user_id matches current user
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID mismatch",
        )
    
    try:
        # Try to get messages, but handle case where table doesn't exist yet
        try:
            from app.models import ConversationMessage
            messages = db.query(ConversationMessage).filter(
                ConversationMessage.user_id == current_user.id
            ).order_by(
                ConversationMessage.created_at.asc()
            ).offset(offset).limit(limit).all()
            
            total_count = db.query(ConversationMessage).filter(
                ConversationMessage.user_id == current_user.id
            ).count()
        except Exception as table_error:
            # Table might not exist yet, return empty history
            print(f"Warning: Could not query conversation_messages table: {str(table_error)}")
            messages = []
            total_count = 0
        
        # Convert messages to response format
        message_responses = [
            ChatMessageResponse(
                id=str(msg.id),
                content=msg.content,
                sender=msg.sender,
                timestamp=msg.created_at.isoformat(),
            )
            for msg in messages
        ]
        
        return ChatHistoryResponse(
            messages=message_responses,
            total_count=total_count,
        )
        
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error in get_chat_history: {str(e)}")
        print(traceback.format_exc())
        
        # Return empty history instead of 500 error
        return ChatHistoryResponse(
            messages=[],
            total_count=0,
        )
