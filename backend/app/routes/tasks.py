"""Task routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.schemas import TaskCreate, TaskUpdate, TaskResponse
from app.services import AuthenticationService, TaskService
from app.models import User

router = APIRouter(prefix="/api", tags=["tasks"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user from JWT token.
    
    Args:
        authorization: Authorization header with Bearer token
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    try:
        auth_service = AuthenticationService(db)
        user_id = auth_service.validate_token(token)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/{user_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    user_id: str,
    request: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new task.
    
    Args:
        user_id: User ID from path
        request: Task creation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created task
        
    Raises:
        HTTPException: If unauthorized or invalid data
    """
    # Verify user_id matches current user
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    
    try:
        task_service = TaskService(db)
        return task_service.create_task(current_user.id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{user_id}/tasks", response_model=list[TaskResponse])
async def get_tasks(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all tasks for a user.
    
    Args:
        user_id: User ID from path
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of tasks
        
    Raises:
        HTTPException: If unauthorized
    """
    # Verify user_id matches current user
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    
    task_service = TaskService(db)
    return task_service.get_tasks(current_user.id)


@router.get("/{user_id}/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    user_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific task.
    
    Args:
        user_id: User ID from path
        task_id: Task ID from path
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Task details
        
    Raises:
        HTTPException: If unauthorized or task not found
    """
    # Verify user_id matches current user
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    
    try:
        task_service = TaskService(db)
        return task_service.get_task(current_user.id, UUID(task_id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/{user_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    user_id: str,
    task_id: str,
    request: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a task.
    
    Args:
        user_id: User ID from path
        task_id: Task ID from path
        request: Task update request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated task
        
    Raises:
        HTTPException: If unauthorized, task not found, or invalid data
    """
    # Verify user_id matches current user
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    
    try:
        task_service = TaskService(db)
        return task_service.update_task(current_user.id, UUID(task_id), request)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{user_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    user_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a task.
    
    Args:
        user_id: User ID from path
        task_id: Task ID from path
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If unauthorized or task not found
    """
    # Verify user_id matches current user
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    
    try:
        task_service = TaskService(db)
        task_service.delete_task(current_user.id, UUID(task_id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch("/{user_id}/tasks/{task_id}/complete", response_model=TaskResponse)
async def toggle_task_completion(
    user_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle task completion status.
    
    Args:
        user_id: User ID from path
        task_id: Task ID from path
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated task
        
    Raises:
        HTTPException: If unauthorized or task not found
    """
    # Verify user_id matches current user
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    
    try:
        task_service = TaskService(db)
        return task_service.toggle_completion(current_user.id, UUID(task_id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
