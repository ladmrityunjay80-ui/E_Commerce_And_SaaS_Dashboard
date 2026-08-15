import pytest
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    # Verify the hash is different from the original password
    assert hashed != password
    
    # Verify the password can be verified
    assert verify_password(password, hashed) is True
    
    # Verify wrong password fails
    assert verify_password("wrong_password", hashed) is False


def test_token_creation():
    """Test JWT token creation and decoding."""
    user_id = 123
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    # Verify tokens are created
    assert access_token is not None
    assert refresh_token is not None
    assert access_token != refresh_token
    
    # Verify access token can be decoded
    access_payload = decode_token(access_token)
    assert access_payload is not None
    assert access_payload["sub"] == user_id
    assert access_payload["type"] == "access"
    
    # Verify refresh token can be decoded
    refresh_payload = decode_token(refresh_token)
    assert refresh_payload is not None
    assert refresh_payload["sub"] == user_id
    assert refresh_payload["type"] == "refresh"


def test_invalid_token():
    """Test invalid token handling."""
    invalid_token = "invalid_token_string"
    payload = decode_token(invalid_token)
    
    assert payload is None


def test_token_expiration():
    """Test token expiration handling."""
    from datetime import timedelta
    from app.core.config import settings
    
    # Create token with very short expiration
    short_lived_token = create_access_token(
        data={"sub": 123},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )
    
    payload = decode_token(short_lived_token)
    assert payload is None
