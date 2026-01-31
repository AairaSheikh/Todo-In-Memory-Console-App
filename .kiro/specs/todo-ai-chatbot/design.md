# Design Document: Todo AI Chatbot

## Overview

The Todo AI Chatbot extends the Phase 2 full-stack todo application with an AI-powered conversational interface for task management. The system consists of four main components:

1. **Chat Frontend**: React component providing a conversational UI for message exchange
2. **Chat Backend**: FastAPI service exposing chat endpoints and managing conversation flow
3. **MCP Server**: Backend service exposing task operations as MCP tools for the AI to use
4. **AI Agent**: OpenAI GPT-4 powered agent that processes messages and calls MCP tools
5. **Chat Repository**: Database layer managing persistent storage of conversation messages

The architecture integrates seamlessly with the existing Phase 2 task management system, reusing authentication, authorization, and task operations while adding a new conversational interaction model.

## Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser                              │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Next.js Frontend (App Router)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Chat Component: Message List, Input Field            │  │
│  │ State: Messages, Loading, Error, User Session        │  │
│  │ API Client: Sends messages to Chat Endpoint          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (JSON)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Chat Routes: POST /api/{user_id}/chat               │  │
│  │ Chat Service: Message processing, AI orchestration  │  │
│  │ MCP Server: Exposes task operations as tools        │  │
│  │ Middleware: JWT Validation, Rate Limiting           │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │
│                         ▼
│  ┌──────────────────────────────────────────────────────┐  │
│  │ OpenAI API Client                                    │  │
│  │ Sends messages to GPT-4 with MCP tools              │  │
│  │ Receives AI responses and tool calls                │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Neon Serverless PostgreSQL Database                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Tables: users, tasks, conversation_messages         │  │
│  │ Indexes: user_id, created_at, message_id            │  │
│  │ Constraints: Foreign keys, unique constraints       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Message Processing Flow

```
User sends message
        │
        ▼
Chat Endpoint receives message
        │
        ├─ Validate JWT token
        ├─ Validate message content
        └─ Extract user_id
        │
        ▼
Store user message in Chat_Repository
        │
        ▼
Retrieve conversation history from Chat_Repository
        │
        ▼
Send message + history + MCP tools to AI_Agent (GPT-4)
        │
        ▼
AI_Agent processes message
        │
        ├─ Understands intent
        ├─ Calls MCP tools as needed
        └─ Generates response
        │
        ▼
MCP tools execute task operations
        │
        ├─ Validate user_id
        ├─ Call existing task service
        └─ Return results
        │
        ▼
AI_Agent receives tool results
        │
        ▼
AI_Agent generates final response
        │
        ▼
Store chatbot response in Chat_Repository
        │
        ▼
Return response to Chat_UI
        │
        ▼
Chat_UI displays response
```

## Components and Interfaces

### Frontend Components

#### ChatComponent
```typescript
interface ChatComponentProps {
  userId: string;
  token: string;
}

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface ChatComponentState {
  messages: Message[];
  inputValue: string;
  isLoading: boolean;
  error: string | null;
}

Methods:
- sendMessage(content: string): Promise<void>
  Sends message to Chat_Endpoint and updates message list
  
- loadConversationHistory(): Promise<void>
  Retrieves conversation history from Chat_Endpoint
  
- handleError(error: Error): void
  Displays error message to user
  
- scrollToBottom(): void
  Auto-scrolls message list to latest message
```

#### MessageListComponent
```typescript
interface MessageListComponentProps {
  messages: Message[];
  isLoading: boolean;
}

Renders:
- User messages with user styling
- Assistant messages with assistant styling
- Loading indicator while waiting for response
- Timestamps for each message
```

#### MessageInputComponent
```typescript
interface MessageInputComponentProps {
  onSendMessage: (content: string) => void;
  isLoading: boolean;
}

Renders:
- Text input field for message content
- Send button (disabled while loading)
- Character count (optional)
- Keyboard shortcut hint (Enter to send)
```

