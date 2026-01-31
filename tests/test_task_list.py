"""Unit tests for the TaskList model."""

import pytest
from src.task_list import TaskList
from src.task import Task


class TestTaskListCreation:
    """Test TaskList initialization."""

    def test_empty_task_list_creation(self):
        """Test creating an empty task list."""
        task_list = TaskList()
        
        assert task_list.is_empty() is True
        assert len(task_list.get_all_tasks()) == 0


class TestTaskListAddTask:
    """Test adding tasks to the list."""

    def test_add_single_task(self):
        """Test adding a single task."""
        task_list = TaskList()
        task = task_list.add_task("Buy groceries")
        
        assert task.task_id == 1
        assert task.description == "Buy groceries"
        assert task.priority == "Medium"
        assert task.completed is False
        assert task_list.is_empty() is False

    def test_add_task_with_priority(self):
        """Test adding a task with specified priority."""
        task_list = TaskList()
        task = task_list.add_task("Urgent task", priority="High")
        
        assert task.priority == "High"

    def test_add_multiple_tasks_generates_unique_ids(self):
        """Test that multiple tasks get unique IDs."""
        task_list = TaskList()
        task1 = task_list.add_task("Task 1")
        task2 = task_list.add_task("Task 2")
        task3 = task_list.add_task("Task 3")
        
        assert task1.task_id == 1
        assert task2.task_id == 2
        assert task3.task_id == 3
        assert len(task_list.get_all_tasks()) == 3

    def test_add_task_with_empty_description_raises_error(self):
        """Test that adding a task with empty description raises ValueError."""
        task_list = TaskList()
        
        with pytest.raises(ValueError, match="Description cannot be empty"):
            task_list.add_task("")

    def test_add_task_with_whitespace_description_raises_error(self):
        """Test that adding a task with whitespace-only description raises ValueError."""
        task_list = TaskList()
        
        with pytest.raises(ValueError, match="Description cannot be empty"):
            task_list.add_task("   ")

    def test_add_task_with_invalid_priority_raises_error(self):
        """Test that adding a task with invalid priority raises ValueError."""
        task_list = TaskList()
        
        with pytest.raises(ValueError, match="Priority must be"):
            task_list.add_task("Task", priority="Urgent")

    def test_add_task_strips_whitespace_from_description(self):
        """Test that description whitespace is stripped."""
        task_list = TaskList()
        task = task_list.add_task("  Buy milk  ")
        
        assert task.description == "Buy milk"


class TestTaskListDeleteTask:
    """Test deleting tasks from the list."""

    def test_delete_existing_task(self):
        """Test deleting an existing task."""
        task_list = TaskList()
        task_list.add_task("Task 1")
        task_list.add_task("Task 2")
        
        deleted = task_list.delete_task(1)
        
        assert deleted.task_id == 1
        assert len(task_list.get_all_tasks()) == 1

    def test_delete_nonexistent_task_raises_error(self):
        """Test that deleting a non-existent task raises ValueError."""
        task_list = TaskList()
        
        with pytest.raises(ValueError, match="Task not found"):
            task_list.delete_task(999)

    def test_delete_task_maintains_insertion_order(self):
        """Test that deletion maintains insertion order of remaining tasks."""
        task_list = TaskList()
        task_list.add_task("Task 1")
        task_list.add_task("Task 2")
        task_list.add_task("Task 3")
        
        task_list.delete_task(2)
        
        remaining = task_list.get_all_tasks()
        assert len(remaining) == 2
        assert remaining[0].task_id == 1
        assert remaining[1].task_id == 3


