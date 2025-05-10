# tests/security/test_token_security.py

import pytest
import jwt
import time
from jitsi_py.security.tokens import generate_jwt_token, verify_jwt_token

def test_token_tampering():
    """Test that tampered tokens are rejected."""
    jwt_secret = "test_secret"
    
    # Generate a valid token
    valid_token = generate_jwt_token(
        jwt_secret=jwt_secret,
        app_id="test_app",
        room_name="secure-room",
        user_name="Test User",
        role="viewer"
    )
    
    # Verify the valid token
    token_obj = verify_jwt_token(valid_token, jwt_secret)
    assert token_obj.is_valid is True
    
    # Tamper with the token by decoding, modifying, and re-encoding
    decoded = jwt.decode(valid_token, options={"verify_signature": False})
    decoded["context"]["user"]["role"] = "host"  # Elevate privileges
    tampered_token = jwt.encode(decoded, "wrong_secret", algorithm="HS256")
    
    # Verify the tampered token
    tampered_obj = verify_jwt_token(tampered_token, jwt_secret)
    assert tampered_obj.is_valid is False
    
    # Verify with wrong secret
    wrong_secret_obj = verify_jwt_token(valid_token, "wrong_secret")
    assert wrong_secret_obj.is_valid is False

def test_token_expiry():
    """Test that expired tokens are rejected."""
    jwt_secret = "test_secret"
    
    # Generate a token that expires immediately
    token = generate_jwt_token(
        jwt_secret=jwt_secret,
        app_id="test_app",
        room_name="expire-room",
        user_name="Test User",
        expiry=1  # 1 second expiry
    )
    
    # Verify the token before expiry
    token_obj = verify_jwt_token(token, jwt_secret)
    assert token_obj.is_valid is True
    
    # Wait for the token to expire
    time.sleep(2)
    
    # Verify the token after expiry
    expired_obj = verify_jwt_token(token, jwt_secret)
    assert expired_obj.is_valid is False