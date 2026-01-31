"""Property-based tests for the Todo application using Hypothesis."""

from hypothesis import given, strategies as st, assume, settings, HealthCheck
from src.task_list import TaskList


class TestTaskIDUniqueness:
    """Property 15: Task ID Uniqueness Is Maintained.
    
    Validates: Requirements 7.2
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_all_task_ids_are_unique(self, descriptions):
        """For any sequence of add and delete operations, all remaining tasks
        should have unique task_ids with no duplicates.
        
        **Validates: Requirements 7.2**
        """
        task_list = TaskList()
        
        # Add all tasks
        added_ids = []
        for desc in descriptions:
            task = task_list.add_task(desc)
            added_ids.append(task.task_id)
        
        # Verify all added IDs are unique
        assert len(added_ids) == len(set(added_ids)), "Added task IDs are not unique"
        
        # Get all tasks and verify their IDs are unique
        all_tasks = task_list.get_all_tasks()
        task_ids = [task.task_id for task in all_tasks]
        
        assert len(task_ids) == len(set(task_ids)), "Task IDs in list are not unique"
        assert len(task_ids) == len(descriptions), "Task count mismatch"

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1),
            min_size=2,
            max_size=30,
        ),
        delete_indices=st.lists(st.integers(min_value=0), max_size=10),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_uniqueness_maintained_after_deletions(self, descriptions, delete_indices):
        """For any sequence of add and delete operations, all remaining tasks
        should have unique task_ids with no duplicates.
        
        **Validates: Requirements 7.2**
        """
        task_list = TaskList()
        
        # Add all tasks
        added_tasks = []
        for desc in descriptions:
            task = task_list.add_task(desc)
            added_tasks.append(task)
        
        # Delete some tasks (filter to valid indices)
        valid_indices = [i for i in delete_indices if i < len(added_tasks)]
        for idx in sorted(set(valid_indices), reverse=True):
            task_list.delete_task(added_tasks[idx].task_id)
        
        # Verify remaining task IDs are unique
        remaining_tasks = task_list.get_all_tasks()
        task_ids = [task.task_id for task in remaining_tasks]
        
        assert len(task_ids) == len(set(task_ids)), "Task IDs are not unique after deletions"
        assert len(task_ids) == len(descriptions) - len(set(valid_indices)), "Task count mismatch"


class TestTaskAddition:
    """Property 1: Task Addition Creates Unique IDs.
    
    Validates: Requirements 1.1, 7.2
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_task_addition_creates_unique_ids(self, descriptions):
        """For any valid task description, adding it to the task list should result
        in a task with a unique task_id that does not match any existing task_id.
        
        **Validates: Requirements 1.1, 7.2**
        """
        task_list = TaskList()
        added_ids = set()
        
        for desc in descriptions:
            task = task_list.add_task(desc)
            assert task.task_id not in added_ids, "Task ID is not unique"
            added_ids.add(task.task_id)
        
        # Verify all tasks in list have unique IDs
        all_tasks = task_list.get_all_tasks()
        all_ids = [task.task_id for task in all_tasks]
        assert len(all_ids) == len(set(all_ids)), "Task IDs in list are not unique"


class TestNewTasksStartIncomplete:
    """Property 2: New Tasks Start Incomplete.
    
    Validates: Requirements 1.2
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_new_tasks_start_incomplete(self, descriptions):
        """For any newly added task, the task's completion status should be False.
        
        **Validates: Requirements 1.2**
        """
        task_list = TaskList()
        
        for desc in descriptions:
            task = task_list.add_task(desc)
            assert task.completed is False, "New task should start incomplete"


class TestInvalidDescriptionsRejected:
    """Property 3: Invalid Descriptions Are Rejected.
    
    Validates: Requirements 1.3
    """

    @given(st.just(""))
    def test_empty_description_rejected(self, desc):
        """For any empty string, attempting to add it should be rejected.
        
        **Validates: Requirements 1.3**
        """
        task_list = TaskList()
        
        try:
            task_list.add_task(desc)
            assert False, "Should have raised ValueError for empty description"
        except ValueError as e:
            assert "Description cannot be empty" in str(e)

    @given(st.text(alphabet=" \t\n\r", min_size=1))
    def test_whitespace_only_description_rejected(self, desc):
        """For any whitespace-only string, attempting to add it should be rejected.
        
        **Validates: Requirements 1.3**
        """
        task_list = TaskList()
        
        try:
            task_list.add_task(desc)
            assert False, "Should have raised ValueError for whitespace-only description"
        except ValueError as e:
            assert "Description cannot be empty" in str(e)


class TestDefaultPriorityIsMedium:
    """Property 4: Default Priority Is Medium.
    
    Validates: Requirements 1.5
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1),
            min_size=1,
            max_size=30,
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_default_priority_is_medium(self, descriptions):
        """For any task added without an explicit priority, the task's priority
        should be "Medium".
        
        **Validates: Requirements 1.5**
        """
        task_list = TaskList()
        
        for desc in descriptions:
            task = task_list.add_task(desc)  # No priority specified
            assert task.priority == "Medium", "Default priority should be Medium"


