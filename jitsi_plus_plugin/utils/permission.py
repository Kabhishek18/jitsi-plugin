"""
Permission utilities for managing user roles and permissions.
"""

import logging
from typing import Dict, Any, List, Set

logger = logging.getLogger(__name__)

class PermissionManager:
    """
    Manager for user roles and permissions.
    Handles permission checks for various actions.
    """
    
    def __init__(self):
        """Initialize the permission manager."""
        """Initialize the permission manager."""
        # Role definitions
        self.roles = {
            "admin": {
                "description": "Administrator with full control",
                "permissions": {
                    "create_room", "delete_room", "configure_room",
                    "manage_users", "kick_user", "mute_user",
                    "start_recording", "stop_recording",
                    "enable_feature", "disable_feature",
                    "create_poll", "end_poll", "delete_poll",
                    "clear_whiteboard"
                }
            },
            "host": {
                "description": "Host with control over a room",
                "permissions": {
                    "configure_room",
                    "manage_users", "kick_user", "mute_user",
                    "start_recording", "stop_recording",
                    "enable_feature", "disable_feature",
                    "create_poll", "end_poll",
                    "clear_whiteboard"
                }
            },
            "presenter": {
                "description": "Presenter with screen sharing and whiteboard control",
                "permissions": {
                    "share_screen",
                    "create_poll", "end_poll",
                    "control_whiteboard"
                }
            },
            "participant": {
                "description": "Regular participant",
                "permissions": {
                    "send_message", "vote_poll",
                    "use_whiteboard"
                }
            },
            "viewer": {
                "description": "Viewer with limited interaction",
                "permissions": {
                    "send_message", "vote_poll"
                }
            }
        }
        
        # Room user roles
        self.room_user_roles = {}
    
    def set_user_role(self, room_id: str, user_id: str, role: str) -> bool:
        """
        Set a user's role in a room.
        
        Args:
            room_id (str): ID of the room.
            user_id (str): ID of the user.
            role (str): Role to assign.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if role not in self.roles:
            logger.warning(f"Unknown role: {role}")
            return False
        
        # Initialize room if not exists
        if room_id not in self.room_user_roles:
            self.room_user_roles[room_id] = {}
        
        # Set user role
        self.room_user_roles[room_id][user_id] = role
        
        logger.info(f"Set user {user_id} role to {role} in room {room_id}")
        return True
    
    def get_user_role(self, room_id: str, user_id: str) -> str:
        """
        Get a user's role in a room.
        
        Args:
            room_id (str): ID of the room.
            user_id (str): ID of the user.
            
        Returns:
            str: User's role or "participant" if not set.
        """
        if room_id in self.room_user_roles and user_id in self.room_user_roles[room_id]:
            return self.room_user_roles[room_id][user_id]
        
        # Default to participant
        return "participant"
    
    def get_user_permissions(self, room_id: str, user_id: str) -> Set[str]:
        """
        Get a user's permissions in a room.
        
        Args:
            room_id (str): ID of the room.
            user_id (str): ID of the user.
            
        Returns:
            Set[str]: Set of permission names.
        """
        role = self.get_user_role(room_id, user_id)
        return self.roles.get(role, {}).get("permissions", set())
    
    def check_permission(self, room_id: str, user_id: str, permission: str) -> bool:
        """
        Check if a user has a specific permission in a room.
        
        Args:
            room_id (str): ID of the room.
            user_id (str): ID of the user.
            permission (str): Permission to check.
            
        Returns:
            bool: True if the user has the permission, False otherwise.
        """
        permissions = self.get_user_permissions(room_id, user_id)
        return permission in permissions
    
    def list_users_with_role(self, room_id: str, role: str) -> List[str]:
        """
        List all users with a specific role in a room.
        
        Args:
            room_id (str): ID of the room.
            role (str): Role to check.
            
        Returns:
            List[str]: List of user IDs.
        """
        if room_id not in self.room_user_roles:
            return []
        
        return [user_id for user_id, user_role in self.room_user_roles[room_id].items() 
                if user_role == role]
    
    def clear_room_permissions(self, room_id: str) -> bool:
        """
        Clear all user roles for a room.
        
        Args:
            room_id (str): ID of the room.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if room_id in self.room_user_roles:
            del self.room_user_roles[room_id]
            
            logger.info(f"Cleared all user roles for room {room_id}")
            return True
        
        return False