"""Task schemas."""

from pydantic import BaseModel, field_serializer
from datetime import datetime
from typing import Optional
from uuid import UUID


class TaskCreate(BaseModel):
    """Request schema for creating a task."""

    description: str
    priority: str = "Medium"


class TaskUpdate(BaseModel):
    """Request schema for updating a task."""

    description: Optional[str] = None
    priority: Optional[str] = None


class TaskResponse(BaseModel):
    """Response schema for task endpoints."""

    id: UUID
    description: str
    completed: bool
    priority: str
    created_at: datetime

    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        return str(value)

    class Config:
        from_attributes = True
