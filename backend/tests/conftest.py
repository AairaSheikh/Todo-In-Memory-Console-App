"""Pytest configuration and fixtures."""

import pytest
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Load environment variables BEFORE importing app modules
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# Set required environment variables for testing
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRATION_HOURS", "24")
os.environ.setdefault("ENVIRONMENT", "testing")

# Clear the settings cache before importing app
from app.config import get_settings
get_settings.cache_clear()

from app.database import Base, get_db
from app.main import app
from app.models import User, Task, ConversationMessage  # Import models to register them

# Use the same database as development for testing (PostgreSQL)
# This ensures UUID support works correctly
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/test_db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    # Drop all tables first
    Base.metadata.drop_all(bind=engine)
    # Create all tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.testclient import TestClient
    return TestClient(app)
