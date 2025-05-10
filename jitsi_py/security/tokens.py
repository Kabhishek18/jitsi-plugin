# jitsi_py/security/tokens.py (Updated implementation)

import jwt
import time
import uuid
from typing import Dict, Optional, List, Any

class JitsiToken:
    """Class for handling Jitsi JWT tokens."""
    
    def __init__(
        self, 
        token: Optional[str] = None,
        decoded_token: Optional[Dict] = None
    ):
        self.token = token
        self.decoded_token = decoded_token

    @property
    def is_valid(self) -> bool:
        """Check if the token is valid."""
        if not self.decoded_token:
            return False
        
        now = int(time.time())
        exp = self.decoded_token.get("exp", 0)
        
        return now < exp
    
    @property
    def user_id(self) -> Optional[str]:
        """Get the user ID from the token."""
        if not self.decoded_token:
            return None
        
        context = self.decoded_token.get("context", {})
        user = context.get("user", {})
        
        return user.get("id")
    
    @property
    def room(self) -> Optional[str]:
        """Get the room from the token."""
        if not self.decoded_token:
            return None
        
        return self.decoded_token.get("room")
    
    @property
    def role(self) -> Optional[str]:
        """Get the user role from the token."""
        if not self.decoded_token:
            return None
        
        context = self.decoded_token.get("context", {})
        user = context.get("user", {})
        
        return user.get("role")

def generate_jwt_token(
    jwt_secret: str,
    app_id: Optional[str] = None,
    room_name: str = "",
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    user_email: Optional[str] = None,
    user_avatar: Optional[str] = None,
    role: Optional[str] = "viewer",
    expiry: int = 3600  # 1 hour
) -> str:
    """Generate a JWT token for Jitsi authentication.
    
    Args:
        jwt_secret: Secret for JWT token generation.
        app_id: Application ID.
        room_name: Name of the room.
        user_id: ID of the user.
        user_name: Display name of the user.
        user_email: Email of the user.
        user_avatar: Avatar URL of the user.
        role: Role of the user.
        expiry: Token expiry time in seconds.
        
    Returns:
        JWT token string.
    """
    now = int(time.time())
    
    # Use a UUID if no user ID is provided
    if not user_id:
        user_id = str(uuid.uuid4())
    
    payload = {
        "iss": app_id or "jitsi-py",
        "sub": app_id or "jitsi-py",
        "exp": now + expiry,
        "iat": now,
        "nbf": now,
        "room": room_name,
        "context": {
            "user": {
                "id": user_id,
                "name": user_name,
                "email": user_email,
                "avatar": user_avatar,
                "role": role
            },
            "features": {
                "livestreaming": role in ["host", "co-host"],
                "recording": role in ["host", "co-host"],
                "transcription": True,
                "outbound-call": role in ["host", "co-host"]
            }
        }
    }
    
    # Only add the audience claim if app_id is provided
    if app_id:
        payload["aud"] = app_id
    
    return jwt.encode(payload, jwt_secret, algorithm="HS256")

def verify_jwt_token(token: str, jwt_secret: str) -> JitsiToken:
    """Verify a JWT token.
    
    Args:
        token: JWT token string.
        jwt_secret: Secret for JWT token verification.
        
    Returns:
        JitsiToken object with decoded token.
    """
    try:
        # Use options to skip audience validation if not needed
        decoded_token = jwt.decode(
            token, 
            jwt_secret, 
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        return JitsiToken(token=token, decoded_token=decoded_token)
    except jwt.PyJWTError as e:
        # Log the error for debugging
        print(f"JWT verification error: {str(e)}")
        return JitsiToken()