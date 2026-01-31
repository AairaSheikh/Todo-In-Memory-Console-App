"""Property-based tests for authentication."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.orm import Session
from app.services import AuthenticationService
from app.schemas import SignupRequest, SigninRequest
from app.models import User
import bcrypt


class TestPasswordProperties:
    """Property-based tests for password hashing."""

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_user_password_stored_hashed(self, db: Session, email: str, password: str):
        """Property 32: User Password Stored Hashed.
        
        For any user account created, the password stored in the database
        should be hashed, not plaintext.
        
        **Validates: Requirements 10.3**
        """
        auth_service = AuthenticationService(db)
        request = SignupRequest(email=email, password=password)
        
        auth_service.signup(request)
        
        # Verify user was created with hashed password
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.password_hash != password
        assert bcrypt.checkpw(password.encode(), user.password_hash.encode())


class TestSignupProperties:
    """Property-based tests for user signup."""

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_valid_signup_creates_account(self, db: Session, email: str, password: str):
        """Property 1: Valid Signup Creates Account.
        
        For any valid email and password, signing up should create a user account
        and return a JWT token with an expiration time.
        
        **Validates: Requirements 1.1, 11.1**
        """
        auth_service = AuthenticationService(db)
        request = SignupRequest(email=email, password=password)
        
        response = auth_service.signup(request)
        
        assert response.user_id is not None
        assert response.token is not None
        assert response.expires_in > 0
        
        # Verify user was created
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.email == email

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_duplicate_email_signup_rejected(self, db: Session, email: str, password: str):
        """Property 2: Duplicate Email Signup Rejected.
        
        For any email that already exists in the system, attempting to sign up
        with that email should be rejected with an error.
        
        **Validates: Requirements 1.2**
        """
        auth_service = AuthenticationService(db)
        request = SignupRequest(email=email, password=password)
        
        # First signup should succeed
        auth_service.signup(request)
        
        # Second signup with same email should fail
        with pytest.raises(ValueError, match="already registered"):
            auth_service.signup(request)

    @given(
        invalid_email=st.text(min_size=1, max_size=50).filter(lambda x: "@" not in x or "." not in x),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_invalid_email_format_rejected(self, db: Session, invalid_email: str, password: str):
        """Property 3: Invalid Email Format Rejected.
        
        For any string that is not a valid email format, attempting to sign up
        with that email should be rejected with an error.
        
        **Validates: Requirements 1.3**
        """
        auth_service = AuthenticationService(db)
        request = SignupRequest(email=invalid_email, password=password)
        
        with pytest.raises(ValueError, match="Invalid email"):
            auth_service.signup(request)

    @given(
        email=st.emails(),
        short_password=st.text(min_size=1, max_size=7),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_short_password_rejected(self, db: Session, email: str, short_password: str):
        """Property 4: Short Password Rejected.
        
        For any password shorter than 8 characters, attempting to sign up with
        that password should be rejected with an error.
        
        **Validates: Requirements 1.4**
        """
        auth_service = AuthenticationService(db)
        request = SignupRequest(email=email, password=short_password)
        
        with pytest.raises(ValueError, match="at least 8 characters"):
            auth_service.signup(request)


class TestSigninProperties:
    """Property-based tests for user signin."""

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_valid_signin_returns_token(self, db: Session, email: str, password: str):
        """Property 5: Valid Signin Returns Token.
        
        For any user account and correct credentials, signing in should return
        a valid JWT token.
        
        **Validates: Requirements 2.1, 11.2**
        """
        auth_service = AuthenticationService(db)
        
        # Create user
        signup_request = SignupRequest(email=email, password=password)
        auth_service.signup(signup_request)
        
        # Sign in
        signin_request = SigninRequest(email=email, password=password)
        response = auth_service.signin(signin_request)
        
        assert response.user_id is not None
        assert response.token is not None
        assert response.expires_in > 0

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_invalid_email_signin_rejected(self, db: Session, email: str, password: str):
        """Property 6: Invalid Email Signin Rejected.
        
        For any email that does not exist in the system, attempting to sign in
        with that email should be rejected with an error.
        
        **Validates: Requirements 2.2**
        """
        auth_service = AuthenticationService(db)
        signin_request = SigninRequest(email=email, password=password)
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            auth_service.signin(signin_request)

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        wrong_password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_incorrect_password_signin_rejected(self, db: Session, email: str, password: str, wrong_password: str):
        """Property 7: Incorrect Password Signin Rejected.
        
        For any user account and incorrect password, attempting to sign in
        should be rejected with an error.
        
        **Validates: Requirements 2.3**
        """
        assume(password != wrong_password)
        
        auth_service = AuthenticationService(db)
        
        # Create user
        signup_request = SignupRequest(email=email, password=password)
        auth_service.signup(signup_request)
        
        # Try to sign in with wrong password
        signin_request = SigninRequest(email=email, password=wrong_password)
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            auth_service.signin(signin_request)


class TestTokenProperties:
    """Property-based tests for JWT token management."""

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_token_validation_extracts_user_id(self, db: Session, email: str, password: str):
        """Property 11: Token Validation Extracts User ID.
        
        For any valid JWT token, validating the token should extract the
        correct user_id from the token.
        
        **Validates: Requirements 12.1**
        """
        auth_service = AuthenticationService(db)
        
        # Create user and get token
        signup_request = SignupRequest(email=email, password=password)
        signup_response = auth_service.signup(signup_request)
        
        # Validate token
        extracted_user_id = auth_service.validate_token(signup_response.token)
        
        assert extracted_user_id == signup_response.user_id

    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_expired_token_rejected(self, db: Session, email: str, password: str):
        """Property 9: Expired Token Rejected.
        
        For any expired JWT token, making an API request with that token
        should be rejected with a 401 Unauthorized error.
        
        **Validates: Requirements 3.3, 11.3**
        """
        auth_service = AuthenticationService(db)
        
        # Create user
        signup_request = SignupRequest(email=email, password=password)
        auth_service.signup(signup_request)
        
        # Create an expired token manually
        import jwt
        from datetime import datetime, timedelta
        
        expired_payload = {
            "user_id": "test-user-id",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow(),
        }
        expired_token = jwt.encode(
            expired_payload,
            auth_service.settings.jwt_secret_key,
            algorithm=auth_service.settings.jwt_algorithm,
        )
        
        # Validate expired token should fail
        with pytest.raises(ValueError, match="expired"):
            auth_service.validate_token(expired_token)

    @given(
        invalid_token=st.text(min_size=10, max_size=100),
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_invalid_token_rejected(self, db: Session, invalid_token: str):
        """Property 10: Missing Token Rejected.
        
        For any API request without a JWT token, the request should be
        rejected with a 401 Unauthorized error.
        
        **Validates: Requirements 3.4, 11.4**
        """
        auth_service = AuthenticationService(db)
        
        # Validate invalid token should fail
        with pytest.raises(ValueError, match="Invalid token"):
            auth_service.validate_token(invalid_token)


# Import assume for hypothesis
from hypothesis import assume
