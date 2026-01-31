"""Task service for task management."""

from sqlalchemy.orm import Session
from uuid import UUID
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate, TaskResponse


class TaskService:
    """Manages task CRUD operations and persistence."""

    def __init__(self, db: Session):
        """Initialize task service.
        
        Args:
            db: Database session
        """
        self.db = db

    def create_task(self, user_id: UUID, request: TaskCreate) -> TaskResponse:
        """Create a new task.
        
        Args:
            user_id: User ID who owns the task
            request: Task creation request
            
        Returns:
            Created task response
            
        Raises:
            ValueError: If description is invalid
        """
        # Validate description
        if not request.description or not request.description.strip():
            raise ValueError("Description cannot be empty or whitespace-only")
        
        # Validate priority
        valid_priorities = {"High", "Medium", "Low"}
        if request.priority not in valid_priorities:
            raise ValueError("Priority must be High, Medium, or Low")
        
        # Create task
        task = Task(
            user_id=user_id,
            description=request.description.strip(),
            priority=request.priority,
            completed=False,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return TaskResponse.from_orm(task)

    def get_tasks(self, user_id: UUID) -> list[TaskResponse]:
        """Get all tasks for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of task responses in creation order
        """
        tasks = self.db.query(Task).filter(Task.user_id == user_id).order_by(Task.created_at).all()
        return [TaskResponse.from_orm(task) for task in tasks]

    def get_task(self, user_id: UUID, task_id: UUID) -> TaskResponse:
        """Get a specific task.
        
        Args:
            user_id: User ID (for authorization)
            task_id: Task ID
            
        Returns:
            Task response
            
        Raises:
            ValueError: If task not found or unauthorized
        """
        task = self.db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if not task:
            raise ValueError("Task not found")
        
        return TaskResponse.from_orm(task)

    def update_task(self, user_id: UUID, task_id: UUID, request: TaskUpdate) -> TaskResponse:
        """Update a task.
        
        Args:
            user_id: User ID (for authorization)
            task_id: Task ID
            request: Task update request
            
        Returns:
            Updated task response
            
        Raises:
            ValueError: If task not found, unauthorized, or invalid data
        """
        task = self.db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if not task:
            raise ValueError("Task not found")
        
        # Update description if provided
        if request.description is not None:
            if not request.description or not request.description.strip():
                raise ValueError("Description cannot be empty or whitespace-only")
            task.description = request.description.strip()
        
        # Update priority if provided
        if request.priority is not None:
            valid_priorities = {"High", "Medium", "Low"}
            if request.priority not in valid_priorities:
                raise ValueError("Priority must be High, Medium, or Low")
            task.priority = request.priority
        
        self.db.commit()
        self.db.refresh(task)
        
        return TaskResponse.from_orm(task)

    def delete_task(self, user_id: UUID, task_id: UUID) -> None:
        """Delete a task.
        
        Args:
            user_id: User ID (for authorization)
            task_id: Task ID
            
        Raises:
            ValueError: If task not found or unauthorized
        """
        task = self.db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if not task:
            raise ValueError("Task not found")
        
        self.db.delete(task)
        self.db.commit()

    def toggle_completion(self, user_id: UUID, task_id: UUID) -> TaskResponse:
        """Toggle task completion status.
        
        Args:
            user_id: User ID (for authorization)
            task_id: Task ID
            
        Returns:
            Updated task response
            
        Raises:
            ValueError: If task not found or unauthorized
        """
        task = self.db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if not task:
            raise ValueError("Task not found")
        
        task.completed = not task.completed
        self.db.commit()
        self.db.refresh(task)
        
        return TaskResponse.from_orm(task)