class TestTaskDeletion:
    """Property 5: Task Deletion Removes Task.
    
    Validates: Requirements 2.1
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_task_deletion_removes_task(self, descriptions):
        """For any task in the task list, deleting it by task_id should result
        in the task no longer appearing in the list.
        
        **Validates: Requirements 2.1**
        """
        task_list = TaskList()
        added_tasks = []
        
        for desc in descriptions:
            task = task_list.add_task(desc)
            added_tasks.append(task)
        
        # Delete each task and verify it's removed
        for task in added_tasks:
            task_list.delete_task(task.task_id)
            remaining = task_list.get_all_tasks()
            remaining_ids = [t.task_id for t in remaining]
            assert task.task_id not in remaining_ids, "Deleted task still in list"


class TestInvalidTaskIDsRejectedOnDelete:
    """Property 6: Invalid Task IDs Are Rejected on Delete.
    
    Validates: Requirements 2.2
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        ),
        invalid_id=st.integers(min_value=1000, max_value=9999),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_invalid_task_ids_rejected_on_delete(self, descriptions, invalid_id):
        """For any non-existent task_id, attempting to delete it should be rejected,
        and the task list should remain unchanged.
        
        **Validates: Requirements 2.2**
        """
        task_list = TaskList()
        
        for desc in descriptions:
            task_list.add_task(desc)
        
        initial_count = len(task_list.get_all_tasks())
        
        try:
            task_list.delete_task(invalid_id)
            assert False, "Should have raised ValueError for non-existent task_id"
        except ValueError as e:
            assert "Task not found" in str(e)
        
        # Verify list unchanged
        assert len(task_list.get_all_tasks()) == initial_count, "List was modified after failed delete"


