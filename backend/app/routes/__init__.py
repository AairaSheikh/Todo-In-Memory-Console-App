"""API routes."""

from app.routes.auth import router as auth_router
from app.routes.tasks import router as tasks_router
from app.routes.chat import router as chat_router

__all__ = ["auth_router", "tasks_router", "chat_router"]
