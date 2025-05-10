# tests/unit/test_tokens.py

import pytest
import jwt
import time
from datetime import datetime, timedelta

from jitsi_py.security.tokens import JitsiToken, generate_jwt_token, verify_jwt_token

class TestJitsiToken:
    
    def test_token_initialization(self):
        """Test token initialization."""
        token = JitsiToken(token="test_token")
        assert token.token == "test_token"
        assert token.decoded_token is None
        
        decoded_token = {"sub": "test_user", "exp": int(time.time()) + 3600}
        token = JitsiToken(token="test_token", decoded_token=decoded_token)
        assert token.token == "test_token"
        assert token.decoded_token == decoded_token
    
    def test_is_valid(self):
        """Test token validity check."""
        # Valid token
        now = int(time.time())
        decoded_token = {"exp": now + 3600}
        token = JitsiToken(token="test_token", decoded_token=decoded_token)
        assert token.is_valid is True
        
        # Expired token
        decoded_token = {"exp": now - 3600}
        token = JitsiToken(token="test_token", decoded_token=decoded_token)
        assert token.is_valid is False
        
        # No decoded token
        token = JitsiToken(token="test_token")
        assert token.is_valid is False
    
    def test_user_id(self):
        """Test getting user ID from token."""
        decoded_token = {"context": {"user": {"id": "test_user_id"}}}
        token = JitsiToken(token="test_token", decoded_token=decoded_token)
        assert token.user_id == "test_user_id"
        
        # No user ID
        decoded_token = {"context": {"user": {}}}
        token = JitsiToken(token="test_token", decoded_token=decoded_token)
        assert token.user_id is None
        
        # No decoded token
        token = JitsiToken(token="test_token")
        assert token.user_id is None
    
    def test_room(self):
        """Test getting room from token."""
        decoded_token = {"room": "test_room"}
        token = JitsiToken(token="test_token", decoded_token=decoded_token)
        assert token.room == "test_room"
        
        # No room
        decoded_token = {}
        token = JitsiToken(token="test_token", decoded_token=decoded_token)
        assert token.room is None
        
        # No decoded token
        token = JitsiToken(token="test_token")
        assert token.room is None
    
    def test_role(self):
        """Test getting user role from token."""
        decoded_token = {"context": {"user": {"role": "host"}}}
        token = JitsiToken(token="test_token", decoded_token=decoded_token)
        assert token.role == "host"
        
        # No role
        decoded_token = {"context": {"user": {}}}
        token = JitsiToken(token="test_token", decoded_token=decoded_token)
        assert token.role is None
        
        # No decoded token
        token = JitsiToken(token="test_token")
        assert token.role is None

class TestJwtTokenFunctions:
    
    # tests/unit/test_tokens.py

    def test_generate_jwt_token(self):
        """Test generating a JWT token."""
        jwt_secret = "test_secret"
        app_id = "test_app"
        room_name = "test_room"
        user_name = "Test User"
        user_email = "test@example.com"
        role = "host"
        
        token = generate_jwt_token(
            jwt_secret=jwt_secret,
            app_id=app_id,
            room_name=room_name,
            user_name=user_name,
            user_email=user_email,
            role=role,
            expiry=3600
        )
        
        # Decode the token to verify its contents - add audience parameter
        decoded = jwt.decode(
            token, 
            jwt_secret, 
            algorithms=["HS256"],
            audience=app_id  # Add this line to fix the test
        )
        
        assert decoded["iss"] == app_id
        assert decoded["aud"] == app_id
        assert decoded["sub"] == app_id
        assert decoded["room"] == room_name
        assert decoded["context"]["user"]["name"] == user_name
        assert decoded["context"]["user"]["email"] == user_email
        assert decoded["context"]["user"]["role"] == role
        assert decoded["context"]["features"]["livestreaming"] is True
        assert decoded["context"]["features"]["recording"] is True
        assert decoded["context"]["features"]["transcription"] is True
        
        # Check expiry time
        now = int(time.time())
        assert decoded["exp"] > now
        assert decoded["exp"] <= now + 3600
        
    def test_verify_jwt_token_valid(self):
        """Test verifying a valid JWT token."""
        jwt_secret = "test_secret"
        
        # Create a token that expires in 1 hour
        payload = {
            "iss": "test_app",
            "room": "test_room",
            "context": {"user": {"id": "test_user"}},
            "exp": int(time.time()) + 3600
        }
        token_str = jwt.encode(payload, jwt_secret, algorithm="HS256")
        
        token = verify_jwt_token(token_str, jwt_secret)
        
        assert token.token == token_str
        assert token.decoded_token == payload
        assert token.is_valid is True
        assert token.room == "test_room"
    
    def test_verify_jwt_token_invalid(self):
        """Test verifying an invalid JWT token."""
        jwt_secret = "test_secret"
        wrong_secret = "wrong_secret"
        
        # Create a token
        payload = {
            "iss": "test_app",
            "room": "test_room",
            "context": {"user": {"id": "test_user"}},
            "exp": int(time.time()) + 3600
        }
        token_str = jwt.encode(payload, jwt_secret, algorithm="HS256")
        
        # Verify with wrong secret
        token = verify_jwt_token(token_str, wrong_secret)
        
        assert token.token is None
        assert token.decoded_token is None
        assert token.is_valid is False
        
        # Verify with invalid token
        token = verify_jwt_token("invalid.token.string", jwt_secret)
        
        assert token.token is None
        assert token.decoded_token is None
        assert token.is_valid is False