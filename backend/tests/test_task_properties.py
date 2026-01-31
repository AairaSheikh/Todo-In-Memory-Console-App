"""Property-based tests for task management."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from sqlalchemy.orm import Session
from app.services import TaskService, AuthenticationService
from app.schemas import TaskCreate, TaskUpdate, SignupRequest
from app.models import User, Task


class TestTaskCreationProperties:
    """Property-based tests for task creation."""

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
        priority=st.sampled_from(["High", "Medium", "Low"]),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_task_creation_persists_to_database(self, db: Session, email: str, password: str, description: str, priority: str):
        """Property 12: Task Creation Persists to Database.
        
        For any authenticated user and valid task description, creating a task
        should persist it to the database and return a 201 status with the created task.
        
        **Validates: Requirements 4.1, 4.4, 10.1**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Create task
        task_service = TaskService(db)
        request = TaskCreate(description=description.strip(), priority=priority)
        response = task_service.create_task(user_id, request)
        
        assert response.id is not None
        assert response.description == description.strip()
        assert response.priority == priority
        assert response.completed is False
        
        # Verify task persisted
        task = db.query(Task).filter(Task.id == response.id).first()
        assert task is not None

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        empty_description=st.just("") | st.text(alphabet=" \t\n\r", min_size=1),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_empty_description_task_rejected(self, db: Session, email: str, password: str, empty_description: str):
        """Property 13: Empty Description Task Rejected.
        
        For any empty or whitespace-only description, attempting to create a task
        with that description should be rejected with a 400 error.
        
        **Validates: Requirements 4.2**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Try to create task with empty description
        task_service = TaskService(db)
        request = TaskCreate(description=empty_description)
        
        with pytest.raises(ValueError, match="empty"):
            task_service.create_task(user_id, request)

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_default_priority_is_medium(self, db: Session, email: str, password: str, description: str):
        """Property 14: Default Priority Is Medium.
        
        For any task created without an explicit priority, the task should have
        a default priority of "Medium".
        
        **Validates: Requirements 4.3**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Create task without priority
        task_service = TaskService(db)
        request = TaskCreate(description=description.strip())
        response = task_service.create_task(user_id, request)
        
        assert response.priority == "Medium"