### Backend API Endpoints

#### Chat Endpoint
```
POST /api/{user_id}/chat
  Request: { message: string }
  Response: { 
    id: string,
    message: string,
    response: string,
    timestamp: datetime,
    task_operations: [
      {
        operation: string,
        status: string,
        details: object
      }
    ]
  }
  Status: 200 OK
  
  Errors:
  - 400: Empty message
  - 401: Invalid/missing JWT token
  - 429: Rate limit exceeded
  - 500: Server error

GET /api/{user_id}/chat/history
  Request: Authorization header with JWT token
  Query params: limit=50, offset=0
  Response: [
    {
      id: string,
      content: string,
      sender: 'user' | 'assistant',
      timestamp: datetime
    }
  ]
  Status: 200 OK
  
  Errors:
  - 401: Invalid/missing JWT token
  - 500: Server error
```

### Backend Services

#### ChatService
```python
class ChatService:
    """Manages chat message processing and AI orchestration."""
    
    Methods:
    - process_message(user_id: str, message: str) -> ChatResponse
      Processes user message, calls AI agent, stores messages
      Returns response with task operations performed
      Raises ValueError if message is invalid
    
    - get_conversation_history(user_id: str, limit: int = 50, offset: int = 0) -> List[ChatMessage]
      Retrieves conversation history for user
      Returns messages in chronological order
    
    - _call_ai_agent(user_id: str, message: str, history: List[ChatMessage]) -> AIResponse
      Calls OpenAI GPT-4 with message and MCP tools
      Returns AI response with tool calls
    
    - _execute_tool_calls(user_id: str, tool_calls: List[ToolCall]) -> List[ToolResult]
      Executes MCP tool calls and returns results
      Validates user_id for each operation
```

#### MCPServer
```python
class MCPServer:
    """Exposes task operations as MCP tools for AI agent."""
    
    Methods:
    - add_task(user_id: str, description: str, priority: str = "Medium") -> Task
      Creates new task via existing task service
      Validates user_id and description
    
    - list_tasks(user_id: str) -> List[Task]
      Retrieves all tasks for user via existing task service
    
    - complete_task(user_id: str, task_id: str) -> Task
      Toggles task completion via existing task service
      Validates user_id and task ownership
    
    - delete_task(user_id: str, task_id: str) -> None
      Deletes task via existing task service
      Validates user_id and task ownership
    
    - update_task(user_id: str, task_id: str, description: str = None, priority: str = None) -> Task
      Updates task via existing task service
      Validates user_id and task ownership
```

#### ChatRepository
```python
class ChatRepository:
    """Data access layer for conversation message persistence."""
    
    Methods:
    - add_message(user_id: str, content: str, sender: str) -> ChatMessage
      Persists message to database
      Returns message with generated ID and timestamp
    
    - get_messages(user_id: str, limit: int = 50, offset: int = 0) -> List[ChatMessage]
      Retrieves messages for user in chronological order
    
    - get_recent_messages(user_id: str, count: int = 10) -> List[ChatMessage]
      Retrieves most recent N messages for user
      Used for AI agent context
    
    - delete_messages(user_id: str) -> None
      Deletes all messages for user (optional cleanup)
```

### OpenAI Integration

#### AIAgent
```python
class AIAgent:
    """OpenAI GPT-4 powered agent for task management."""
    
    Configuration:
    - Model: gpt-4 or gpt-4o
    - Temperature: 0.7 (balanced creativity and consistency)
    - Max tokens: 1000
    - Tools: MCP tools for task operations
    
    Methods:
    - process_message(user_id: str, message: str, history: List[ChatMessage]) -> AIResponse
      Sends message to GPT-4 with conversation history and MCP tools
      Returns response with tool calls and text
    
    - _format_system_prompt() -> str
      Creates system prompt instructing AI on task management
    
    - _format_messages(history: List[ChatMessage]) -> List[dict]
      Formats conversation history for OpenAI API
    
    - _parse_tool_calls(response: dict) -> List[ToolCall]
      Extracts tool calls from OpenAI response
```

