"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.config import get_settings
from app.routes import auth_router, tasks_router, chat_router
from app.middleware import RateLimitMiddleware

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Todo Full-Stack Web Application",
    description="A full-stack todo application with authentication and persistent storage",
    version="1.0.0",
)

# Add rate limiting middleware (must be added before CORS)
app.add_middleware(RateLimitMiddleware, requests_per_minute=10)

# Add CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