class TestTaskDeletionProperties:
    """Property-based tests for task deletion."""

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_task_deletion_removes_from_database(self, db: Session, email: str, password: str, description: str):
        """Property 24: Task Deletion Removes from Database.
        
        For any task belonging to an authenticated user, deleting that task
        should remove it from the database and return a 204 No Content status.
        
        **Validates: Requirements 8.1, 8.4**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Create task
        task_service = TaskService(db)
        create_request = TaskCreate(description=description.strip())
        created_task = task_service.create_task(user_id, create_request)
        task_id = created_task.id
        
        # Delete task
        task_service.delete_task(user_id, task_id)
        
        # Verify task was deleted
        with pytest.raises(ValueError, match="not found"):
            task_service.get_task(user_id, task_id)

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_non_existent_task_delete_returns_404(self, db: Session, email: str, password: str, description: str):
        """Property 25: Non-Existent Task Delete Returns 404.
        
        For any non-existent task ID, attempting to delete that task should
        return a 404 Not Found error.
        
        **Validates: Requirements 8.2**
        """
        from uuid import uuid4
        
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Try to delete non-existent task
        task_service = TaskService(db)
        fake_task_id = uuid4()
        
        with pytest.raises(ValueError, match="not found"):
            task_service.delete_task(user_id, fake_task_id)

    @given(
        email1=st.emails(),
        password1=st.text(min_size=8, max_size=100),
        email2=st.emails(),
        password2=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_cross_user_task_delete_rejected(self, db: Session, email1: str, password1: str, email2: str, password2: str, description: str):
        """Property 26: Cross-User Task Delete Rejected.
        
        For any two different users, attempting to delete one user's task
        as the other user should be rejected with a 403 Forbidden error.
        
        **Validates: Requirements 8.3, 12.4**
        """
        assume(email1 != email2)
        
        # Create two users
        auth_service = AuthenticationService(db)
        signup_request1 = SignupRequest(email=email1, password=password1)
        signup_response1 = auth_service.signup(signup_request1)
        user_id1 = signup_response1.user_id
        
        signup_request2 = SignupRequest(email=email2, password=password2)
        signup_response2 = auth_service.signup(signup_request2)
        user_id2 = signup_response2.user_id
        
        # User 1 creates a task
        task_service = TaskService(db)
        create_request = TaskCreate(description=description.strip())
        created_task = task_service.create_task(user_id1, create_request)
        
        # User 2 tries to delete User 1's task
        with pytest.raises(ValueError, match="not found"):
            task_service.delete_task(user_id2, created_task.id)


class TestTaskRetrievalProperties:
    """Property-based tests for task retrieval."""

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_single_task_retrieval_returns_correct_task(self, db: Session, email: str, password: str, description: str):
        """Property 19: Single Task Retrieval Returns Correct Task.
        
        For any task belonging to an authenticated user, retrieving that task
        by ID should return the correct task.
        
        **Validates: Requirements 6.1**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Create task
        task_service = TaskService(db)
        create_request = TaskCreate(description=description.strip())
        created_task = task_service.create_task(user_id, create_request)
        
        # Retrieve task
        retrieved_task = task_service.get_task(user_id, created_task.id)
        
        assert retrieved_task.id == created_task.id
        assert retrieved_task.description == description.strip()

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_non_existent_task_returns_404(self, db: Session, email: str, password: str):
        """Property 20: Non-Existent Task Returns 404.
        
        For any non-existent task ID, attempting to retrieve that task should
        return a 404 Not Found error.
        
        **Validates: Requirements 6.2**
        """
        from uuid import uuid4
        
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Try to retrieve non-existent task
        task_service = TaskService(db)
        fake_task_id = uuid4()
        
        with pytest.raises(ValueError, match="not found"):
            task_service.get_task(user_id, fake_task_id)

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        descriptions=st.lists(
            st.text(min_size=1).filter(lambda x: x.strip()),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_task_list_retrieval_returns_all_user_tasks(self, db: Session, email: str, password: str, descriptions: list):
        """Property 16: Task List Retrieval Returns All User Tasks.
        
        For any authenticated user, retrieving their task list should return
        all tasks belonging to that user.
        
        **Validates: Requirements 5.1, 5.3**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Create multiple tasks
        task_service = TaskService(db)
        for desc in descriptions:
            request = TaskCreate(description=desc.strip())
            task_service.create_task(user_id, request)
        
        # Retrieve tasks
        tasks = task_service.get_tasks(user_id)
        
        assert len(tasks) == len(descriptions)

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_empty_task_list_returns_empty_array(self, db: Session, email: str, password: str):
        """Property 17: Empty Task List Returns Empty Array.
        
        For any user with no tasks, retrieving their task list should return
        an empty array with a 200 status.
        
        **Validates: Requirements 5.2**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Retrieve tasks
        task_service = TaskService(db)
        tasks = task_service.get_tasks(user_id)
        
        assert len(tasks) == 0


class TestTaskUpdateProperties:
    """Property-based tests for task updates."""

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        original_description=st.text(min_size=1).filter(lambda x: x.strip()),
        new_description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_task_update_persists_changes(self, db: Session, email: str, password: str, original_description: str, new_description: str):
        """Property 21: Task Update Persists Changes.
        
        For any task belonging to an authenticated user and valid update data,
        updating the task should persist the changes to the database and return a 200 status.
        
        **Validates: Requirements 7.1, 7.2, 7.6**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Create task
        task_service = TaskService(db)
        create_request = TaskCreate(description=original_description.strip())
        created_task = task_service.create_task(user_id, create_request)
        
        # Update task
        update_request = TaskUpdate(description=new_description.strip())
        updated_task = task_service.update_task(user_id, created_task.id, update_request)
        
        assert updated_task.description == new_description.strip()
        
        # Verify persisted
        retrieved_task = task_service.get_task(user_id, created_task.id)
        assert retrieved_task.description == new_description.strip()

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
        empty_update=st.just("") | st.text(alphabet=" \t\n\r", min_size=1),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_invalid_description_update_rejected(self, db: Session, email: str, password: str, description: str, empty_update: str):
        """Property 22: Invalid Description Update Rejected.
        
        For any empty or whitespace-only description, attempting to update a task
        with that description should be rejected with a 400 error.
        
        **Validates: Requirements 7.3**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Create task
        task_service = TaskService(db)
        create_request = TaskCreate(description=description.strip())
        created_task = task_service.create_task(user_id, create_request)
        
        # Try to update with empty description
        update_request = TaskUpdate(description=empty_update)
        
        with pytest.raises(ValueError, match="empty"):
            task_service.update_task(user_id, created_task.id, update_request)

    @given(
        email1=st.emails(),
        password1=st.text(min_size=8, max_size=100),
        email2=st.emails(),
        password2=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
        new_description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_cross_user_task_update_rejected(self, db: Session, email1: str, password1: str, email2: str, password2: str, description: str, new_description: str):
        """Property 23: Cross-User Task Update Rejected.
        
        For any two different users, attempting to update one user's task
        as the other user should be rejected with a 403 Forbidden error.
        
        **Validates: Requirements 7.5, 12.3**
        """
        assume(email1 != email2)
        
        # Create two users
        auth_service = AuthenticationService(db)
        signup_request1 = SignupRequest(email=email1, password=password1)
        signup_response1 = auth_service.signup(signup_request1)
        user_id1 = signup_response1.user_id
        
        signup_request2 = SignupRequest(email=email2, password=password2)
        signup_response2 = auth_service.signup(signup_request2)
        user_id2 = signup_response2.user_id
        
        # User 1 creates a task
        task_service = TaskService(db)
        create_request = TaskCreate(description=description.strip())
        created_task = task_service.create_task(user_id1, create_request)
        
        # User 2 tries to update User 1's task
        update_request = TaskUpdate(description=new_description.strip())
        
        with pytest.raises(ValueError, match="not found"):
            task_service.update_task(user_id2, created_task.id, update_request)


class TestTaskCompletionProperties:
    """Property-based tests for task completion."""

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_task_completion_toggle_inverts_status(self, db: Session, email: str, password: str, description: str):
        """Property 27: Task Completion Toggle Inverts Status.
        
        For any task belonging to an authenticated user, toggling the completion
        status should invert the current status and persist to the database.
        
        **Validates: Requirements 9.1**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Create task
        task_service = TaskService(db)
        create_request = TaskCreate(description=description.strip())
        created_task = task_service.create_task(user_id, create_request)
        
        original_status = created_task.completed
        
        # Toggle completion
        toggled_task = task_service.toggle_completion(user_id, created_task.id)
        
        assert toggled_task.completed != original_status

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_completion_toggle_is_idempotent_round_trip(self, db: Session, email: str, password: str, description: str):
        """Property 28: Completion Toggle Is Idempotent Round-Trip.
        
        For any task, toggling the completion status twice should return the
        task to its original completion status.
        
        **Validates: Requirements 9.1**
        """
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Create task
        task_service = TaskService(db)
        create_request = TaskCreate(description=description.strip())
        created_task = task_service.create_task(user_id, create_request)
        
        original_status = created_task.completed
        
        # Toggle twice
        task_service.toggle_completion(user_id, created_task.id)
        final_task = task_service.toggle_completion(user_id, created_task.id)
        
        assert final_task.completed == original_status

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_non_existent_task_toggle_returns_404(self, db: Session, email: str, password: str):
        """Property 29: Non-Existent Task Toggle Returns 404.
        
        For any non-existent task ID, attempting to toggle its completion
        should return a 404 Not Found error.
        
        **Validates: Requirements 9.2**
        """
        from uuid import uuid4
        
        # Create user
        auth_service = AuthenticationService(db)
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        user_id = signup_response.user_id
        
        # Try to toggle non-existent task
        task_service = TaskService(db)
        fake_task_id = uuid4()
        
        with pytest.raises(ValueError, match="not found"):
            task_service.toggle_completion(user_id, fake_task_id)

    @given(
        email1=st.emails(),
        password1=st.text(min_size=8, max_size=100),
        email2=st.emails(),
        password2=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_cross_user_task_toggle_rejected(self, db: Session, email1: str, password1: str, email2: str, password2: str, description: str):
        """Property 30: Cross-User Task Toggle Rejected.
        
        For any two different users, attempting to toggle one user's task
        as the other user should be rejected with a 403 Forbidden error.
        
        **Validates: Requirements 9.3, 12.3**
        """
        assume(email1 != email2)
        
        # Create two users
        auth_service = AuthenticationService(db)
        signup_request1 = SignupRequest(email=email1, password=password1)
        signup_response1 = auth_service.signup(signup_request1)
        user_id1 = signup_response1.user_id
        
        signup_request2 = SignupRequest(email=email2, password=password2)
        signup_response2 = auth_service.signup(signup_request2)
        user_id2 = signup_response2.user_id
        
        # User 1 creates a task
        task_service = TaskService(db)
        create_request = TaskCreate(description=description.strip())
        created_task = task_service.create_task(user_id1, create_request)
        
        # User 2 tries to toggle User 1's task
        with pytest.raises(ValueError, match="not found"):
            task_service.toggle_completion(user_id2, created_task.id)


class TestAuthorizationProperties:
    """Property-based tests for authorization."""

    @given(
        email1=st.emails(),
        password1=st.text(min_size=8, max_size=100),
        email2=st.emails(),
        password2=st.text(min_size=8, max_size=100),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_cross_user_task_access_rejected(self, db: Session, email1: str, password1: str, email2: str, password2: str, description: str):
        """Property 18: Cross-User Task Access Rejected.
        
        For any two different users, attempting to retrieve one user's tasks
        as the other user should be rejected with a 403 Forbidden error.
        
        **Validates: Requirements 5.5, 12.2**
        """
        assume(email1 != email2)
        
        # Create two users
        auth_service = AuthenticationService(db)
        signup_request1 = SignupRequest(email=email1, password=password1)
        signup_response1 = auth_service.signup(signup_request1)
        user_id1 = signup_response1.user_id
        
        signup_request2 = SignupRequest(email=email2, password=password2)
        signup_response2 = auth_service.signup(signup_request2)
        user_id2 = signup_response2.user_id
        
        # User 1 creates a task
        task_service = TaskService(db)
        create_request = TaskCreate(description=description.strip())
        created_task = task_service.create_task(user_id1, create_request)
        
        # User 2 tries to access User 1's task
        with pytest.raises(ValueError, match="not found"):
            task_service.get_task(user_id2, created_task.id)
