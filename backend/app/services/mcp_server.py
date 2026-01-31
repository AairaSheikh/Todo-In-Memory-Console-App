"""MCP Server for exposing task operations as tools for AI agents."""

from sqlalchemy.orm import Session
from app.services.task import TaskService
from app.models import Task
from uuid import UUID
from typing import List, Dict, Any, Optional


class MCPServer:
    """Exposes task operations as MCP tools for AI agent."""

    def __init__(self, db: Session, task_service: TaskService):
        """Initialize MCP server with database session and task service.
        
        Args:
            db: SQLAlchemy database session
            task_service: TaskService instance for task operations
        """
        self.db = db
        self.task_service = task_service

    def add_task(self, user_id: UUID, description: str, priority: str = "Medium") -> Dict[str, Any]:
        """Add a new task via MCP tool.
        
        Args:
            user_id: ID of the user
            description: Task description
            priority: Task priority (Low, Medium, High) - defaults to Medium
            
        Returns:
            dict: Created task with id, description, priority, completed status
            
        Raises:
            ValueError: If description is empty or priority is invalid
            
        **Validates: Requirements 3.1, 11.2**
        """
        if not description or not description.strip():
            raise ValueError("Task description cannot be empty")
        
        if priority not in ["Low", "Medium", "High"]:
            raise ValueError(f"Invalid priority: {priority}. Must be Low, Medium, or High")
        
        from app.schemas import TaskCreate
        task_create = TaskCreate(description=description.strip(), priority=priority)
        task = self.task_service.create_task(user_id=user_id, request=task_create)
        
        return {
            "id": str(task.id),
            "description": task.description,
            "priority": task.priority,
            "completed": task.completed,
            "created_at": task.created_at.isoformat(),
        }

    def list_tasks(self, user_id: UUID) -> List[Dict[str, Any]]:
        """List all tasks for a user via MCP tool.
        
        Args:
            user_id: ID of the user
            
        Returns:
            list: All tasks for the user with id, description, priority, completed status
            
        **Validates: Requirements 3.2, 11.1**
        """
        tasks = self.task_service.get_tasks(user_id=user_id)
        
        return [
            {
                "id": str(task.id),
                "description": task.description,
                "priority": task.priority,
                "completed": task.completed,
                "created_at": task.created_at.isoformat(),
            }
            for task in tasks
        ]

    def complete_task(self, user_id: UUID, task_id: str) -> Dict[str, Any]:
        """Mark a task as complete/incomplete via MCP tool.
        
        Args:
            user_id: ID of the user
            task_id: ID of the task to toggle
            
        Returns:
            dict: Updated task with new completed status
            
        Raises:
            ValueError: If task not found or user doesn't own the task
            
        **Validates: Requirements 3.3, 11.3**
        """
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise ValueError(f"Invalid task ID format: {task_id}")
        
        task = self.task_service.toggle_completion(
            user_id=user_id,
            task_id=task_uuid,
        )
        
        return {
            "id": str(task.id),
            "description": task.description,
            "priority": task.priority,
            "completed": task.completed,
            "created_at": task.created_at.isoformat(),
        }

    def delete_task(self, user_id: UUID, task_id: str) -> Dict[str, str]:
        """Delete a task via MCP tool.
        
        Args:
            user_id: ID of the user
            task_id: ID of the task to delete
            
        Returns:
            dict: Confirmation message
            
        Raises:
            ValueError: If task not found or user doesn't own the task
            
        **Validates: Requirements 3.4, 11.4**
        """
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise ValueError(f"Invalid task ID format: {task_id}")
        
        self.task_service.delete_task(
            user_id=user_id,
            task_id=task_uuid,
        )
        
        return {
            "status": "success",
            "message": f"Task {task_id} deleted successfully",
        }

    def update_task(
        self,
        user_id: UUID,
        task_id: str,
        description: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a task via MCP tool.
        
        Args:
            user_id: ID of the user
            task_id: ID of the task to update
            description: New task description (optional)
            priority: New task priority (optional)
            
        Returns:
            dict: Updated task with all fields
            
        Raises:
            ValueError: If task not found, user doesn't own the task, or invalid parameters
            
        **Validates: Requirements 3.5, 11.5**
        """
        try:
            task_uuid = UUID(task_id)
        except ValueError:
            raise ValueError(f"Invalid task ID format: {task_id}")
        
        if priority and priority not in ["Low", "Medium", "High"]:
            raise ValueError(f"Invalid priority: {priority}. Must be Low, Medium, or High")
        
        from app.schemas import TaskUpdate
        task_update = TaskUpdate(
            description=description.strip() if description else None,
            priority=priority,
        )
        task = self.task_service.update_task(
            user_id=user_id,
            task_id=task_uuid,
            request=task_update,
        )
        
        return {
            "id": str(task.id),
            "description": task.description,
            "priority": task.priority,
            "completed": task.completed,
            "created_at": task.created_at.isoformat(),
        }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get MCP tool definitions for the AI agent.
        
        Returns:
            list: Tool definitions with name, description, and input schema
        """
        return [
            {
                "name": "add_task",
                "description": "Add a new task to the user's task list",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "The task description",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["Low", "Medium", "High"],
                            "description": "Task priority (optional, defaults to Medium)",
                        },
                    },
                    "required": ["description"],
                },
            },
            {
                "name": "list_tasks",
                "description": "List all tasks for the user",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "complete_task",
                "description": "Mark a task as complete or incomplete",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to complete",
                        },
                    },
                    "required": ["task_id"],
                },
            },
            {
                "name": "delete_task",
                "description": "Delete a task from the user's task list",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to delete",
                        },
                    },
                    "required": ["task_id"],
                },
            },
            {
                "name": "update_task",
                "description": "Update a task's description or priority",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to update",
                        },
                        "description": {
                            "type": "string",
                            "description": "New task description (optional)",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["Low", "Medium", "High"],
                            "description": "New task priority (optional)",
                        },
                    },
                    "required": ["task_id"],
                },
            },
        ]
