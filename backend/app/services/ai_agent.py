"""AI Agent for processing messages and calling MCP tools."""

import os
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from openai import OpenAI, APIError, APITimeoutError
from app.models import ConversationMessage
from app.services.mcp_server import MCPServer


class AIAgent:
    """OpenAI GPT-4 powered agent for task management.
    
    This agent processes user messages, understands intent, calls MCP tools,
    and generates natural language responses.
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 4.3, 5.1, 5.2, 5.5, 9.5**
    """

    def __init__(self, mcp_server: MCPServer):
        """Initialize AI Agent with OpenAI client and MCP server.
        
        Args:
            mcp_server: MCPServer instance for executing tool calls
            
        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
            
        **Validates: Requirements 10.3**
        """
        # Try to get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        
        # If not found, try to get from settings
        if not api_key:
            try:
                from app.config import get_settings
                settings = get_settings()
                api_key = settings.openai_api_key
            except Exception as e:
                print(f"Error getting settings: {str(e)}")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Initialize OpenAI client with 30-second timeout
        self.client = OpenAI(api_key=api_key, timeout=30.0)
        self.mcp_server = mcp_server
        self.model = "gpt-4o"  # Using gpt-4o as it's more available than gpt-4
        self.temperature = 0.7
        self.max_tokens = 1000

    def process_message(
        self,
        user_id: UUID,
        message: str,
        history: List[ConversationMessage],
    ) -> Dict[str, Any]:
        """Process a user message and generate a response.
        
        This method:
        1. Formats the conversation history
        2. Sends the message to GPT-4 with MCP tools
        3. Parses tool calls from the response
        4. Executes tool calls via MCPServer
        5. Generates a final response with tool results
        
        Args:
            user_id: ID of the user
            message: The user message to process
            history: Conversation history for context
            
        Returns:
            dict: Contains 'response' (str) and 'tool_calls' (list of executed tools)
            
        Raises:
            ValueError: If message processing fails
            
        **Validates: Requirements 4.3, 5.1, 5.2, 5.5**
        """
        try:
            # Format messages for OpenAI API
            formatted_messages = self._format_messages(message, history)
            
            # Get tool definitions
            tools = self.mcp_server.get_tool_definitions()
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                tools=[{"type": "function", "function": tool} for tool in tools],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            # Parse response
            assistant_message = response.choices[0].message
            
            # Execute tool calls if any
            tool_results = []
            if assistant_message.tool_calls:
                tool_results = self._execute_tool_calls(user_id, assistant_message.tool_calls)
            
            # Generate final response
            final_response = self._generate_final_response(
                assistant_message.content,
                tool_results,
            )
            
            return {
                "response": final_response,
                "tool_calls": tool_results,
            }
            
        except APITimeoutError as e:
            print(f"OpenAI API timeout: {str(e)}")
            return {
                "response": "The AI service is taking longer than expected. Please try again.",
                "tool_calls": [],
            }
        except APIError as e:
            print(f"OpenAI API error: {str(e)}")
            return {
                "response": "I encountered an error while processing your request. Please try again.",
                "tool_calls": [],
            }
        except Exception as e:
            print(f"Unexpected error in AIAgent.process_message: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {
                "response": "An unexpected error occurred. Please try again.",
                "tool_calls": [],
            }

    def _format_messages(
        self,
        message: str,
        history: List[ConversationMessage],
    ) -> List[Dict[str, str]]:
        """Format conversation history and current message for OpenAI API.
        
        Args:
            message: The current user message
            history: Conversation history
            
        Returns:
            list: Formatted messages for OpenAI API
            
        **Validates: Requirements 4.3**
        """
        messages = [
            {
                "role": "system",
                "content": self._format_system_prompt(),
            }
        ]
        
        # Add conversation history
        for msg in history:
            role = "user" if msg.sender == "user" else "assistant"
            messages.append({
                "role": role,
                "content": msg.content,
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message,
        })
        
        return messages

    def _format_system_prompt(self) -> str:
        """Create system prompt for task management context.
        
        Returns:
            str: System prompt for the AI agent
            
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 12.1, 12.2, 12.3, 12.4, 12.5**
        """
        return """You are a helpful task management assistant. Your role is to help users manage their tasks through conversation.

You have access to the following tools:
- add_task: Add a new task to the user's task list
- list_tasks: List all tasks for the user
- complete_task: Mark a task as complete or incomplete
- delete_task: Delete a task from the user's task list
- update_task: Update a task's description or priority

CRITICAL INSTRUCTIONS FOR TASK OPERATIONS:

When a user asks to ADD a task:
1. Extract the task description from their message - this is REQUIRED
2. The description should be the main content of what they want to add
3. Examples:
   - "add new task pilates" → description: "pilates"
   - "add buy groceries" → description: "buy groceries"
   - "add call mom" → description: "call mom"
4. Optionally extract priority if mentioned (High, Medium, Low)
5. ALWAYS provide a non-empty description to the add_task tool

When a user asks to UPDATE/CHANGE a task:
1. FIRST call list_tasks to get all current tasks with their IDs
2. Find the task they're referring to by matching the description
3. Extract the task_id from the list_tasks result
4. IMMEDIATELY call update_task with the correct task_id and new description/priority
5. Do NOT ask for confirmation - just perform the update
6. NEVER guess or make up a task_id - always get it from list_tasks first

When a user asks to LIST tasks:
- Call list_tasks with no parameters
- Present results in a readable format

When a user asks to COMPLETE/DELETE a task:
- FIRST call list_tasks to get all current tasks with their IDs
- Find the task they're referring to:
  - If they say "task 3", that means the 3rd task in the list
  - If they mention a description like "walking", find the task with that description
  - Use conversation history to resolve references
- Extract the task_id from the list_tasks result
- Then immediately call complete_task or delete_task with the correct task_id
- Do NOT ask for confirmation - just perform the action

CONVERSATION HISTORY USAGE:
- Review the full conversation history to understand context
- Use it to resolve pronouns and references
- Remember what tasks have been discussed
- Extract task IDs from previous successful operations

Remember: Task descriptions MUST NOT be empty. Always extract meaningful content from the user's message. Be proactive and complete operations in a single turn when possible. When users reference tasks by number (like "task 3"), count the position in the list_tasks result."""

    def _execute_tool_calls(
        self,
        user_id: UUID,
        tool_calls: List[Any],
    ) -> List[Dict[str, Any]]:
        """Execute MCP tool calls and return results.
        
        Args:
            user_id: ID of the user
            tool_calls: Tool calls from OpenAI response
            
        Returns:
            list: Results of tool executions
            
        **Validates: Requirements 5.1, 5.2, 5.5**
        """
        results = []
        
        for tool_call in tool_calls:
            try:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Execute the appropriate tool
                if tool_name == "add_task":
                    result = self.mcp_server.add_task(
                        user_id=user_id,
                        description=tool_args.get("description"),
                        priority=tool_args.get("priority", "Medium"),
                    )
                    results.append({
                        "tool": tool_name,
                        "status": "success",
                        "result": result,
                    })
                    
                elif tool_name == "list_tasks":
                    result = self.mcp_server.list_tasks(user_id=user_id)
                    results.append({
                        "tool": tool_name,
                        "status": "success",
                        "result": result,
                    })
                    
                elif tool_name == "complete_task":
                    result = self.mcp_server.complete_task(
                        user_id=user_id,
                        task_id=tool_args.get("task_id"),
                    )
                    results.append({
                        "tool": tool_name,
                        "status": "success",
                        "result": result,
                    })
                    
                elif tool_name == "delete_task":
                    result = self.mcp_server.delete_task(
                        user_id=user_id,
                        task_id=tool_args.get("task_id"),
                    )
                    results.append({
                        "tool": tool_name,
                        "status": "success",
                        "result": result,
                    })
                    
                elif tool_name == "update_task":
                    result = self.mcp_server.update_task(
                        user_id=user_id,
                        task_id=tool_args.get("task_id"),
                        description=tool_args.get("description"),
                        priority=tool_args.get("priority"),
                    )
                    results.append({
                        "tool": tool_name,
                        "status": "success",
                        "result": result,
                    })
                    
            except Exception as e:
                results.append({
                    "tool": tool_call.function.name,
                    "status": "error",
                    "error": str(e),
                })
        
        return results

    def _generate_final_response(
        self,
        assistant_content: Optional[str],
        tool_results: List[Dict[str, Any]],
    ) -> str:
        """Generate final response with tool results.
        
        Args:
            assistant_content: Content from assistant message
            tool_results: Results from tool executions
            
        Returns:
            str: Final response to user
            
        **Validates: Requirements 5.1, 5.2, 5.5**
        """
        # If there's assistant content, use it as the base
        if assistant_content:
            response = assistant_content
        else:
            response = ""
        
        # Add tool results if any
        if tool_results:
            # Check if there are any errors
            errors = [r for r in tool_results if r["status"] == "error"]
            successes = [r for r in tool_results if r["status"] == "success"]
            
            if errors:
                if response:
                    response += "\n\n"
                response += "I encountered some errors:\n"
                for error in errors:
                    response += f"- {error['tool']}: {error['error']}\n"
            
            # If no assistant content but we have successful tool results, generate a summary
            if not assistant_content and successes:
                if response:
                    response += "\n\n"
                response += "I've completed the following operations:\n"
                for result in successes:
                    tool_name = result["tool"]
                    if tool_name == "add_task":
                        task = result["result"]
                        response += f"✓ Added task: {task['description']} (Priority: {task['priority']})\n"
                    elif tool_name == "list_tasks":
                        tasks = result["result"]
                        if tasks:
                            response += f"✓ Found {len(tasks)} task(s):\n"
                            for task in tasks:
                                status = "✓" if task["completed"] else "○"
                                response += f"  {status} {task['description']} (Priority: {task['priority']})\n"
                        else:
                            response += "✓ You have no tasks.\n"
                    elif tool_name == "complete_task":
                        task = result["result"]
                        status = "completed" if task["completed"] else "marked as incomplete"
                        response += f"✓ Task marked as {status}: {task['description']}\n"
                    elif tool_name == "delete_task":
                        response += f"✓ Task deleted successfully\n"
                    elif tool_name == "update_task":
                        task = result["result"]
                        response += f"✓ Updated task: {task['description']} (Priority: {task['priority']})\n"
        
        # If still no response, provide a default
        if not response:
            response = "I didn't quite understand that. Could you rephrase your request?"
        
        return response