class TestTaskListUpdateTask:
    """Test updating tasks in the list."""

    def test_update_task_description(self):
        """Test updating a task's description."""
        task_list = TaskList()
        task_list.add_task("Original description")
        
        updated = task_list.update_task(1, description="Updated description")
        
        assert updated.description == "Updated description"
        assert task_list.get_task(1).description == "Updated description"

    def test_update_task_priority(self):
        """Test updating a task's priority."""
        task_list = TaskList()
        task_list.add_task("Task", priority="Low")
        
        updated = task_list.update_task(1, priority="High")
        
        assert updated.priority == "High"
        assert task_list.get_task(1).priority == "High"

    def test_update_task_both_fields(self):
        """Test updating both description and priority."""
        task_list = TaskList()
        task_list.add_task("Original", priority="Low")
        
        updated = task_list.update_task(
            1,
            description="Updated",
            priority="High",
        )
        
        assert updated.description == "Updated"
        assert updated.priority == "High"

    def test_update_nonexistent_task_raises_error(self):
        """Test that updating a non-existent task raises ValueError."""
        task_list = TaskList()
        
        with pytest.raises(ValueError, match="Task not found"):
            task_list.update_task(999, description="New")

    def test_update_with_empty_description_raises_error(self):
        """Test that updating with empty description raises ValueError."""
        task_list = TaskList()
        task_list.add_task("Original")
        
        with pytest.raises(ValueError, match="Description cannot be empty"):
            task_list.update_task(1, description="")

    def test_update_with_invalid_priority_raises_error(self):
        """Test that updating with invalid priority raises ValueError."""
        task_list = TaskList()
        task_list.add_task("Task")
        
        with pytest.raises(ValueError, match="Priority must be"):
            task_list.update_task(1, priority="Invalid")

    def test_update_strips_whitespace_from_description(self):
        """Test that description whitespace is stripped on update."""
        task_list = TaskList()
        task_list.add_task("Original")
        
        task_list.update_task(1, description="  Updated  ")
        
        assert task_list.get_task(1).description == "Updated"


class TestTaskListGetTask:
    """Test retrieving individual tasks."""

    def test_get_existing_task(self):
        """Test retrieving an existing task."""
        task_list = TaskList()
        task_list.add_task("Test task")
        
        task = task_list.get_task(1)
        
        assert task.task_id == 1
        assert task.description == "Test task"

    def test_get_nonexistent_task_raises_error(self):
        """Test that getting a non-existent task raises ValueError."""
        task_list = TaskList()
        
        with pytest.raises(ValueError, match="Task not found"):
            task_list.get_task(999)


class TestTaskListGetAllTasks:
    """Test retrieving all tasks."""

    def test_get_all_tasks_empty_list(self):
        """Test getting all tasks from empty list."""
        task_list = TaskList()
        
        tasks = task_list.get_all_tasks()
        
        assert tasks == []

    def test_get_all_tasks_maintains_insertion_order(self):
        """Test that get_all_tasks returns tasks in insertion order."""
        task_list = TaskList()
        task_list.add_task("First")
        task_list.add_task("Second")
        task_list.add_task("Third")
        
        tasks = task_list.get_all_tasks()
        
        assert len(tasks) == 3
        assert tasks[0].description == "First"
        assert tasks[1].description == "Second"
        assert tasks[2].description == "Third"

    def test_get_all_tasks_after_deletion(self):
        """Test that get_all_tasks reflects deletions."""
        task_list = TaskList()
        task_list.add_task("First")
        task_list.add_task("Second")
        task_list.add_task("Third")
        
        task_list.delete_task(2)
        
        tasks = task_list.get_all_tasks()
        assert len(tasks) == 2
        assert tasks[0].description == "First"
        assert tasks[1].description == "Third"


class TestTaskListToggleCompletion:
    """Test toggling task completion status."""

    def test_toggle_incomplete_to_complete(self):
        """Test toggling an incomplete task to complete."""
        task_list = TaskList()
        task_list.add_task("Task")
        
        updated = task_list.toggle_completion(1)
        
        assert updated.completed is True
        assert task_list.get_task(1).completed is True

    def test_toggle_complete_to_incomplete(self):
        """Test toggling a complete task to incomplete."""
        task_list = TaskList()
        task_list.add_task("Task")
        task_list.toggle_completion(1)
        
        updated = task_list.toggle_completion(1)
        
        assert updated.completed is False

    def test_toggle_nonexistent_task_raises_error(self):
        """Test that toggling a non-existent task raises ValueError."""
        task_list = TaskList()
        
        with pytest.raises(ValueError, match="Task not found"):
            task_list.toggle_completion(999)


class TestTaskListIsEmpty:
    """Test checking if task list is empty."""

    def test_is_empty_on_new_list(self):
        """Test that new list is empty."""
        task_list = TaskList()
        
        assert task_list.is_empty() is True

    def test_is_empty_after_adding_task(self):
        """Test that list is not empty after adding task."""
        task_list = TaskList()
        task_list.add_task("Task")
        
        assert task_list.is_empty() is False

    def test_is_empty_after_deleting_all_tasks(self):
        """Test that list is empty after deleting all tasks."""
        task_list = TaskList()
        task_list.add_task("Task")
        task_list.delete_task(1)
        
        assert task_list.is_empty() is True
