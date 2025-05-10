# jitsi_py/core/room.py

from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import uuid

class RoomState:
    """Class representing the state of a Jitsi room."""
    
    def __init__(self, room_config: Dict):
        self.name = room_config.get("name")
        self.features = room_config.get("features", {})
        self.created_at = datetime.now()
        self.expiry = room_config.get("expiry")
        self.participants = []
        self.room_id = str(uuid.uuid4())
        self.breakout_rooms = []

    @property
    def expires_at(self) -> Optional[datetime]:
        """Return the expiry date of the room."""
        if self.expiry:
            return self.created_at + timedelta(seconds=self.expiry)
        return None
    
    @property
    def is_expired(self) -> bool:
        """Check if the room is expired."""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    @property
    def participant_count(self) -> int:
        """Return the count of participants in the room."""
        return len(self.participants)

class Room:
    """Class representing a Jitsi room."""
    
    def __init__(self, client, room_config: Dict):
        """Initialize a room.
        
        Args:
            client: JitsiClient instance.
            room_config: Room configuration.
        """
        self.client = client
        self.state = RoomState(room_config)
        
    def join_url(
        self, 
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_avatar: Optional[str] = None,
        role: Optional[str] = "viewer",
        features: Optional[Dict] = None
    ) -> str:
        """Generate a URL for joining the room.
        
        Args:
            user_name: Display name of the user.
            user_email: Email of the user.
            user_avatar: Avatar URL of the user.
            role: Role of the user in the room.
            features: Features to enable for this session.
            
        Returns:
            URL for joining the room.
        """
        merged_features = {**self.state.features, **(features or {})}
        
        return self.client.generate_room_url(
            room_name=self.state.name,
            user_name=user_name,
            user_email=user_email,
            user_avatar=user_avatar,
            role=role,
            features=merged_features
        )
    
    def host_url(
        self,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_avatar: Optional[str] = None,
        features: Optional[Dict] = None
    ) -> str:
        """Generate a URL for joining the room as a host.
        
        Args:
            user_name: Display name of the user.
            user_email: Email of the user.
            user_avatar: Avatar URL of the user.
            features: Features to enable for this session.
            
        Returns:
            URL for joining the room as a host.
        """
        return self.join_url(
            user_name=user_name,
            user_email=user_email,
            user_avatar=user_avatar,
            role="host",
            features=features
        )
    
    def create_breakout_room(self, room_name: str) -> 'Room':
        """Create a breakout room."""
        breakout_room = self.client.create_room(
            room_name=f"{self.state.name}_{room_name}",
            features=self.state.features,
            expiry=self.state.expiry
        )
        self.state.breakout_rooms.append(breakout_room)
        return breakout_room