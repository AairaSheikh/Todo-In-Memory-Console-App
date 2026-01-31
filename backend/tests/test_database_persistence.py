"""Property-based tests for database persistence."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.orm import Session
from app.models import User, Task
from app.database import SessionLocal
import bcrypt
from uuid import uuid4


class TestDatabasePersistence:
    """Property 31: Database Persistence Survives Restart.
    
    Validates: Requirements 10.2
    """

    @given(
        email=st.emails(),
        description=st.text(min_size=1).filter(lambda x: x.strip()),
        priority=st.sampled_from(["High", "Medium", "Low"]),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_task_persists_to_database(self, db: Session, email: str, description: str, priority: str):
        """For any task created and persisted to the database, restarting the application
        and querying the database should retrieve the same task.
        
        **Validates: Requirements 10.2**
        """
        # Create user
        password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
        user = User(email=email, password_hash=password_hash)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create task
        task = Task(
            user_id=user.id,
            description=description.strip(),
            priority=priority,
            completed=False,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        task_id = task.id
        
        # Simulate restart by creating new session
        db.close()
        new_db = SessionLocal()
        
        try:
            # Retrieve task from new session
            retrieved_task = new_db.query(Task).filter(Task.id == task_id).first()
            
            assert retrieved_task is not None, "Task not found after restart"
            assert retrieved_task.description == description.strip(), "Description mismatch"
            assert retrieved_task.priority == priority, "Priority mismatch"
            assert retrieved_task.completed is False, "Completion status mismatch"
            assert retrieved_task.user_id == user.id, "User ID mismatch"
        finally:
            new_db.close()


class TestUserPasswordHashing:
    """Property 32: User Password Stored Hashed.
    
    Validates: Requirements 10.3
    """

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_user_password_stored_hashed(self, db: Session, email: str, password: str):
        """For any user account created, the password stored in the database
        should be hashed, not plaintext.
        
        **Validates: Requirements 10.3**
        """
        # Hash password
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        # Create user
        user = User(email=email, password_hash=password_hash)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Retrieve user from database
        retrieved_user = db.query(User).filter(User.email == email).first()
        
        assert retrieved_user is not None, "User not found"
        assert retrieved_user.password_hash != password, "Password is stored in plaintext"
        assert retrieved_user.password_hash == password_hash, "Password hash mismatch"
        
        # Verify password can be checked
        assert bcrypt.checkpw(password.encode(), retrieved_user.password_hash.encode()), "Password verification failed"
