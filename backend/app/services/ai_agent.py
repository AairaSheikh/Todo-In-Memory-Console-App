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
            
            # Debug logging
            print(f"DEBUG: Formatted messages count: {len(formatted_messages)}")
            print(f"DEBUG: Tools available: {len(tools)}")
            print(f"DEBUG: Tool names: {[t['name'] for t in tools]}")
            print(f"DEBUG: First message (system prompt): {formatted_messages[0]['content'][:300]}...")
            
            # Format tools for OpenAI
            formatted_tools = [{"type": "function", "function": tool} for tool in tools]
            print(f"DEBUG: Formatted tools sample: {formatted_tools[0]}")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                tools=formatted_tools,
                tool_choice="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            # Parse response
            assistant_message = response.choices[0].message
            
            # Debug logging
            print(f"DEBUG: Response finish_reason: {response.choices[0].finish_reason}")
            print(f"DEBUG: Assistant message content: {assistant_message.content}")
            print(f"DEBUG: Tool calls count: {len(assistant_message.tool_calls) if assistant_message.tool_calls else 0}")
            if assistant_message.tool_calls:
                for tc in assistant_message.tool_calls:
                    print(f"DEBUG: Tool call - {tc.function.name}: {tc.function.arguments}")
            
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
        
        # Add current message with explicit instruction to use tools
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
        return """You are a task management assistant. Help users manage tasks through conversation.

CRITICAL: You MUST call tools for task operations. Do NOT just talk about what you would do - actually call the tools.

When user asks to:
- ADD a task: Call add_task with the description
- LIST tasks: Call list_tasks
- COMPLETE/MARK DONE a task: Call list_tasks first, then complete_task with the task UUID
- DELETE a task: Call list_tasks first, then delete_task with the task UUID  
- UPDATE/CHANGE a task: Call list_tasks first, then update_task with the task UUID

CRITICAL TASK ID EXTRACTION RULES:
1. When user says "task 1" or "task 2", they mean the position in the list
2. You MUST call list_tasks first to get the actual UUIDs
3. Extract the UUID from the "id" field of the task at that position
4. NEVER use the position number as the task_id - always use the full UUID string
5. Example: If user says "complete task 2", call list_tasks, find the 2nd task, extract its "id" field (UUID), then call complete_task with that UUID

After calling tools, provide a natural language response confirming what was done."""

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
            # BUT: Don't add summary if list_tasks was called (let assistant handle the formatting)
            if not assistant_content and successes:
                # Check if any of the results are from list_tasks
                has_list_tasks = any(r["tool"] == "list_tasks" for r in successes)
                
                if not has_list_tasks:
                    if response:
                        response += "\n\n"
                    response += "I've completed the following operations:\n"
                    for result in successes:
                        tool_name = result["tool"]
                        if tool_name == "add_task":
                            task = result["result"]
                            response += f"✓ Added task: {task['description']} (Priority: {task['priority']})\n"
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
