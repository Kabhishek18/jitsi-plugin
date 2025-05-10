# jitsi_py/core/client.py

import logging
from typing import Dict, Optional, Union, List
from dataclasses import dataclass
from enum import Enum

from ..security.tokens import JitsiToken
from ..core.room import Room

class JitsiServerType(Enum):
    PUBLIC = "public"    # Default public Jitsi server
    SELF_HOSTED = "self_hosted"  # Self-hosted Jitsi server
    DOCKER = "docker"    # Dockerized local deployment

@dataclass
class JitsiServerConfig:
    server_type: JitsiServerType
    domain: str
    secure: bool = True
    api_endpoint: Optional[str] = None
    
    @property
    def base_url(self) -> str:
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.domain}"

class JitsiClient:
    """Main client interface for interacting with Jitsi Meet."""
    
    def __init__(
        self, 
        server_config: Optional[JitsiServerConfig] = None,
        app_id: Optional[str] = None,
        api_key: Optional[str] = None,
        jwt_secret: Optional[str] = None
    ):
        """Initialize the Jitsi client.
        
        Args:
            server_config: Configuration for the Jitsi server.
            app_id: Application ID for authentication.
            api_key: API key for authenticated requests.
            jwt_secret: Secret for JWT token generation.
        """
        self.logger = logging.getLogger("jitsi_py")
        
        # Default to public Jitsi server if not provided
        self.server_config = server_config or JitsiServerConfig(
            server_type=JitsiServerType.PUBLIC,
            domain="meet.jit.si"
        )
        
        self.app_id = app_id
        self.api_key = api_key
        self.jwt_secret = jwt_secret
        
        # Import here to avoid circular reference
        from ..utils.config import JitsiConfig
        self.config = JitsiConfig(server_config=self.server_config)
        
    def create_room(
        self, 
        room_name: str, 
        features: Optional[Dict] = None, 
        expiry: Optional[int] = None
    ) -> Room:
        """Create a new Jitsi room.
        
        Args:
            room_name: Name of the room to create.
            features: Features to enable for this room.
            expiry: Room expiry time in seconds.
            
        Returns:
            Room object.
        """
        room_config = {
            "name": room_name,
            "features": features or {},
            "expiry": expiry
        }
        
        return Room(self, room_config)
    
    def get_room(self, room_name: str) -> Room:
        """Get an existing room by name.
        
        Args:
            room_name: Name of the room to retrieve.
            
        Returns:
            Room object.
        """
        return Room(self, {"name": room_name})
    
    def generate_room_url(
        self, 
        room_name: str, 
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_avatar: Optional[str] = None,
        role: Optional[str] = None,
        token: Optional[str] = None,
        features: Optional[Dict] = None
    ) -> str:
        """Generate a URL for joining a room.
        
        Args:
            room_name: Name of the room.
            user_name: Display name of the user.
            user_email: Email of the user.
            user_avatar: Avatar URL of the user.
            role: Role of the user in the room.
            token: JWT token for authentication.
            features: Features to enable for this room.
            
        Returns:
            URL for joining the room.
        """
        from ..utils.url import build_jitsi_url
        
        if not token and self.jwt_secret:
            from ..security.tokens import generate_jwt_token
            
            token = generate_jwt_token(
                jwt_secret=self.jwt_secret,
                app_id=self.app_id,
                room_name=room_name,
                user_name=user_name,
                user_email=user_email,
                user_avatar=user_avatar,
                role=role
            )
        
        return build_jitsi_url(
            domain=self.server_config.base_url,
            room_name=room_name,
            token=token,
            features=features
        )