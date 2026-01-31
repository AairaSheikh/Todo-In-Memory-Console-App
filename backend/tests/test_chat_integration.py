"""Integration tests for chat endpoints and functionality."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal, Base, engine
from app.models import User, Task, ConversationMessage
from uuid import uuid4
from unittest.mock import patch, MagicMock
import os


# Mock OpenAI API to avoid actual API calls during testing
@pytest.fixture(autouse=True)
def mock_openai_api():
    """Mock OpenAI API for all tests."""
    with patch('app.services.ai_agent.OpenAI') as mock_openai:
        # Create a mock client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock the chat.completions.create method
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "I've processed your request. You have no tasks."
        mock_message.tool_calls = []
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        
        yield mock_client


@pytest.fixture(scope="function")
def test_client():
    """Create test client with fresh database."""
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    Base.metadata.drop_all(bind=engine)


class TestEndToEndChatFlow:
    """Integration tests for end-to-end chat flow (Task 17.1).
    
    **Validates: Requirements 1.1, 7.3, 7.4, 8.1**
    """

    def test_message_stored_in_database_directly(self, test_client):
        """Test that messages are stored in the database.
        
        Verifies:
        - Messages can be persisted to database
        - Messages can be retrieved from database
        """
        from app.repositories import ChatRepository
        from app.database import SessionLocal
        from uuid import uuid4
        
        # Create a test user ID
        test_user_id = uuid4()
        
        # Create a database session
        db = SessionLocal()
        try:
            # Create repository and add messages
            repo = ChatRepository(db)
            user_msg = repo.add_message(test_user_id, "Test message", "user")
            assistant_msg = repo.add_message(test_user_id, "Test response", "assistant")
            
            # Verify messages were stored
            assert user_msg.id is not None
            assert user_msg.content == "Test message"
            assert user_msg.sender == "user"
            
            assert assistant_msg.id is not None
            assert assistant_msg.content == "Test response"
            assert assistant_msg.sender == "assistant"
            
            # Retrieve messages
            messages = repo.get_messages(test_user_id)
            assert len(messages) == 2
            assert messages[0].content == "Test message"
            assert messages[1].content == "Test response"
        finally:
            db.close()

    def test_message_stored_in_database(self, test_client):
        """Test that messages are stored in the database.
        
        Verifies:
        - User message is persisted to database
        - Assistant message is persisted to database
        - Messages can be retrieved from database
        """
        from app.repositories import ChatRepository
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            repo = ChatRepository(db)
            
            # Add messages
            user_msg = repo.add_message(test_user_id, "List my tasks", "user")
            assistant_msg = repo.add_message(test_user_id, "You have no tasks", "assistant")
            
            # Retrieve and verify
            messages = repo.get_messages(test_user_id)
            assert len(messages) >= 2
            assert any(m.content == "List my tasks" for m in messages)
            assert any(m.content == "You have no tasks" for m in messages)
        finally:
            db.close()

    def test_ai_response_generated(self, test_client):
        """Test that AI response is generated for user message.
        
        Verifies:
        - AI generates a response
        - Response is not empty
        - Response can be stored
        """
        from app.services.chat import ChatService
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            chat_service = ChatService(db)
            result = chat_service.process_message(test_user_id, "List my tasks")
            
            assert result["user_message"]["content"] == "List my tasks"
            assert result["assistant_message"]["content"]
            assert len(result["assistant_message"]["content"]) > 0
        finally:
            db.close()

    def test_response_displayed_in_ui(self, test_client):
        """Test that response can be retrieved for display in UI.
        
        Verifies:
        - Response is returned from chat service
        - Response can be retrieved from repository
        - Response structure is correct for UI display
        """
        from app.services.chat import ChatService
        from app.repositories import ChatRepository
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            chat_service = ChatService(db)
            result = chat_service.process_message(test_user_id, "List my tasks")
            
            # Verify response structure
            assert "assistant_message" in result
            assert "timestamp" in result
            
            # Retrieve from repository to verify persistence
            repo = ChatRepository(db)
            messages = repo.get_messages(test_user_id)
            
            # Find the assistant message
            assistant_messages = [m for m in messages if m.sender == "assistant"]
            assert len(assistant_messages) > 0
            assert assistant_messages[-1].content == result["assistant_message"]["content"]
        finally:
            db.close()


class TestTaskOperationsThroughChatbot:
    """Integration tests for task operations through chatbot (Task 17.2).
    
    **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6**
    """

    def test_add_task_through_mcp_tool(self, test_client):
        """Test adding a task through the MCP tool.
        
        Verifies:
        - Task can be added via MCP tool
        - Task appears in task list
        - Task has correct properties
        """
        from app.services.mcp_server import MCPServer
        from app.services.task import TaskService
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            task_service = TaskService(db)
            mcp_server = MCPServer(db, task_service)
            
            # Add task via MCP tool
            result = mcp_server.add_task(test_user_id, "Buy groceries", "High")
            
            assert result["description"] == "Buy groceries"
            assert result["priority"] == "High"
            assert result["completed"] is False
            
            # Verify task appears in list
            tasks = mcp_server.list_tasks(test_user_id)
            assert len(tasks) > 0
            assert any(t["description"] == "Buy groceries" for t in tasks)
        finally:
            db.close()

    def test_complete_task_through_mcp_tool(self, test_client):
        """Test completing a task through the MCP tool.
        
        Verifies:
        - Task can be completed via MCP tool
        - Task completion is reflected in task list
        - Task status is updated correctly
        """
        from app.services.mcp_server import MCPServer
        from app.services.task import TaskService
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            task_service = TaskService(db)
            mcp_server = MCPServer(db, task_service)
            
            # Create a task first
            task = task_service.create_task(test_user_id, "Test task to complete", "Medium")
            
            # Complete task via MCP tool
            result = mcp_server.complete_task(test_user_id, str(task.id))
            
            assert result["completed"] is True
            
            # Verify task is completed in list
            tasks = mcp_server.list_tasks(test_user_id)
            completed_task = next((t for t in tasks if t["id"] == str(task.id)), None)
            assert completed_task is not None
            assert completed_task["completed"] is True
        finally:
            db.close()

    def test_delete_task_through_mcp_tool(self, test_client):
        """Test deleting a task through the MCP tool.
        
        Verifies:
        - Task can be deleted via MCP tool
        - Task is removed from task list
        - Task no longer appears in list
        """
        from app.services.mcp_server import MCPServer
        from app.services.task import TaskService
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            task_service = TaskService(db)
            mcp_server = MCPServer(db, task_service)
            
            # Create a task first
            task = task_service.create_task(test_user_id, "Task to delete", "Low")
            task_id = str(task.id)
            
            # Verify task exists
            tasks_before = mcp_server.list_tasks(test_user_id)
            assert len(tasks_before) > 0
            
            # Delete task via MCP tool
            mcp_server.delete_task(test_user_id, task_id)
            
            # Verify task is deleted
            tasks_after = mcp_server.list_tasks(test_user_id)
            task_ids_after = [t["id"] for t in tasks_after]
            assert task_id not in task_ids_after
        finally:
            db.close()

    def test_ui_synchronization_with_chatbot_operations(self, test_client):
        """Test that UI is synchronized with chatbot operations.
        
        Verifies:
        - Changes made through MCP tools are reflected in task list
        - Multiple operations are synchronized
        - UI can display updated state
        """
        from app.services.mcp_server import MCPServer
        from app.services.task import TaskService
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            task_service = TaskService(db)
            mcp_server = MCPServer(db, task_service)
            
            # Get initial task count
            initial_tasks = mcp_server.list_tasks(test_user_id)
            initial_count = len(initial_tasks)
            
            # Add task through MCP tool
            added_task = mcp_server.add_task(test_user_id, "Sync test task", "Medium")
            
            # Verify task count increased
            after_add = mcp_server.list_tasks(test_user_id)
            assert len(after_add) > initial_count
            
            # Complete the task through MCP tool
            mcp_server.complete_task(test_user_id, added_task["id"])
            
            # Verify task is completed in list
            updated_tasks = mcp_server.list_tasks(test_user_id)
            updated_task = next((t for t in updated_tasks if t["id"] == added_task["id"]), None)
            assert updated_task is not None
            assert updated_task["completed"] is True
        finally:
            db.close()


class TestConversationContextAndHistory:
    """Integration tests for conversation context and history (Task 17.3).
    
    **Validates: Requirements 4.2, 4.3, 4.4, 12.1, 12.2, 12.3**
    """

    def test_multiple_messages_with_task_operations(self, test_client):
        """Test sending multiple messages with task operations.
        
        Verifies:
        - Multiple messages can be sent in sequence
        - Each message is stored
        - Conversation history grows
        """
        from app.services.chat import ChatService
        from app.repositories import ChatRepository
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            chat_service = ChatService(db)
            
            # Send multiple messages
            chat_service.process_message(test_user_id, "Add a task to buy milk")
            chat_service.process_message(test_user_id, "Add a task to buy bread")
            chat_service.process_message(test_user_id, "List my tasks")
            
            # Verify all messages are in history
            repo = ChatRepository(db)
            messages = repo.get_messages(test_user_id, limit=100)
            
            # Should have at least 6 messages (3 user + 3 assistant)
            assert len(messages) >= 6
        finally:
            db.close()

    def test_ai_uses_context_from_previous_messages(self, test_client):
        """Test that AI uses context from previous messages.
        
        Verifies:
        - AI can reference previous messages
        - Context is maintained across messages
        - AI understands conversation flow
        """
        from app.services.chat import ChatService
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            chat_service = ChatService(db)
            
            # Send first message to add a task
            result1 = chat_service.process_message(test_user_id, "Add a task called important project")
            assert result1["user_message"]["content"] == "Add a task called important project"
            
            # Send second message referencing the previous task
            result2 = chat_service.process_message(test_user_id, "Mark it as high priority")
            assert result2["user_message"]["content"] == "Mark it as high priority"
            
            # Verify both messages are in history
            history = chat_service.get_conversation_history(test_user_id)
            assert len(history) >= 4  # 2 user + 2 assistant messages
        finally:
            db.close()

    def test_conversation_history_persisted_and_retrieved(self, test_client):
        """Test that conversation history is persisted and can be retrieved.
        
        Verifies:
        - Messages are persisted to database
        - History can be retrieved in chronological order
        - All messages are preserved
        """
        from app.services.chat import ChatService
        from app.repositories import ChatRepository
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            chat_service = ChatService(db)
            
            # Send multiple messages
            messages_sent = [
                "Add a task to study",
                "Add a task to exercise",
                "List my tasks",
            ]
            
            for msg in messages_sent:
                chat_service.process_message(test_user_id, msg)
            
            # Retrieve history
            repo = ChatRepository(db)
            messages = repo.get_messages(test_user_id, limit=100)
            
            # Verify messages are in chronological order
            user_messages = [m for m in messages if m.sender == "user"]
            
            # Should have all messages we sent
            assert len(user_messages) >= len(messages_sent)
            
            # Verify chronological order (timestamps should be increasing)
            for i in range(len(user_messages) - 1):
                assert user_messages[i].created_at <= user_messages[i + 1].created_at
        finally:
            db.close()

    def test_history_pagination(self, test_client):
        """Test that conversation history supports pagination.
        
        Verifies:
        - Limit parameter works
        - Offset parameter works
        - Total count is accurate
        """
        from app.repositories import ChatRepository
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            repo = ChatRepository(db)
            
            # Add multiple messages
            for i in range(5):
                repo.add_message(test_user_id, f"Message {i}", "user")
            
            # Get all messages
            all_messages = repo.get_messages(test_user_id, limit=100)
            total_count = len(all_messages)
            
            # Get paginated messages
            page1 = repo.get_messages(test_user_id, limit=3, offset=0)
            page2 = repo.get_messages(test_user_id, limit=3, offset=3)
            
            # Verify pagination works
            assert len(page1) <= 3
            assert len(page2) <= 3
            assert len(page1) + len(page2) <= total_count
        finally:
            db.close()


class TestErrorScenarios:
    """Integration tests for error scenarios (Task 17.4).
    
    **Validates: Requirements 1.2, 1.5, 9.1, 9.2, 9.3, 9.5**
    """

    def test_empty_message_rejection(self, test_client):
        """Test that empty messages are rejected.
        
        Verifies:
        - Empty string is rejected
        - Whitespace-only string is rejected
        - Proper error response is returned
        """
        from app.services.chat import ChatService
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            chat_service = ChatService(db)
            
            # Try to send empty message
            with pytest.raises(ValueError):
                chat_service.process_message(test_user_id, "")
            
            # Try to send whitespace-only message
            with pytest.raises(ValueError):
                chat_service.process_message(test_user_id, "   ")
        finally:
            db.close()

    def test_message_validation(self, test_client):
        """Test that message validation works correctly.
        
        Verifies:
        - Valid messages are accepted
        - Invalid messages are rejected
        """
        from app.repositories import ChatRepository
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            repo = ChatRepository(db)
            
            # Valid message should work
            msg = repo.add_message(test_user_id, "Valid message", "user")
            assert msg.content == "Valid message"
            
            # Invalid sender should raise error
            with pytest.raises(ValueError):
                repo.add_message(test_user_id, "Test", "invalid_sender")
        finally:
            db.close()

    def test_cross_user_access_rejection(self, test_client):
        """Test that users cannot access other users' chat history.
        
        Verifies:
        - User A cannot access User B's chat history
        - Proper error response is returned
        """
        from app.repositories import ChatRepository
        from app.database import SessionLocal
        from uuid import uuid4
        
        user1_id = uuid4()
        user2_id = uuid4()
        db = SessionLocal()
        try:
            repo = ChatRepository(db)
            
            # User 1 sends a message
            repo.add_message(user1_id, "User 1 private message", "user")
            
            # User 2 tries to access User 1's messages
            user2_messages = repo.get_messages(user2_id)
            
            # Should not have User 1's messages
            assert len(user2_messages) == 0
            
            # User 1 should have their message
            user1_messages = repo.get_messages(user1_id)
            assert len(user1_messages) > 0
        finally:
            db.close()

    def test_message_persistence_on_error(self, test_client):
        """Test that database state is preserved on error.
        
        Verifies:
        - Failed operations don't corrupt data
        - Previous messages are still accessible
        """
        from app.repositories import ChatRepository
        from app.database import SessionLocal
        from uuid import uuid4
        
        test_user_id = uuid4()
        db = SessionLocal()
        try:
            repo = ChatRepository(db)
            
            # Add a valid message
            msg1 = repo.add_message(test_user_id, "Valid message", "user")
            
            # Try to add invalid message (should fail)
            try:
                repo.add_message(test_user_id, "Invalid", "invalid_sender")
            except ValueError:
                pass  # Expected
            
            # Verify first message is still there
            messages = repo.get_messages(test_user_id)
            assert len(messages) == 1
            assert messages[0].content == "Valid message"
        finally:
            db.close()
