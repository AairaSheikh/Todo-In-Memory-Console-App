"""Task model for the Todo application."""

from datetime import datetime


class Task:
    """Represents a single task with metadata.
    
    Attributes:
        task_id: Unique integer identifier for the task
        description: Non-empty string describing the task
        completed: Boolean flag indicating completion status (default: False)
        priority: Priority level from {High, Medium, Low} (default: Medium)
        created_at: Timestamp of task creation
    """

    def __init__(
        self,
        task_id: int,
        description: str,
        priority: str = "Medium",
        completed: bool = False,
    ):
        """Initialize a Task instance.
        
        Args:
            task_id: Unique identifier for the task
            description: Task description
            priority: Priority level (default: "Medium")
            completed: Completion status (default: False)
        """
        self.task_id = task_id
        self.description = description
        self.priority = priority
        self.completed = completed
        self.created_at = datetime.now()

    def __repr__(self) -> str:
        """Return a clear string representation of the task.
        
        Returns:
            Formatted string showing task details
        """
        status = "✓" if self.completed else "○"
        return (
            f"Task(id={self.task_id}, description='{self.description}', "
            f"priority={self.priority}, completed={status})"
        )

    def __str__(self) -> str:
        """Return a user-friendly string representation of the task.
        
        Returns:
            Formatted string for display
        """
        status = "✓ DONE" if self.completed else "○ TODO"
        return (
            f"[{self.task_id}] {self.description} | "
            f"Priority: {self.priority} | Status: {status}"
        )
