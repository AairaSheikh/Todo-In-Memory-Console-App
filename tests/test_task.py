"""Unit tests for the Task model."""

import pytest
from src.task import Task


class TestTaskCreation:
    """Test Task creation with valid inputs."""

    def test_task_creation_with_defaults(self):
        """Test creating a task with default values."""
        task = Task(task_id=1, description="Buy groceries")
        
        assert task.task_id == 1
        assert task.description == "Buy groceries"
        assert task.priority == "Medium"
        assert task.completed is False
        assert task.created_at is not None

    def test_task_creation_with_all_fields(self):
        """Test creating a task with all fields specified."""
        task = Task(
            task_id=2,
            description="Complete project",
            priority="High",
            completed=False,
        )
        
        assert task.task_id == 2
        assert task.description == "Complete project"
        assert task.priority == "High"
        assert task.completed is False

    def test_task_creation_with_completed_true(self):
        """Test creating a task that is already completed."""
        task = Task(
            task_id=3,
            description="Finished task",
            completed=True,
        )
        
        assert task.completed is True

    def test_task_creation_with_low_priority(self):
        """Test creating a task with low priority."""
        task = Task(
            task_id=4,
            description="Low priority task",
            priority="Low",
        )
        
        assert task.priority == "Low"


class TestTaskFieldAccess:
    """Test accessing and modifying task fields."""

    def test_modify_description(self):
        """Test modifying task description."""
        task = Task(task_id=1, description="Original")
        task.description = "Updated"
        
        assert task.description == "Updated"

    def test_modify_priority(self):
        """Test modifying task priority."""
        task = Task(task_id=1, description="Test", priority="Low")
        task.priority = "High"
        
        assert task.priority == "High"

    def test_modify_completed_status(self):
        """Test modifying task completion status."""
        task = Task(task_id=1, description="Test", completed=False)
        task.completed = True
        
        assert task.completed is True

    def test_toggle_completed_status(self):
        """Test toggling task completion status."""
        task = Task(task_id=1, description="Test", completed=False)
        task.completed = not task.completed
        
        assert task.completed is True
        
        task.completed = not task.completed
        assert task.completed is False


class TestTaskRepresentation:
    """Test task string representations."""

    def test_repr_incomplete_task(self):
        """Test __repr__ for incomplete task."""
        task = Task(task_id=1, description="Test task", priority="Medium")
        repr_str = repr(task)
        
        assert "id=1" in repr_str
        assert "Test task" in repr_str
        assert "Medium" in repr_str
        assert "completed=○" in repr_str

    def test_repr_completed_task(self):
        """Test __repr__ for completed task."""
        task = Task(task_id=2, description="Done task", completed=True)
        repr_str = repr(task)
        
        assert "id=2" in repr_str
        assert "completed=✓" in repr_str

    def test_str_incomplete_task(self):
        """Test __str__ for incomplete task."""
        task = Task(task_id=1, description="Buy milk", priority="High")
        str_repr = str(task)
        
        assert "[1]" in str_repr
        assert "Buy milk" in str_repr
        assert "High" in str_repr
        assert "TODO" in str_repr

    def test_str_completed_task(self):
        """Test __str__ for completed task."""
        task = Task(task_id=2, description="Finished", completed=True)
        str_repr = str(task)
        
        assert "[2]" in str_repr
        assert "DONE" in str_repr