## Data Models

### Database Schema

#### ConversationMessages Table
```sql
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sender VARCHAR(20) NOT NULL CHECK (sender IN ('user', 'assistant')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversation_messages_user_id ON conversation_messages(user_id);
CREATE INDEX idx_conversation_messages_created_at ON conversation_messages(created_at);
CREATE INDEX idx_conversation_messages_user_created ON conversation_messages(user_id, created_at);
```

### ORM Models (SQLAlchemy)

```python
class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sender: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="messages")
```

### API Request/Response Models (Pydantic)

```python
class ChatMessageRequest(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    id: str
    message: str
    response: str
    timestamp: datetime
    task_operations: List[Dict[str, Any]] = []

class ConversationMessageResponse(BaseModel):
    id: str
    content: str
    sender: str
    timestamp: datetime

class ChatHistoryResponse(BaseModel):
    messages: List[ConversationMessageResponse]
    total_count: int
```

### MCP Tool Definitions

```python
MCP_TOOLS = [
    {
        "name": "add_task",
        "description": "Add a new task to the user's task list",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "The task description"
                },
                "priority": {
                    "type": "string",
                    "enum": ["Low", "Medium", "High"],
                    "description": "Task priority (optional, defaults to Medium)"
                }
            },
            "required": ["description"]
        }
    },
    {
        "name": "list_tasks",
        "description": "List all tasks for the user",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "complete_task",
        "description": "Mark a task as complete or incomplete",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The ID of the task to complete"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "delete_task",
        "description": "Delete a task from the user's task list",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The ID of the task to delete"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "update_task",
        "description": "Update a task's description or priority",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The ID of the task to update"
                },
                "description": {
                    "type": "string",
                    "description": "New task description (optional)"
                },
                "priority": {
                    "type": "string",
                    "enum": ["Low", "Medium", "High"],
                    "description": "New task priority (optional)"
                }
            },
            "required": ["task_id"]
        }
    }
]
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.


### Chat Message Submission Properties

Property 1: Authenticated Chat Message Processing
*For any* authenticated user and valid message, sending a message to the Chat_Endpoint should process it and return a chatbot response.
**Validates: Requirements 1.1**

Property 2: Empty Message Validation
*For any* empty or whitespace-only message, submitting it to the Chat_Endpoint should be rejected with a 400 error.
**Validates: Requirements 1.2**

Property 3: User Message Persistence
*For any* authenticated user and valid message, sending a message should persist it to the Chat_Repository with correct user_id and timestamp.
**Validates: Requirements 1.3**

Property 4: Chatbot Response Persistence
*For any* chatbot response generated, it should be persisted to the Chat_Repository with correct user_id and timestamp.
**Validates: Requirements 1.4**

Property 5: Unauthenticated Request Rejection
*For any* request to the Chat_Endpoint without a valid JWT token, the request should be rejected with a 401 Unauthorized error.
**Validates: Requirements 1.5**

### Natural Language Understanding Properties

Property 6: Add Task Intent Recognition
*For any* message requesting to add a task, the AI_Agent should parse the request and extract the task description correctly.
**Validates: Requirements 2.1**

Property 7: List Tasks Intent Recognition
*For any* message requesting to list tasks, the AI_Agent should recognize the intent and call the list_tasks MCP tool.
**Validates: Requirements 2.2**

Property 8: Complete Task Intent Recognition
*For any* message requesting to complete a task, the AI_Agent should parse the request and identify the target task.
**Validates: Requirements 2.3**

Property 9: Delete Task Intent Recognition
*For any* message requesting to delete a task, the AI_Agent should parse the request and identify the target task.
**Validates: Requirements 2.4**

Property 10: Update Task Intent Recognition
*For any* message requesting to update a task, the AI_Agent should parse the request and extract the update details.
**Validates: Requirements 2.5**

### MCP Tool Integration Properties

Property 11: List Tasks Tool Returns All User Tasks
*For any* authenticated user, calling the list_tasks MCP tool should return all tasks belonging to that user.
**Validates: Requirements 3.2**

Property 12: MCP Tool Authorization Validation
*For any* MCP tool call, the MCP_Server should validate that the task belongs to the authenticated user before executing.
**Validates: Requirements 3.6**

### Conversation History Properties

Property 13: Message Storage with All Fields
*For any* message sent by a user, the Chat_Repository should store it with user_id, content, sender, and timestamp.
**Validates: Requirements 4.1**

Property 14: Conversation History Retrieval
*For any* authenticated user, the Chat_Endpoint should retrieve the conversation history from the Chat_Repository.
**Validates: Requirements 4.2**

Property 15: AI Agent Uses Conversation Context
*For any* message that requires context from previous messages, the AI_Agent should use the conversation history to understand the intent.
**Validates: Requirements 4.3**

Property 16: AI Agent References History for Previous Operations
*For any* user request about previous tasks or operations, the AI_Agent should reference the conversation history to provide accurate responses.
**Validates: Requirements 4.4**

Property 17: Chronological Message Ordering
*For any* set of messages stored in the Chat_Repository, retrieving them should return them in chronological order.
**Validates: Requirements 4.5**

### Response Generation Properties

Property 18: Successful Operation Confirmation
*For any* successful task operation, the Chatbot should generate a natural language response confirming the operation.
**Validates: Requirements 5.1**

Property 19: Task List Formatting
*For any* list of tasks retrieved, the Chatbot should format them in a readable way for the user.
**Validates: Requirements 5.2**

Property 20: Error Response Generation
*For any* failed task operation, the Chatbot should generate a response explaining the error in user-friendly language.
**Validates: Requirements 5.3**

Property 21: Multiple Operations Summarization
*For any* user message that triggers multiple task operations, the Chatbot should summarize all operations in the response.
**Validates: Requirements 5.5**

### Authentication and Authorization Properties

Property 22: JWT Token Validation
*For any* request to the Chat_Endpoint, the endpoint should validate the JWT_Token in the Authorization header.
**Validates: Requirements 6.1**

Property 23: User ID Extraction from Token
*For any* valid JWT_Token, the Chat_Endpoint should extract the correct user_id from the token.
**Validates: Requirements 6.2**

Property 24: Invalid Token Rejection
*For any* invalid or expired JWT_Token, the Chat_Endpoint should reject the request with a 401 Unauthorized error.
**Validates: Requirements 6.3**

Property 25: MCP Tool User ID Verification
*For any* MCP tool call, the MCP_Server should verify that the user_id matches the authenticated user.
**Validates: Requirements 6.4**

Property 26: Cross-User History Access Prevention
*For any* attempt to access another user's conversation history, the Chat_Repository should reject with a 403 Forbidden error.
**Validates: Requirements 6.5**

Property 27: Message User ID Association
*For any* message stored in the Chat_Repository, it should be associated with the authenticated user_id.
**Validates: Requirements 6.6**

### Chat UI Properties

Property 28: Message List Display
*For any* user navigating to the chat interface, the Chat_UI should display a message list showing previous messages and responses.
**Validates: Requirements 7.1**

Property 29: Send Button Enable on Input
*For any* non-empty message typed in the input field, the Chat_UI should enable the send button.
**Validates: Requirements 7.2**

Property 30: Message Submission on Send
*For any* send button click or Enter key press, the Chat_UI should submit the message to the Chat_Endpoint.
**Validates: Requirements 7.3**

Property 31: Response Display in Message List
*For any* response returned from the Chat_Endpoint, the Chat_UI should display it in the message list.
**Validates: Requirements 7.4**

Property 32: Loading Indicator Display
*For any* message being processed, the Chat_UI should display a loading indicator.
**Validates: Requirements 7.5**

Property 33: Error Message Display
*For any* error that occurs, the Chat_UI should display an error message to the user.
**Validates: Requirements 7.6**

Property 34: Conversation History Persistence in UI
*For any* user navigating away and returning to the chat interface, the Chat_UI should display the conversation history.
**Validates: Requirements 7.7**

### Message Persistence Properties

Property 35: Database Message Persistence
*For any* message sent by a user, the Chat_Repository should persist it to the database with all fields.
**Validates: Requirements 8.1**

Property 36: Persistence Across Application Restart
*For any* message persisted to the database, restarting the application and querying should retrieve the same message.
**Validates: Requirements 8.2**

Property 37: History Chronological Ordering
*For any* user requesting their conversation history, the Chat_Repository should return messages in chronological order.
**Validates: Requirements 8.3**

Property 38: Concurrent Message Consistency
*For any* multiple concurrent messages submitted, the Chat_Repository should maintain consistency without race conditions.
**Validates: Requirements 8.4**

Property 39: Failed Operation State Preservation
*For any* failed database operation, the Chat_Endpoint should return an error and the database state should remain unchanged.
**Validates: Requirements 8.5**

### Error Handling Properties

Property 40: Empty Message Error Response
*For any* empty message submitted, the Chat_Endpoint should return a 400 error with message "Message cannot be empty".
**Validates: Requirements 9.1**

Property 41: Unclear Request Clarification
*For any* message the AI_Agent fails to understand, the Chatbot should respond with a helpful message asking for clarification.
**Validates: Requirements 9.2**

Property 42: Tool Failure Error Handling
*For any* MCP tool call that fails, the Chatbot should inform the user of the failure and suggest alternatives.
**Validates: Requirements 9.3**

Property 43: OpenAI API Error Handling
*For any* API error from OpenAI, the Chatbot should respond with a user-friendly message and suggest retrying.
**Validates: Requirements 9.5**

### Rate Limiting and Performance Properties

Property 44: Rate Limiting Application
*For any* user sending multiple messages in rapid succession, the Chat_Endpoint should apply rate limiting.
**Validates: Requirements 10.1**

Property 45: Rate Limit Exceeded Response
*For any* user exceeding the rate limit, the Chat_Endpoint should return a 429 Too Many Requests error.
**Validates: Requirements 10.2**

Property 46: Response Timeout Compliance
*For any* message processed by the AI_Agent, the Chat_Endpoint should return a response within 30 seconds.
**Validates: Requirements 10.3**

Property 47: Concurrent Request Handling
*For any* concurrent requests from multiple users, the Chat_Endpoint should handle them without performance degradation.
**Validates: Requirements 10.4**

Property 48: Database Query Performance
*For any* conversation history query, the Chat_Repository should use appropriate indexing to maintain performance.
**Validates: Requirements 10.5**

### Integration with Existing Task System Properties

Property 49: List Tasks Tool Consistency
*For any* authenticated user, calling the list_tasks MCP tool should return the same tasks as the GET /api/{user_id}/tasks endpoint.
**Validates: Requirements 11.1**

Property 50: Add Task Tool Consistency
*For any* task created via the add_task MCP tool, it should be identical to a task created via POST /api/{user_id}/tasks.
**Validates: Requirements 11.2**

Property 51: Complete Task Tool Consistency
*For any* task toggled via the complete_task MCP tool, it should behave identically to PATCH /api/{user_id}/tasks/{id}/complete.
**Validates: Requirements 11.3**

Property 52: Delete Task Tool Consistency
*For any* task deleted via the delete_task MCP tool, it should behave identically to DELETE /api/{user_id}/tasks/{id}.
**Validates: Requirements 11.4**

Property 53: Update Task Tool Consistency
*For any* task updated via the update_task MCP tool, it should behave identically to PUT /api/{user_id}/tasks/{id}.
**Validates: Requirements 11.5**

Property 54: UI Synchronization with Chatbot Operations
*For any* task operation performed through the chatbot, the existing task list in the web UI should reflect the changes immediately.
**Validates: Requirements 11.6**

### Conversation Context Properties

Property 55: Pronoun Reference Resolution
*For any* message using pronouns like "it" after discussing a specific task, the AI_Agent should understand which task is being referenced.
**Validates: Requirements 12.1**

Property 56: Relative Reference Resolution
*For any* message using relative references like "the last one I added", the AI_Agent should identify the correct task from history.
**Validates: Requirements 12.2**

Property 57: Historical Question Resolution
*For any* question about previous operations like "What did I just add?", the AI_Agent should reference history correctly.
**Validates: Requirements 12.3**

Property 58: Multi-Operation Context Maintenance
*For any* conversation with multiple task operations, the AI_Agent should maintain context about which tasks have been discussed.
**Validates: Requirements 12.4**

Property 59: New Session History Access
*For any* new conversation session, the AI_Agent should have access to the full conversation history for context.
**Validates: Requirements 12.5**

## Error Handling

### Backend Error Handling

**Chat Endpoint Errors**:
- Empty message: 400 Bad Request with message "Message cannot be empty"
- Invalid token: 401 Unauthorized with message "Invalid or expired token"
- Rate limit exceeded: 429 Too Many Requests with message "Too many requests. Please try again later."
- Database error: 500 Internal Server Error with message "An error occurred. Please try again later."
- OpenAI API error: 503 Service Unavailable with message "AI service temporarily unavailable. Please try again."

**MCP Tool Errors**:
- Task not found: Tool returns error message "Task not found"
- Unauthorized access: Tool returns error message "You do not have permission to access this task"
- Invalid parameters: Tool returns error message "Invalid parameters provided"

**AI Agent Errors**:
- Failed to understand request: Responds with "I didn't quite understand that. Could you rephrase your request?"
- Tool execution failed: Responds with "I encountered an error while performing that operation. Please try again."
- OpenAI API timeout: Responds with "The AI service is taking longer than expected. Please try again."

### Frontend Error Handling

**Network Errors**:
- Display: "Network error. Please check your connection and try again."
- Action: Retry button with exponential backoff

**API Errors**:
- 4xx errors: Display error message from API response
- 5xx errors: Display "Server error. Please try again later."
- Timeout: Display "Request timed out. Please try again."

**Authentication Errors**:
- 401 Unauthorized: Clear token and redirect to login page
- 403 Forbidden: Display "You do not have permission to perform this action"

**Chat-Specific Errors**:
- Empty message: Display inline validation error "Message cannot be empty"
- Rate limit: Display "You're sending messages too quickly. Please wait a moment."

## Testing Strategy

### Unit Testing

Unit tests verify specific examples and edge cases:

1. **Chat Endpoint Tests**
   - Test sending message with valid authentication
   - Test sending empty message
   - Test sending message without authentication
   - Test rate limiting
   - Test message persistence
   - Test conversation history retrieval

2. **MCP Tool Tests**
   - Test add_task tool with valid parameters
   - Test list_tasks tool returns all user tasks
   - Test complete_task tool toggles completion
   - Test delete_task tool removes task
   - Test update_task tool updates fields
   - Test tool authorization checks

3. **Chat Service Tests**
   - Test message processing flow
   - Test AI agent integration
   - Test tool call execution
   - Test error handling
   - Test response generation

4. **Chat Repository Tests**
   - Test storing messages
   - Test retrieving messages
   - Test chronological ordering
   - Test user isolation
   - Test concurrent operations

5. **Frontend Component Tests**
   - Test message list rendering
   - Test input field interaction
   - Test send button state
   - Test loading indicator display
   - Test error message display
   - Test conversation history loading

### Property-Based Testing

Property-based tests verify universal properties across many generated inputs:

1. **Chat Message Properties**
   - Property 1: Authenticated Chat Message Processing
   - Property 2: Empty Message Validation
   - Property 3: User Message Persistence
   - Property 4: Chatbot Response Persistence
   - Property 5: Unauthenticated Request Rejection

2. **Natural Language Understanding Properties**
   - Property 6: Add Task Intent Recognition
   - Property 7: List Tasks Intent Recognition
   - Property 8: Complete Task Intent Recognition
   - Property 9: Delete Task Intent Recognition
   - Property 10: Update Task Intent Recognition

3. **MCP Tool Properties**
   - Property 11: List Tasks Tool Returns All User Tasks
   - Property 12: MCP Tool Authorization Validation

4. **Conversation History Properties**
   - Property 13: Message Storage with All Fields
   - Property 14: Conversation History Retrieval
   - Property 15: AI Agent Uses Conversation Context
   - Property 16: AI Agent References History for Previous Operations
   - Property 17: Chronological Message Ordering

5. **Response Generation Properties**
   - Property 18: Successful Operation Confirmation
   - Property 19: Task List Formatting
   - Property 20: Error Response Generation
   - Property 21: Multiple Operations Summarization

6. **Authentication and Authorization Properties**
   - Property 22: JWT Token Validation
   - Property 23: User ID Extraction from Token
   - Property 24: Invalid Token Rejection
   - Property 25: MCP Tool User ID Verification
   - Property 26: Cross-User History Access Prevention
   - Property 27: Message User ID Association

7. **Chat UI Properties**
   - Property 28: Message List Display
   - Property 29: Send Button Enable on Input
   - Property 30: Message Submission on Send
   - Property 31: Response Display in Message List
   - Property 32: Loading Indicator Display
   - Property 33: Error Message Display
   - Property 34: Conversation History Persistence in UI

8. **Message Persistence Properties**
   - Property 35: Database Message Persistence
   - Property 36: Persistence Across Application Restart
   - Property 37: History Chronological Ordering
   - Property 38: Concurrent Message Consistency
   - Property 39: Failed Operation State Preservation

9. **Error Handling Properties**
   - Property 40: Empty Message Error Response
   - Property 41: Unclear Request Clarification
   - Property 42: Tool Failure Error Handling
   - Property 43: OpenAI API Error Handling

10. **Rate Limiting and Performance Properties**
    - Property 44: Rate Limiting Application
    - Property 45: Rate Limit Exceeded Response
    - Property 46: Response Timeout Compliance
    - Property 47: Concurrent Request Handling
    - Property 48: Database Query Performance

11. **Integration Properties**
    - Property 49: List Tasks Tool Consistency
    - Property 50: Add Task Tool Consistency
    - Property 51: Complete Task Tool Consistency
    - Property 52: Delete Task Tool Consistency
    - Property 53: Update Task Tool Consistency
    - Property 54: UI Synchronization with Chatbot Operations

12. **Conversation Context Properties**
    - Property 55: Pronoun Reference Resolution
    - Property 56: Relative Reference Resolution
    - Property 57: Historical Question Resolution
    - Property 58: Multi-Operation Context Maintenance
    - Property 59: New Session History Access

### Testing Approach

- **Unit tests** focus on specific examples, edge cases, and error conditions
- **Property tests** verify that universal properties hold across all generated inputs
- **Integration tests** verify that chatbot and existing task system work together correctly
- Together, they provide comprehensive coverage: unit tests catch concrete bugs, property tests verify general correctness, integration tests verify system behavior

### Property Test Configuration

- Minimum 100 iterations per property test
- Use Hypothesis for Python backend property tests
- Use fast-check for TypeScript/JavaScript frontend property tests
- Each test tagged with feature name and property number
- Format: **Feature: todo-ai-chatbot, Property {number}: {property_text}**
