"""
Jitsi connector for integrating with Jitsi Meet API.
"""

import logging
import requests
import json
import time
import uuid
import asyncio
import websockets
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

class JitsiConnector:
    """
    Connector for Jitsi Meet API integration.
    Handles connection and communication with Jitsi servers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Jitsi connector.
        
        Args:
            config (Dict[str, Any]): Configuration for Jitsi connection.
        """
        self.config = config
        self.server_url = config.get("server_url", "https://meet.jit.si")
        self.room_prefix = config.get("room_prefix", "jitsi-plus-")
        self.use_ssl = config.get("use_ssl", True)
        
        # Connection tracking
        self.active_rooms = {}
        self.active_connections = {}
        self.websocket = None
        self.connection_id = None
        self.connected = False
        
        # Callbacks
        self.on_participant_joined = None
        self.on_participant_left = None
        self.on_message_received = None
    
    def initialize(self) -> bool:
        """
        Initialize the Jitsi connector.
        
        Returns:
            bool: True if initialized successfully, False otherwise.
        """
        try:
            # Test connection to Jitsi server
            response = requests.get(f"{self.server_url}/http-pre-bind", timeout=5)
            if response.status_code == 200:
                logger.info(f"Successfully connected to Jitsi server at {self.server_url}")
                self.connected = True
                return True
            else:
                logger.error(f"Failed to connect to Jitsi server: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to Jitsi server: {str(e)}")
            return False
    
    def create_room(self, room_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new Jitsi room.
        
        Args:
            room_name (str, optional): Name for the room. If None, a random name is generated.
            
        Returns:
            Dict[str, Any]: Room information dictionary.
        """
        if not room_name:
            room_name = f"{self.room_prefix}{str(uuid.uuid4())[:8]}"
        
        # Add room to active rooms
        room_info = {
            "room_name": room_name,
            "created_at": time.time(),
            "participants": {},
            "features": {
                "video": True,
                "audio": True,
                "chat": True,
                "screen_sharing": True,
                "polls": True,
                "whiteboard": True,
                "settings": True,
                "background": True
            }
        }
        
        self.active_rooms[room_name] = room_info
        logger.info(f"Created room: {room_name}")
        
        return room_info
    
    def join_room(self, room_name: str, participant_name: str) -> Dict[str, Any]:
        """
        Join an existing Jitsi room.
        
        Args:
            room_name (str): Name of the room to join.
            participant_name (str): Name of the participant joining.
            
        Returns:
            Dict[str, Any]: Participant information dictionary.
        """
        if room_name not in self.active_rooms:
            # Auto-create room if it doesn't exist
            self.create_room(room_name)
        
        participant_id = str(uuid.uuid4())
        participant_info = {
            "id": participant_id,
            "name": participant_name,
            "joined_at": time.time(),
            "features": {
                "video": True,
                "audio": True,
                "screen_sharing": False
            }
        }
        
        self.active_rooms[room_name]["participants"][participant_id] = participant_info
        logger.info(f"Participant {participant_name} joined room {room_name}")
        
        # Trigger callback if set
        if self.on_participant_joined:
            self.on_participant_joined(room_name, participant_info)
        
        return participant_info
    
    def leave_room(self, room_name: str, participant_id: str) -> bool:
        """
        Leave a Jitsi room.
        
        Args:
            room_name (str): Name of the room.
            participant_id (str): ID of the participant leaving.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if room_name in self.active_rooms:
            if participant_id in self.active_rooms[room_name]["participants"]:
                participant_info = self.active_rooms[room_name]["participants"][participant_id]
                
                # Remove participant
                del self.active_rooms[room_name]["participants"][participant_id]
                logger.info(f"Participant {participant_info['name']} left room {room_name}")
                
                # Clean up empty rooms
                if not self.active_rooms[room_name]["participants"]:
                    del self.active_rooms[room_name]
                    logger.info(f"Room {room_name} closed (no participants left)")
                
                # Trigger callback if set
                if self.on_participant_left:
                    self.on_participant_left(room_name, participant_info)
                
                return True
        
        logger.warning(f"Failed to leave room: {room_name} or participant {participant_id} not found")
        return False
    
    def configure_room(self, room_name: str, features: Dict[str, bool]) -> bool:
        """
        Configure features for a room.
        
        Args:
            room_name (str): Name of the room to configure.
            features (Dict[str, bool]): Dictionary of features to enable/disable.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if room_name in self.active_rooms:
            for feature, enabled in features.items():
                if feature in self.active_rooms[room_name]["features"]:
                    self.active_rooms[room_name]["features"][feature] = enabled
            
            logger.info(f"Room {room_name} configuration updated: {features}")
            return True
        
        logger.warning(f"Failed to configure room: {room_name} not found")
        return False
    
    def toggle_participant_feature(self, room_name: str, participant_id: str, 
                                  feature: str, enabled: bool) -> bool:
        """
        Toggle a feature for a specific participant.
        
        Args:
            room_name (str): Name of the room.
            participant_id (str): ID of the participant.
            feature (str): Feature to toggle.
            enabled (bool): True to enable, False to disable.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if room_name in self.active_rooms:
            if participant_id in self.active_rooms[room_name]["participants"]:
                if feature in self.active_rooms[room_name]["participants"][participant_id]["features"]:
                    self.active_rooms[room_name]["participants"][participant_id]["features"][feature] = enabled
                    
                    logger.info(f"Participant {participant_id} feature {feature} set to {enabled}")
                    return True
        
        logger.warning(f"Failed to toggle feature: room {room_name} or participant {participant_id} not found")
        return False
    
    def get_room_info(self, room_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a room.
        
        Args:
            room_name (str): Name of the room.
            
        Returns:
            Optional[Dict[str, Any]]: Room information or None if not found.
        """
        return self.active_rooms.get(room_name)
    
    def get_participant_info(self, room_name: str, participant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a participant.
        
        Args:
            room_name (str): Name of the room.
            participant_id (str): ID of the participant.
            
        Returns:
            Optional[Dict[str, Any]]: Participant information or None if not found.
        """
        if room_name in self.active_rooms:
            return self.active_rooms[room_name]["participants"].get(participant_id)
        return None
    
    def get_jitsi_url(self, room_name: str) -> str:
        """
        Get the full URL for a Jitsi room.
        
        Args:
            room_name (str): Name of the room.
            
        Returns:
            str: Full URL for accessing the room.
        """
        return f"{self.server_url}/{room_name}"
    
    async def connect_websocket(self, room_name: str):
        """
        Connect to Jitsi websocket for real-time events.
        
        Args:
            room_name (str): Name of the room to connect to.
        """
        protocol = "wss" if self.use_ssl else "ws"
        ws_url = f"{protocol}://{self.server_url.replace('https://', '').replace('http://', '')}/xmpp-websocket"
        
        try:
            self.websocket = await websockets.connect(ws_url)
            
            # Send join message
            join_msg = {
                "action": "join",
                "room": room_name
            }
            await self.websocket.send(json.dumps(join_msg))
            
            # Start listening for messages
            asyncio.create_task(self._websocket_listener())
            
            logger.info(f"Connected to websocket for room {room_name}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to websocket: {str(e)}")
            return False
    
    async def _websocket_listener(self):
        """Listen for incoming websocket messages."""
        try:
            while True:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Process different message types
                if data.get("type") == "participant_joined":
                    if self.on_participant_joined:
                        self.on_participant_joined(data["room"], data["participant"])
                
                elif data.get("type") == "participant_left":
                    if self.on_participant_left:
                        self.on_participant_left(data["room"], data["participant"])
                
                elif data.get("type") == "message":
                    if self.on_message_received:
                        self.on_message_received(data["room"], data["from"], data["message"])
                
                # Handle other message types as needed
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Websocket connection closed")
        except Exception as e:
            logger.error(f"Error in websocket listener: {str(e)}")
    
    def disconnect(self):
        """Disconnect from Jitsi server and clean up resources."""
        self.connected = False
        # Clean up websocket connection in async context
        if self.websocket:
            asyncio.create_task(self.websocket.close())
        
        logger.info("Disconnected from Jitsi server")