class TestTaskDescriptionUpdate:
    """Property 7: Task Description Update Persists.
    
    Validates: Requirements 3.1
    """

    @given(
        original_desc=st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
        new_desc=st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_task_description_update_persists(self, original_desc, new_desc):
        """For any task in the task list and any valid new description, updating
        the task's description should result in the task having the new description.
        
        **Validates: Requirements 3.1**
        """
        task_list = TaskList()
        task_list.add_task(original_desc)
        
        updated = task_list.update_task(1, description=new_desc)
        
        assert updated.description == new_desc.strip(), "Description not updated"
        assert task_list.get_task(1).description == new_desc.strip(), "Description not persisted"


class TestTaskPriorityUpdate:
    """Property 8: Task Priority Update Persists.
    
    Validates: Requirements 3.2
    """

    @given(
        desc=st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
        new_priority=st.sampled_from(["High", "Medium", "Low"]),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_task_priority_update_persists(self, desc, new_priority):
        """For any task in the task list and any valid priority value, updating
        the task's priority should result in the task having the new priority.
        
        **Validates: Requirements 3.2**
        """
        task_list = TaskList()
        task_list.add_task(desc, priority="Low")
        
        updated = task_list.update_task(1, priority=new_priority)
        
        assert updated.priority == new_priority, "Priority not updated"
        assert task_list.get_task(1).priority == new_priority, "Priority not persisted"


class TestInvalidTaskIDsRejectedOnUpdate:
    """Property 9: Invalid Task IDs Are Rejected on Update.
    
    Validates: Requirements 3.3
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        ),
        invalid_id=st.integers(min_value=1000, max_value=9999),
        new_desc=st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_invalid_task_ids_rejected_on_update(self, descriptions, invalid_id, new_desc):
        """For any non-existent task_id, attempting to update it should be rejected,
        and the task list should remain unchanged.
        
        **Validates: Requirements 3.3**
        """
        task_list = TaskList()
        
        for desc in descriptions:
            task_list.add_task(desc)
        
        initial_tasks = task_list.get_all_tasks()
        
        try:
            task_list.update_task(invalid_id, description=new_desc)
            assert False, "Should have raised ValueError for non-existent task_id"
        except ValueError as e:
            assert "Task not found" in str(e)
        
        # Verify list unchanged
        final_tasks = task_list.get_all_tasks()
        assert len(final_tasks) == len(initial_tasks), "Task count changed"


class TestInvalidDescriptionsRejectedOnUpdate:
    """Property 10: Invalid Descriptions Are Rejected on Update.
    
    Validates: Requirements 3.4
    """

    @given(st.just(""))
    def test_empty_description_rejected_on_update(self, empty_desc):
        """For any empty string, attempting to update with it should be rejected.
        
        **Validates: Requirements 3.4**
        """
        task_list = TaskList()
        task_list.add_task("Original")
        
        try:
            task_list.update_task(1, description=empty_desc)
            assert False, "Should have raised ValueError for empty description"
        except ValueError as e:
            assert "Description cannot be empty" in str(e)

    @given(st.text(alphabet=" \t\n\r", min_size=1))
    def test_whitespace_only_description_rejected_on_update(self, whitespace_desc):
        """For any whitespace-only string, attempting to update with it should be rejected.
        
        **Validates: Requirements 3.4**
        """
        task_list = TaskList()
        task_list.add_task("Original")
        
        try:
            task_list.update_task(1, description=whitespace_desc)
            assert False, "Should have raised ValueError for whitespace-only description"
        except ValueError as e:
            assert "Description cannot be empty" in str(e)


class TestCompletionToggle:
    """Property 12: Completion Status Toggle Is Idempotent Round-Trip.
    
    Validates: Requirements 5.1
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_completion_toggle_is_idempotent_round_trip(self, descriptions):
        """For any task in the task list, toggling the completion status twice
        should return the task to its original completion status.
        
        **Validates: Requirements 5.1**
        """
        task_list = TaskList()
        
        for desc in descriptions:
            task = task_list.add_task(desc)
            original_status = task.completed
            
            # Toggle twice
            task_list.toggle_completion(task.task_id)
            task_list.toggle_completion(task.task_id)
            
            # Should be back to original
            final_task = task_list.get_task(task.task_id)
            assert final_task.completed == original_status, "Toggle is not idempotent"


class TestInvalidTaskIDsRejectedOnToggle:
    """Property 13: Invalid Task IDs Are Rejected on Toggle.
    
    Validates: Requirements 5.2
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        ),
        invalid_id=st.integers(min_value=1000, max_value=9999),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_invalid_task_ids_rejected_on_toggle(self, descriptions, invalid_id):
        """For any non-existent task_id, attempting to toggle its completion status
        should be rejected, and the task list should remain unchanged.
        
        **Validates: Requirements 5.2**
        """
        task_list = TaskList()
        
        for desc in descriptions:
            task_list.add_task(desc)
        
        initial_tasks = task_list.get_all_tasks()
        
        try:
            task_list.toggle_completion(invalid_id)
            assert False, "Should have raised ValueError for non-existent task_id"
        except ValueError as e:
            assert "Task not found" in str(e)
        
        # Verify list unchanged
        final_tasks = task_list.get_all_tasks()
        assert len(final_tasks) == len(initial_tasks), "Task count changed"



class TestInsertionOrderPreservation:
    """Property 11: Tasks Display in Insertion Order.
    
    Validates: Requirements 4.4
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_tasks_display_in_insertion_order(self, descriptions):
        """For any sequence of tasks added to the task list, retrieving all tasks
        should return them in the same order they were added.
        
        **Validates: Requirements 4.4**
        """
        task_list = TaskList()
        
        for desc in descriptions:
            task_list.add_task(desc)
        
        all_tasks = task_list.get_all_tasks()
        
        # Verify order matches insertion order (accounting for whitespace stripping)
        for i, desc in enumerate(descriptions):
            assert all_tasks[i].description == desc.strip(), f"Task at index {i} is out of order"


class TestFailedOperationsPreserveState:
    """Property 14: Failed Operations Preserve State.
    
    Validates: Requirements 7.1, 7.3
    """

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_failed_add_preserves_state(self, descriptions):
        """For any failed add operation (invalid description), the task list
        should remain in the same state as before the operation.
        
        **Validates: Requirements 7.1, 7.3**
        """
        task_list = TaskList()
        
        # Add valid tasks
        for desc in descriptions:
            task_list.add_task(desc)
        
        initial_count = len(task_list.get_all_tasks())
        initial_tasks = [t.description for t in task_list.get_all_tasks()]
        
        # Try to add invalid task
        try:
            task_list.add_task("")
        except ValueError:
            pass
        
        # Verify state unchanged
        final_count = len(task_list.get_all_tasks())
        final_tasks = [t.description for t in task_list.get_all_tasks()]
        
        assert final_count == initial_count, "Task count changed after failed add"
        assert final_tasks == initial_tasks, "Task list changed after failed add"

    @given(
        descriptions=st.lists(
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=30,
        ),
        invalid_id=st.integers(min_value=1000, max_value=9999),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_failed_delete_preserves_state(self, descriptions, invalid_id):
        """For any failed delete operation (invalid task_id), the task list
        should remain in the same state as before the operation.
        
        **Validates: Requirements 7.1, 7.3**
        """
        task_list = TaskList()
        
        # Add valid tasks
        for desc in descriptions:
            task_list.add_task(desc)
        
        initial_count = len(task_list.get_all_tasks())
        initial_tasks = [t.description for t in task_list.get_all_tasks()]
        
        # Try to delete invalid task
        try:
            task_list.delete_task(invalid_id)
        except ValueError:
            pass
        
        # Verify state unchanged
        final_count = len(task_list.get_all_tasks())
        final_tasks = [t.description for t in task_list.get_all_tasks()]
        
        assert final_count == initial_count, "Task count changed after failed delete"
        assert final_tasks == initial_tasks, "Task list changed after failed delete"
