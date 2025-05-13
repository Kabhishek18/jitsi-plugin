"""
Whiteboard controller for managing whiteboard functionality.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

class WhiteboardController:
    """
    Controller for managing whiteboard functionality.
    Handles drawing, shapes, and collaborative editing.
    """
    
    def __init__(self, signaling_server):
        """
        Initialize the whiteboard controller.
        
        Args:
            signaling_server: Signaling server instance.
        """
        self.signaling = signaling_server
        self.active_whiteboards = {}
    
    def create_whiteboard(self, room_id: str) -> Dict[str, Any]:
        """
        Create a new whiteboard for a room.
        
        Args:
            room_id (str): ID of the room.
            
        Returns:
            Dict[str, Any]: Whiteboard information.
        """
        whiteboard_id = f"wb-{room_id}"
        
        whiteboard_info = {
            "id": whiteboard_id,
            "room_id": room_id,
            "created_at": self.signaling.room_states.get(room_id, {}).get("created_at", 0) or 0,
            "elements": [],
            "active_users": set()
        }
        
        self.active_whiteboards[whiteboard_id] = whiteboard_info
        
        logger.info(f"Created whiteboard for room: {room_id}")
        return whiteboard_info
    
    def get_whiteboard(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the whiteboard for a room.
        
        Args:
            room_id (str): ID of the room.
            
        Returns:
            Optional[Dict[str, Any]]: Whiteboard information or None if not found.
        """
        whiteboard_id = f"wb-{room_id}"
        return self.active_whiteboards.get(whiteboard_id)
    
    def join_whiteboard(self, room_id: str, user_id: str) -> bool:
        """
        Join a whiteboard.
        
        Args:
            room_id (str): ID of the room.
            user_id (str): ID of the user.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        whiteboard_id = f"wb-{room_id}"
        
        if whiteboard_id not in self.active_whiteboards:
            # Create whiteboard if it doesn't exist
            self.create_whiteboard(room_id)
        
        # Add user to active users
        self.active_whiteboards[whiteboard_id]["active_users"].add(user_id)
        
        logger.info(f"User {user_id} joined whiteboard for room {room_id}")
        return True
    
    def leave_whiteboard(self, room_id: str, user_id: str) -> bool:
        """
        Leave a whiteboard.
        
        Args:
            room_id (str): ID of the room.
            user_id (str): ID of the user.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        whiteboard_id = f"wb-{room_id}"
        
        if whiteboard_id in self.active_whiteboards:
            # Remove user from active users
            if user_id in self.active_whiteboards[whiteboard_id]["active_users"]:
                self.active_whiteboards[whiteboard_id]["active_users"].remove(user_id)
            
            logger.info(f"User {user_id} left whiteboard for room {room_id}")
            
            # Clean up empty whiteboard
            if not self.active_whiteboards[whiteboard_id]["active_users"]:
                del self.active_whiteboards[whiteboard_id]
                logger.info(f"Whiteboard for room {room_id} closed (no users left)")
            
            return True
        
        return False
    
    def add_element(self, room_id: str, element_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Add an element to a whiteboard.
        
        Args:
            room_id (str): ID of the room.
            element_data (Dict[str, Any]): Element data.
            user_id (str): ID of the user adding the element.
            
        Returns:
            Dict[str, Any]: Element information.
        """
        whiteboard_id = f"wb-{room_id}"
        
        if whiteboard_id not in self.active_whiteboards:
            # Create whiteboard if it doesn't exist
            self.create_whiteboard(room_id)
        
        # Generate element ID
        element_id = str(uuid.uuid4())
        
        # Create element
        element = {
            "id": element_id,
            "type": element_data.get("type", "path"),
            "data": element_data.get("data", {}),
            "style": element_data.get("style", {}),
            "creator": user_id,
            "created_at": self.signaling.room_states.get(room_id, {}).get("created_at", 0) or 0
        }
        
        # Add to whiteboard
        self.active_whiteboards[whiteboard_id]["elements"].append(element)
        
        # Send whiteboard event through signaling server
        if self.signaling and hasattr(self.signaling, "_handle_whiteboard_event"):
            import asyncio
            asyncio.create_task(self.signaling._handle_whiteboard_event(
                user_id, room_id, {
                    "type": "add",
                    "element": element
                }
            ))
        
        logger.info(f"Added element {element_id} to whiteboard for room {room_id}")
        return element
    
    def update_element(self, room_id: str, element_id: str, updates: Dict[str, Any], user_id: str) -> bool:
        """
        Update an element on a whiteboard.
        
        Args:
            room_id (str): ID of the room.
            element_id (str): ID of the element.
            updates (Dict[str, Any]): Updates to apply.
            user_id (str): ID of the user updating the element.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        whiteboard_id = f"wb-{room_id}"
        
        if whiteboard_id not in self.active_whiteboards:
            logger.warning(f"Whiteboard not found for room: {room_id}")
            return False
        
        # Find and update element
        for i, element in enumerate(self.active_whiteboards[whiteboard_id]["elements"]):
            if element["id"] == element_id:
                # Update element
                for key, value in updates.items():
                    if key in ["data", "style"]:
                        if key not in element:
                            element[key] = {}
                        element[key].update(value)
                    elif key != "id" and key != "creator" and key != "created_at":
                        element[key] = value
                
                # Send whiteboard event through signaling server
                if self.signaling and hasattr(self.signaling, "_handle_whiteboard_event"):
                    import asyncio
                    asyncio.create_task(self.signaling._handle_whiteboard_event(
                        user_id, room_id, {
                            "type": "update",
                            "elementId": element_id,
                            "updates": updates
                        }
                    ))
                
                logger.info(f"Updated element {element_id} on whiteboard for room {room_id}")
                return True
        
        logger.warning(f"Element not found: {element_id}")
        return False
    
    def delete_element(self, room_id: str, element_id: str, user_id: str) -> bool:
        """
        Delete an element from a whiteboard.
        
        Args:
            room_id (str): ID of the room.
            element_id (str): ID of the element.
            user_id (str): ID of the user deleting the element.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        whiteboard_id = f"wb-{room_id}"
        
        if whiteboard_id not in self.active_whiteboards:
            logger.warning(f"Whiteboard not found for room: {room_id}")
            return False
        
        # Find and remove element
        elements = self.active_whiteboards[whiteboard_id]["elements"]
        for i, element in enumerate(elements):
            if element["id"] == element_id:
                # Remove element
                del elements[i]
                
                # Send whiteboard event through signaling server
                if self.signaling and hasattr(self.signaling, "_handle_whiteboard_event"):
                    import asyncio
                    asyncio.create_task(self.signaling._handle_whiteboard_event(
                        user_id, room_id, {
                            "type": "delete",
                            "elementId": element_id
                        }
                    ))
                
                logger.info(f"Deleted element {element_id} from whiteboard for room {room_id}")
                return True
        
        logger.warning(f"Element not found: {element_id}")
        return False
    
    def clear_whiteboard(self, room_id: str, user_id: str) -> bool:
        """
        Clear all elements from a whiteboard.
        
        Args:
            room_id (str): ID of the room.
            user_id (str): ID of the user clearing the whiteboard.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        whiteboard_id = f"wb-{room_id}"
        
        if whiteboard_id not in self.active_whiteboards:
            logger.warning(f"Whiteboard not found for room: {room_id}")
            return False
        
        # Clear all elements
        self.active_whiteboards[whiteboard_id]["elements"] = []
        
        # Send whiteboard event through signaling server
        if self.signaling and hasattr(self.signaling, "_handle_whiteboard_event"):
            import asyncio
            asyncio.create_task(self.signaling._handle_whiteboard_event(
                user_id, room_id, {
                    "type": "clear"
                }
            ))
        
        logger.info(f"Cleared whiteboard for room {room_id}")
        return True
    
    def export_whiteboard(self, room_id: str, format: str = "json") -> Any:
        """
        Export whiteboard content.
        
        Args:
            room_id (str): ID of the room.
            format (str): Export format ('json', 'svg', 'png').
            
        Returns:
            Any: Exported whiteboard data.
        """
        whiteboard_id = f"wb-{room_id}"
        
        if whiteboard_id not in self.active_whiteboards:
            logger.warning(f"Whiteboard not found for room: {room_id}")
            return None
        
        if format == "json":
            # Export as JSON
            return {
                "id": whiteboard_id,
                "elements": self.active_whiteboards[whiteboard_id]["elements"]
            }
        
        elif format == "svg":
            # Export as SVG
            # This would require additional implementation to convert elements to SVG
            raise NotImplementedError("SVG export not implemented yet")
        
        elif format == "png":
            # Export as PNG
            # This would require additional implementation to render whiteboard to PNG
            raise NotImplementedError("PNG export not implemented yet")
        
        else:
            raise ValueError(f"Unsupported export format: {format}")