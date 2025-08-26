import pytest
from app.auth import verify_password, get_password_hash, create_access_token, verify_token
from app.models import TokenData
from datetime import timedelta


class TestAuth:
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Should verify correctly
        assert verify_password(password, hashed) is True
        
        # Should not verify with wrong password
        assert verify_password("wrongpassword", hashed) is False
    
    def test_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        # Token should be created
        assert token is not None
        assert isinstance(token, str)
        
        # Token should be verifiable
        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.email == "test@example.com"
    
    def test_token_with_expiry(self):
        """Test JWT token with custom expiry."""
        data = {"sub": "test@example.com"}
        expiry = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=expiry)
        
        # Token should be created
        assert token is not None
        
        # Token should be verifiable
        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.email == "test@example.com"
    
    def test_invalid_token(self):
        """Test invalid token handling."""
        # Invalid token should return None
        token_data = verify_token("invalid.token.here")
        assert token_data is None
