"""Authentication service for user registration and login."""

import bcrypt
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import User
from app.config import get_settings
from app.schemas import SignupRequest, SigninRequest, AuthResponse


class AuthenticationService:
    """Manages user registration, login, and JWT token operations."""

    def __init__(self, db: Session):
        """Initialize authentication service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.settings = get_settings()

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash.
        
        Args:
            password: Plain text password
            password_hash: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def generate_token(self, user_id: str) -> tuple[str, int]:
        """Generate JWT token for user.
        
        Args:
            user_id: User ID to encode in token
            
        Returns:
            Tuple of (token, expiration_hours)
        """
        expiration = datetime.utcnow() + timedelta(hours=self.settings.jwt_expiration_hours)
        payload = {
            "user_id": str(user_id),
            "exp": expiration,
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )
        return token, self.settings.jwt_expiration_hours

    def validate_token(self, token: str) -> str:
        """Validate JWT token and extract user_id.
        
        Args:
            token: JWT token to validate
            
        Returns:
            User ID extracted from token
            
        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            user_id = payload.get("user_id")
            if not user_id:
                raise ValueError("Invalid token: missing user_id")
            return user_id
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def signup(self, request: SignupRequest) -> AuthResponse:
        """Register a new user.
        
        Args:
            request: Signup request with email and password
            
        Returns:
            AuthResponse with user_id and token
            
        Raises:
            ValueError: If email exists or password is invalid
        """
        # Validate email format (basic check)
        if "@" not in request.email or "." not in request.email:
            raise ValueError("Invalid email format")
        
        # Validate password length
        if len(request.password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Create new user
        password_hash = self.hash_password(request.password)
        user = User(email=request.email, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Generate token
        token, expires_in = self.generate_token(user.id)
        
        return AuthResponse(
            user_id=str(user.id),
            token=token,
            expires_in=expires_in,
        )

    def signin(self, request: SigninRequest) -> AuthResponse:
        """Sign in a user.
        
        Args:
            request: Signin request with email and password
            
        Returns:
            AuthResponse with user_id and token
            
        Raises:
            ValueError: If credentials are invalid
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == request.email).first()
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not self.verify_password(request.password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        # Generate token
        token, expires_in = self.generate_token(user.id)
        
        return AuthResponse(
            user_id=str(user.id),
            token=token,
            expires_in=expires_in,
        )
