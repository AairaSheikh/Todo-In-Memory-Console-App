"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal, Base, engine
from app.models import User, Task


@pytest.fixture(scope="function")
def test_client():
    """Create test client with fresh database."""
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    Base.metadata.drop_all(bind=engine)


class TestAuthenticationEndpoints:
    """Integration tests for authentication endpoints."""

    def test_signup_success(self, test_client):
        """Test successful user signup."""
        response = test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert "token" in data
        assert "expires_in" in data

    def test_signup_duplicate_email(self, test_client):
        """Test signup with duplicate email."""
        # First signup
        test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        
        # Second signup with same email
        response = test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password456"},
        )
        
        # Backend returns 400 for duplicate email (validation error)
        assert response.status_code in [400, 409]

    def test_signup_invalid_email(self, test_client):
        """Test signup with invalid email."""
        response = test_client.post(
            "/auth/signup",
            json={"email": "invalid-email", "password": "password123"},
        )
        
        assert response.status_code == 422  # Pydantic validation error

    def test_signup_short_password(self, test_client):
        """Test signup with short password."""
        response = test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "short"},
        )
        
        assert response.status_code == 400

    def test_signin_success(self, test_client):
        """Test successful user signin."""
        # Create user
        test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        
        # Sign in
        response = test_client.post(
            "/auth/signin",
            json={"email": "test@example.com", "password": "password123"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "token" in data

    def test_signin_invalid_email(self, test_client):
        """Test signin with non-existent email."""
        response = test_client.post(
            "/auth/signin",
            json={"email": "nonexistent@example.com", "password": "password123"},
        )
        
        assert response.status_code == 401

    def test_signin_wrong_password(self, test_client):
        """Test signin with wrong password."""
        # Create user
        test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        
        # Try to sign in with wrong password
        response = test_client.post(
            "/auth/signin",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        
        assert response.status_code == 401

    def test_logout(self, test_client):
        """Test logout endpoint."""
        response = test_client.post("/auth/logout")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"


class TestTaskEndpoints:
    """Integration tests for task endpoints."""

    def test_create_task_success(self, test_client):
        """Test successful task creation."""
        # Create user
        signup_response = test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        user_id = signup_response.json()["user_id"]
        token = signup_response.json()["token"]
        
        # Create task
        response = test_client.post(
            f"/api/{user_id}/tasks",
            json={"description": "Test task", "priority": "High"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Test task"
        assert data["priority"] == "High"
        assert data["completed"] is False

    def test_create_task_without_auth(self, test_client):
        """Test task creation without authentication."""
        response = test_client.post(
            "/api/test-user-id/tasks",
            json={"description": "Test task"},
        )
        
        assert response.status_code == 401

    def test_create_task_empty_description(self, test_client):
        """Test task creation with empty description."""
        # Create user
        signup_response = test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        user_id = signup_response.json()["user_id"]
        token = signup_response.json()["token"]
        
        # Try to create task with empty description
        response = test_client.post(
            f"/api/{user_id}/tasks",
            json={"description": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 400

    def test_get_tasks(self, test_client):
        """Test retrieving task list."""
        # Create user
        signup_response = test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        user_id = signup_response.json()["user_id"]
        token = signup_response.json()["token"]
        
        # Create tasks
        test_client.post(
            f"/api/{user_id}/tasks",
            json={"description": "Task 1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        test_client.post(
            f"/api/{user_id}/tasks",
            json={"description": "Task 2"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # Get tasks
        response = test_client.get(
            f"/api/{user_id}/tasks",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2

    def test_get_task_by_id(self, test_client):
        """Test retrieving a specific task."""
        # Create user
        signup_response = test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        user_id = signup_response.json()["user_id"]
        token = signup_response.json()["token"]
        
        # Create task
        create_response = test_client.post(
            f"/api/{user_id}/tasks",
            json={"description": "Test task"},
            headers={"Authorization": f"Bearer {token}"},
        )
        task_id = create_response.json()["id"]
        
        # Get task
        response = test_client.get(
            f"/api/{user_id}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        assert response.json()["description"] == "Test task"

    def test_update_task(self, test_client):
        """Test updating a task."""
        # Create user
        signup_response = test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        user_id = signup_response.json()["user_id"]
        token = signup_response.json()["token"]
        
        # Create task
        create_response = test_client.post(
            f"/api/{user_id}/tasks",
            json={"description": "Original task"},
            headers={"Authorization": f"Bearer {token}"},
        )
        task_id = create_response.json()["id"]
        
        # Update task
        response = test_client.put(
            f"/api/{user_id}/tasks/{task_id}",
            json={"description": "Updated task", "priority": "Low"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        assert response.json()["description"] == "Updated task"
        assert response.json()["priority"] == "Low"

    def test_delete_task(self, test_client):
        """Test deleting a task."""
        # Create user
        signup_response = test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        user_id = signup_response.json()["user_id"]
        token = signup_response.json()["token"]
        
        # Create task
        create_response = test_client.post(
            f"/api/{user_id}/tasks",
            json={"description": "Task to delete"},
            headers={"Authorization": f"Bearer {token}"},
        )
        task_id = create_response.json()["id"]
        
        # Delete task
        response = test_client.delete(
            f"/api/{user_id}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 204

    def test_toggle_task_completion(self, test_client):
        """Test toggling task completion."""
        # Create user
        signup_response = test_client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123"},
        )
        user_id = signup_response.json()["user_id"]
        token = signup_response.json()["token"]
        
        # Create task
        create_response = test_client.post(
            f"/api/{user_id}/tasks",
            json={"description": "Task to complete"},
            headers={"Authorization": f"Bearer {token}"},
        )
        task_id = create_response.json()["id"]
        
        # Toggle completion
        response = test_client.patch(
            f"/api/{user_id}/tasks/{task_id}/complete",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        assert response.json()["completed"] is True


class TestCrossUserAuthorization:
    """Integration tests for cross-user authorization."""

    def test_cross_user_task_access_rejected(self, test_client):
        """Test that users cannot access other users' tasks."""
        # Create user 1
        user1_response = test_client.post(
            "/auth/signup",
            json={"email": "user1@example.com", "password": "password123"},
        )
        user1_id = user1_response.json()["user_id"]
        user1_token = user1_response.json()["token"]
        
        # Create user 2
        user2_response = test_client.post(
            "/auth/signup",
            json={"email": "user2@example.com", "password": "password123"},
        )
        user2_id = user2_response.json()["user_id"]
        user2_token = user2_response.json()["token"]
        
        # User 1 creates a task
        create_response = test_client.post(
            f"/api/{user1_id}/tasks",
            json={"description": "User 1's task"},
            headers={"Authorization": f"Bearer {user1_token}"},
        )
        task_id = create_response.json()["id"]
        
        # User 2 tries to access User 1's task
        response = test_client.get(
            f"/api/{user1_id}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        
        assert response.status_code == 403
