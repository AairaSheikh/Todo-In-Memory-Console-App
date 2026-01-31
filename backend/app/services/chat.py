"""Chat service for managing conversational task operations."""

from sqlalchemy.orm import Session
from app.repositories import ChatRepository
from app.models import ConversationMessage
from app.services.ai_agent import AIAgent
from app.services.mcp_server import MCPServer
from uuid import UUID
from typing import List
from datetime import datetime


class ChatService:
    """Service layer for chat message processing and orchestration."""

    def __init__(self, db: Session, mcp_server: MCPServer = None):
        """Initialize chat service with database session.
        
        Args:
            db: SQLAlchemy database session
            mcp_server: MCPServer instance for AI agent (optional, created if not provided)
        """
        self.db = db
        self.repository = ChatRepository(db)
        
        # Initialize MCP server if not provided
        if mcp_server is None:
            from app.services.task import TaskService
            task_service = TaskService(db)
            mcp_server = MCPServer(db, task_service)
        
        self.mcp_server = mcp_server
        
        # Initialize AI agent
        self.ai_agent = AIAgent(mcp_server)

    def process_message(self, user_id: UUID, message: str) -> dict:
        """Process a user message and generate a response.
        
        This is the main orchestration method that:
        1. Validates and stores the user message
        2. Retrieves conversation history for context
        3. Generates an AI response using the AIAgent
        4. Stores the AI response
        5. Returns both messages
        
        Args:
            user_id: ID of the user sending the message
            message: The message content
            
        Returns:
            dict: Contains user_message and assistant_message with all fields
            
        Raises:
            ValueError: If message is empty or invalid
            
        **Validates: Requirements 1.1, 1.3, 1.4, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.5, 9.1, 9.2, 9.3**
        """
        # Validate message is not empty
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        
        try:
            # Store user message
            user_message = self.repository.add_message(
                user_id=user_id,
                content=message.strip(),
                sender="user",
            )
            
            # Retrieve conversation history for context (last 10 messages)
            history = self.get_recent_messages_for_context(user_id, count=10)
            
            # Generate AI response using AIAgent
            try:
                ai_response = self.ai_agent.process_message(user_id, message.strip(), history)
                response_text = ai_response["response"]
            except Exception as e:
                # Handle tool execution failures with user-friendly message
                print(f"Error in AIAgent.process_message: {str(e)}")
                import traceback
                print(traceback.format_exc())
                response_text = self._format_error_response(str(e))
            
            # Store assistant response
            assistant_message = self.repository.add_message(
                user_id=user_id,
                content=response_text,
                sender="assistant",
            )
            
            return {
                "user_message": {
                    "id": str(user_message.id),
                    "content": user_message.content,
                    "sender": user_message.sender,
                    "timestamp": user_message.created_at.isoformat(),
                },
                "assistant_message": {
                    "id": str(assistant_message.id),
                    "content": assistant_message.content,
                    "sender": assistant_message.sender,
                    "timestamp": assistant_message.created_at.isoformat(),
                },
            }
        except Exception as e:
            print(f"Error in ChatService.process_message: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise

    def get_conversation_history(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[ConversationMessage]:
        """Retrieve conversation history for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of messages to retrieve (default 50)
            offset: Number of messages to skip (default 0)
            
        Returns:
            List[ConversationMessage]: Messages in chronological order
            
        **Validates: Requirements 4.2**
        """
        return self.repository.get_messages(user_id, limit=limit, offset=offset)

    def get_recent_messages_for_context(self, user_id: UUID, count: int = 10) -> List[ConversationMessage]:
        """Retrieve recent messages for AI context.
        
        Args:
            user_id: ID of the user
            count: Number of recent messages to retrieve (default 10)
            
        Returns:
            List[ConversationMessage]: Most recent messages in chronological order
            
        **Validates: Requirements 4.3**
        """
        return self.repository.get_recent_messages(user_id, count=count)

    def _format_error_response(self, error_message: str) -> str:
        """Format an error message in a user-friendly way.
        
        Args:
            error_message: The error message to format
            
        Returns:
            str: User-friendly error response
            
        **Validates: Requirements 5.3, 9.2, 9.3**
        """
        # Handle specific error types
        if "not found" in error_message.lower():
            return "I couldn't find that task. Could you provide more details or check the task ID?"
        elif "permission" in error_message.lower() or "unauthorized" in error_message.lower():
            return "You don't have permission to perform that action."
        elif "invalid" in error_message.lower():
            return "I didn't quite understand that. Could you rephrase your request?"
        elif "timeout" in error_message.lower():
            return "The operation took too long. Please try again."
        else:
            # Generic error message
            return "I encountered an error while performing that operation. Please try again or rephrase your request."

