"""Authentication schemas."""

from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    """Request schema for user signup."""

    email: EmailStr
    password: str


class SigninRequest(BaseModel):
    """Request schema for user signin."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response schema for authentication endpoints."""

    user_id: str
    token: str
    expires_in: int
