"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import SignupRequest, SigninRequest, AuthResponse
from app.services import AuthenticationService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user.
    
    Args:
        request: Signup request with email and password
        db: Database session
        
    Returns:
        AuthResponse with user_id and token
        
    Raises:
        HTTPException: If signup fails
    """
    try:
        auth_service = AuthenticationService(db)
        return auth_service.signup(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered" if "already" in str(e).lower() else str(e),
        )


@router.post("/signin", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def signin(request: SigninRequest, db: Session = Depends(get_db)):
    """Sign in a user.
    
    Args:
        request: Signin request with email and password
        db: Database session
        
    Returns:
        AuthResponse with user_id and token
        
    Raises:
        HTTPException: If signin fails
    """
    try:
        auth_service = AuthenticationService(db)
        return auth_service.signin(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """Sign out a user.
    
    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user(token: str = None, db: Session = Depends(get_db)):
    """Get current user info.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        Current user info
        
    Raises:
        HTTPException: If token is invalid
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )
    
    try:
        auth_service = AuthenticationService(db)
        user_id = auth_service.validate_token(token)
        
        from app.models import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        return {"user_id": str(user.id), "email": user.email}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
