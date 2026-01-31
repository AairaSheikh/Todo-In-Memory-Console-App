"""TaskList model for managing a collection of tasks."""

from typing import List, Dict
from src.task import Task


class TaskList:
    """Manages the in-memory collection of tasks.
    
    Maintains tasks in a dictionary for O(1) lookup and a list for insertion order.
    Provides methods to add, delete, update, and retrieve tasks.
    """

    def __init__(self):
        """Initialize an empty TaskList."""
        self._tasks: Dict[int, Task] = {}  # task_id -> Task mapping
        self._order: List[int] = []  # List of task_ids in insertion order
        self._next_id: int = 1  # Counter for generating unique task_ids

    def add_task(self, description: str, priority: str = "Medium") -> Task:
        """Add a new task to the list.
        
        Args:
            description: Task description (must not be empty or whitespace-only)
            priority: Priority level from {High, Medium, Low} (default: "Medium")
            
        Returns:
            The newly created Task with assigned task_id
            
        Raises:
            ValueError: If description is empty or whitespace-only
            ValueError: If priority is not in {High, Medium, Low}
        """
        # Validate description
        if not description or not description.strip():
            raise ValueError("Description cannot be empty or whitespace-only")
        
        # Validate priority
        valid_priorities = {"High", "Medium", "Low"}
        if priority not in valid_priorities:
            raise ValueError("Priority must be High, Medium, or Low")
        
        # Create new task with auto-incremented ID
        task_id = self._next_id
        task = Task(
            task_id=task_id,
            description=description.strip(),
            priority=priority,
            completed=False,
        )
        
        # Store task and track insertion order
        self._tasks[task_id] = task
        self._order.append(task_id)
        self._next_id += 1
        
        return task

    def delete_task(self, task_id: int) -> Task:
        """Delete a task from the list.
        
        Args:
            task_id: The ID of the task to delete
            
        Returns:
            The deleted Task
            
        Raises:
            ValueError: If task_id does not exist
        """
        if task_id not in self._tasks:
            raise ValueError("Task not found")
        
        # Remove from both dictionary and order list
        task = self._tasks.pop(task_id)
        self._order.remove(task_id)
        
        return task

    def update_task(
        self,
        task_id: int,
        description: str = None,
        priority: str = None,
    ) -> Task:
        """Update a task's fields.
        
        Args:
            task_id: The ID of the task to update
            description: New description (optional, must not be empty if provided)
            priority: New priority (optional, must be valid if provided)
            
        Returns:
            The updated Task
            
        Raises:
            ValueError: If task_id does not exist
            ValueError: If description is empty or whitespace-only
            ValueError: If priority is not in {High, Medium, Low}
        """
        if task_id not in self._tasks:
            raise ValueError("Task not found")
        
        task = self._tasks[task_id]
        
        # Validate and update description if provided
        if description is not None:
            if not description or not description.strip():
                raise ValueError("Description cannot be empty or whitespace-only")
            task.description = description.strip()
        
        # Validate and update priority if provided
        if priority is not None:
            valid_priorities = {"High", "Medium", "Low"}
            if priority not in valid_priorities:
                raise ValueError("Priority must be High, Medium, or Low")
            task.priority = priority
        
        return task

    def get_task(self, task_id: int) -> Task:
        """Retrieve a task by ID.
        
        Args:
            task_id: The ID of the task to retrieve
            
        Returns:
            The Task with the given task_id
            
        Raises:
            ValueError: If task_id does not exist
        """
        if task_id not in self._tasks:
            raise ValueError("Task not found")
        
        return self._tasks[task_id]

    def get_all_tasks(self) -> List[Task]:
        """Retrieve all tasks in insertion order.
        
        Returns:
            List of all tasks in the order they were added
        """
        return [self._tasks[task_id] for task_id in self._order]

    def toggle_completion(self, task_id: int) -> Task:
        """Toggle the completion status of a task.
        
        Args:
            task_id: The ID of the task to toggle
            
        Returns:
            The updated Task
            
        Raises:
            ValueError: If task_id does not exist
        """
        if task_id not in self._tasks:
            raise ValueError("Task not found")
        
        task = self._tasks[task_id]
        task.completed = not task.completed
        
        return task

    def is_empty(self) -> bool:
        """Check if the task list is empty.
        
        Returns:
            True if no tasks exist, False otherwise
        """
        return len(self._tasks) == 0
