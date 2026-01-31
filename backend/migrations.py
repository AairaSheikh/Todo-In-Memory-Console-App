"""Database migrations script."""

from app.database import Base, engine
from app.models import User, Task, ConversationMessage


def create_all_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")


def drop_all_tables():
    """Drop all database tables (use with caution)."""
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All tables dropped!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_all_tables()
    else:
        create_all_tables()
