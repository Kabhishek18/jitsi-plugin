"""
Signaling server for real-time communication.
"""

import logging
import json
import asyncio
import websockets
import threading
import uuid
from typing import Dict, Any, List, Optional, Callable, Set

logger = logging.getLogger(__name__)

class SignalingServer:
    """
    Signaling server for real-time communication between clients.
    Handles feature toggling, whiteboard events, polls, and other real-time features.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the signaling server.
        
        Args:
            config (Dict[str, Any]): Configuration for signaling server.
        """
        self.config = config
        self.host = config.get("host", "0.0.0.0")
        self.port = config.get("port", 8080)
        self.use_ssl = config.get("use_ssl", False)
        self.ssl_cert = config.get("ssl_cert", "")
        self.ssl_key = config.get("ssl_key", "")
        
        # Connection tracking
        self.active_connections = {}
        self.connection_rooms = {}
        self.room_connections = {}
        
        # State management
        self.room_states = {}
        self.features_states = {}
        
        # Server state
        self.server = None
        self.is_running = False
        self.server_thread = None
        
        # Event handlers
        self.event_handlers = {}
    
    def start(self):
        """Start the signaling server."""
        if self.is_running:
            logger.warning("Signaling server is already running")
            return
        
        self.is_running = True
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logger.info(f"Signaling server starting on {self.host}:{self.port}")
        return True
    
    def stop(self):
        """Stop the signaling server."""
        if not self.is_running:
            logger.warning("Signaling server is not running")
            return
        
        self.is_running = False
        if self.server:
            asyncio.run(self._stop_server())
        
        logger.info("Signaling server stopped")
        return True
    
    def _run_server(self):
        """Run the WebSocket server in a separate thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        ssl_context = None
        if self.use_ssl and self.ssl_cert and self.ssl_key:
            import ssl
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.ssl_cert, self.ssl_key)
        
        start_server = websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ssl=ssl_context
        )
        
        self.server = loop.run_until_complete(start_server)
        loop.run_forever()
    
    async def _stop_server(self):
        """Stop the WebSocket server."""
        self.server.close()
        await self.server.wait_closed()
    
    async def _handle_connection(self, websocket, path):
        """
        Handle new WebSocket connections.
        
        Args:
            websocket: WebSocket connection object.
            path: Connection path.
        """
        # Generate connection ID
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "connectionId": connection_id
            }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(connection_id, websocket, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from connection {connection_id}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON"
                    }))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {connection_id}")
        finally:
            # Clean up connection
            await self._handle_disconnect(connection_id)
    
    async def _handle_message(self, connection_id: str, websocket, data: Dict[str, Any]):
        """
        Handle incoming messages from clients.
        
        Args:
            connection_id (str): ID of the client connection.
            websocket: WebSocket connection object.
            data (Dict[str, Any]): Message data.
        """
        message_type = data.get("type")
        
        if message_type == "join":
            # Join a room
            room_id = data.get("roomId")
            user_info = data.get("userInfo", {})
            
            if not room_id:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Room ID is required to join"
                }))
                return
            
            await self._handle_join(connection_id, room_id, user_info)
        
        elif message_type == "leave":
            # Leave a room
            room_id = data.get("roomId")
            
            if not room_id:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Room ID is required to leave"
                }))
                return
            
            await self._handle_leave(connection_id, room_id)
        
        elif message_type == "feature":
            # Toggle a feature
            room_id = data.get("roomId")
            feature = data.get("feature")
            enabled = data.get("enabled")
            target = data.get("target", "room")  # "room" or connection ID
            
            if not all([room_id, feature, enabled is not None]):
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Room ID, feature, and enabled state are required"
                }))
                return
            
            await self._handle_feature_toggle(connection_id, room_id, feature, enabled, target)
        
        elif message_type == "whiteboard":
            # Whiteboard event
            room_id = data.get("roomId")
            event = data.get("event")
            
            if not all([room_id, event]):
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Room ID and event are required for whiteboard events"
                }))
                return
            
            await self._handle_whiteboard_event(connection_id, room_id, event)
        
        elif message_type == "poll":
            # Poll event
            room_id = data.get("roomId")
            poll_action = data.get("action")
            poll_data = data.get("data", {})
            
            if not all([room_id, poll_action]):
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Room ID and poll action are required for poll events"
                }))
                return
            
            await self._handle_poll_event(connection_id, room_id, poll_action, poll_data)
        
        elif message_type == "message":
            # Chat message
            room_id = data.get("roomId")
            message_content = data.get("message")
            
            if not all([room_id, message_content]):
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Room ID and message content are required for chat messages"
                }))
                return
            
            await self._handle_chat_message(connection_id, room_id, message_content)
        
        elif message_type == "custom":
            # Custom event
            event_name = data.get("event")
            event_data = data.get("data", {})
            
            if not event_name:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Event name is required for custom events"
                }))
                return
            
            await self._handle_custom_event(connection_id, event_name, event_data)
        
        else:
            # Unknown message type
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }))
    
    async def _handle_join(self, connection_id: str, room_id: str, user_info: Dict[str, Any]):
        """
        Handle a client joining a room.
        
        Args:
            connection_id (str): ID of the client connection.
            room_id (str): ID of the room to join.
            user_info (Dict[str, Any]): Information about the user.
        """
        # Create room if it doesn't exist
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
            self.room_states[room_id] = {
                "features": {
                    "video": True,
                    "audio": True,
                    "chat": True,
                    "screen_sharing": True,
                    "polls": True,
                    "whiteboard": True,
                    "settings": True,
                    "background": True
                },
                "whiteboard": {
                    "elements": []
                },
                "polls": [],
                "messages": []
            }
        
        # Add connection to room
        self.room_connections[room_id].add(connection_id)
        
        # Store room for connection
        if connection_id not in self.connection_rooms:
            self.connection_rooms[connection_id] = set()
        self.connection_rooms[connection_id].add(room_id)
        
        # Store user info
        self.features_states[connection_id] = {
            "user_info": user_info,
            "features": {
                "video": True,
                "audio": True,
                "screen_sharing": False
            }
        }
        
        # Notify other clients in the room
        await self._broadcast_to_room(room_id, {
            "type": "user_joined",
            "roomId": room_id,
            "userId": connection_id,
            "userInfo": user_info
        }, exclude=[connection_id])
        
        # Send room state to the new client
        websocket = self.active_connections.get(connection_id)
        if websocket:
            # Get user list
            users = []
            for conn_id in self.room_connections[room_id]:
                if conn_id in self.features_states:
                    users.append({
                        "id": conn_id,
                        "info": self.features_states[conn_id]["user_info"],
                        "features": self.features_states[conn_id]["features"]
                    })
            
            await websocket.send(json.dumps({
                "type": "room_state",
                "roomId": room_id,
                "state": self.room_states[room_id],
                "users": users
            }))
        
        logger.info(f"Connection {connection_id} joined room {room_id}")
    
    async def _handle_leave(self, connection_id: str, room_id: str):
        """
        Handle a client leaving a room.
        
        Args:
            connection_id (str): ID of the client connection.
            room_id (str): ID of the room to leave.
        """
        if room_id in self.room_connections and connection_id in self.room_connections[room_id]:
            # Remove connection from room
            self.room_connections[room_id].remove(connection_id)
            
            # Remove room from connection
            if connection_id in self.connection_rooms and room_id in self.connection_rooms[connection_id]:
                self.connection_rooms[connection_id].remove(room_id)
            
            # Notify other clients in the room
            await self._broadcast_to_room(room_id, {
                "type": "user_left",
                "roomId": room_id,
                "userId": connection_id
            })
            
            # Clean up empty room
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
                if room_id in self.room_states:
                    del self.room_states[room_id]
                logger.info(f"Room {room_id} closed (no users left)")
            
            logger.info(f"Connection {connection_id} left room {room_id}")
    
    async def _handle_disconnect(self, connection_id: str):
        """
        Handle a client disconnecting.
        
        Args:
            connection_id (str): ID of the client connection.
        """
        # Leave all rooms
        if connection_id in self.connection_rooms:
            rooms = list(self.connection_rooms[connection_id])
            for room_id in rooms:
                await self._handle_leave(connection_id, room_id)
            
            del self.connection_rooms[connection_id]
        
        # Clean up connection
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Clean up feature states
        if connection_id in self.features_states:
            del self.features_states[connection_id]
        
        logger.info(f"Connection {connection_id} disconnected")
    
    async def _handle_feature_toggle(self, connection_id: str, room_id: str, 
                                    feature: str, enabled: bool, target: str):
        """
        Handle toggling a feature.
        
        Args:
            connection_id (str): ID of the client connection.
            room_id (str): ID of the room.
            feature (str): Feature to toggle.
            enabled (bool): Whether the feature is enabled.
            target (str): Target for the toggle ('room' or connection ID).
        """
        if room_id not in self.room_connections:
            logger.warning(f"Feature toggle for non-existent room: {room_id}")
            return
        
        if target == "room":
            # Toggle room feature
            if room_id in self.room_states and feature in self.room_states[room_id]["features"]:
                self.room_states[room_id]["features"][feature] = enabled
                
                # Broadcast to all clients in the room
                await self._broadcast_to_room(room_id, {
                    "type": "feature_toggle",
                    "roomId": room_id,
                    "feature": feature,
                    "enabled": enabled,
                    "target": "room",
                    "userId": connection_id  # User who toggled the feature
                })
                
                logger.info(f"Room {room_id} feature {feature} set to {enabled} by {connection_id}")
        else:
            # Toggle user feature
            target_conn_id = target
            if target_conn_id in self.features_states and feature in self.features_states[target_conn_id]["features"]:
                self.features_states[target_conn_id]["features"][feature] = enabled
                
                # Broadcast to all clients in the room
                await self._broadcast_to_room(room_id, {
                    "type": "feature_toggle",
                    "roomId": room_id,
                    "feature": feature,
                    "enabled": enabled,
                    "target": target_conn_id,
                    "userId": connection_id  # User who toggled the feature
                })
                
                logger.info(f"User {target_conn_id} feature {feature} set to {enabled} by {connection_id}")
    
    async def _handle_whiteboard_event(self, connection_id: str, room_id: str, event: Dict[str, Any]):
        """
        Handle whiteboard events.
        
        Args:
            connection_id (str): ID of the client connection.
            room_id (str): ID of the room.
            event (Dict[str, Any]): Whiteboard event data.
        """
        if room_id not in self.room_connections:
            logger.warning(f"Whiteboard event for non-existent room: {room_id}")
            return
        
        # Process whiteboard event
        event_type = event.get("type")
        
        if event_type == "add":
            # Add element to whiteboard
            element = event.get("element")
            if element and room_id in self.room_states:
                self.room_states[room_id]["whiteboard"]["elements"].append(element)
        
        elif event_type == "update":
            # Update element on whiteboard
            element_id = event.get("elementId")
            updates = event.get("updates")
            
            if element_id and updates and room_id in self.room_states:
                for i, element in enumerate(self.room_states[room_id]["whiteboard"]["elements"]):
                    if element.get("id") == element_id:
                        self.room_states[room_id]["whiteboard"]["elements"][i].update(updates)
                        break
        
        elif event_type == "delete":
            # Delete element from whiteboard
            element_id = event.get("elementId")
            
            if element_id and room_id in self.room_states:
                self.room_states[room_id]["whiteboard"]["elements"] = [
                    element for element in self.room_states[room_id]["whiteboard"]["elements"]
                    if element.get("id") != element_id
                ]
        
        elif event_type == "clear":
            # Clear whiteboard
            if room_id in self.room_states:
                self.room_states[room_id]["whiteboard"]["elements"] = []
        
        # Broadcast whiteboard event to all clients in the room
        await self._broadcast_to_room(room_id, {
            "type": "whiteboard_event",
            "roomId": room_id,
            "userId": connection_id,
            "event": event
        })
    
    async def _handle_poll_event(self, connection_id: str, room_id: str, 
                                poll_action: str, poll_data: Dict[str, Any]):
        """
        Handle poll events.
        
        Args:
            connection_id (str): ID of the client connection.
            room_id (str): ID of the room.
            poll_action (str): Poll action ('create', 'vote', 'end').
            poll_data (Dict[str, Any]): Poll data.
        """
        if room_id not in self.room_connections:
            logger.warning(f"Poll event for non-existent room: {room_id}")
            return
        
        if poll_action == "create":
            # Create new poll
            poll_id = str(uuid.uuid4())
            poll = {
                "id": poll_id,
                "creator": connection_id,
                "question": poll_data.get("question", ""),
                "options": poll_data.get("options", []),
                "created_at": asyncio.get_event_loop().time(),
                "active": True,
                "votes": {}
            }
            
            if room_id in self.room_states:
                self.room_states[room_id]["polls"].append(poll)
            
            # Broadcast new poll to all clients in the room
            await self._broadcast_to_room(room_id, {
                "type": "poll_created",
                "roomId": room_id,
                "userId": connection_id,
                "poll": poll
            })
            
            logger.info(f"Poll created in room {room_id} by {connection_id}: {poll_id}")
        
        elif poll_action == "vote":
            # Vote in a poll
            poll_id = poll_data.get("pollId")
            option_index = poll_data.get("optionIndex")
            
            if poll_id is not None and option_index is not None and room_id in self.room_states:
                for poll in self.room_states[room_id]["polls"]:
                    if poll["id"] == poll_id and poll["active"]:
                        # Record vote
                        poll["votes"][connection_id] = option_index
                        
                        # Broadcast vote to all clients in the room
                        await self._broadcast_to_room(room_id, {
                            "type": "poll_vote",
                            "roomId": room_id,
                            "userId": connection_id,
                            "pollId": poll_id,
                            "optionIndex": option_index
                        })
                        
                        logger.info(f"Vote in poll {poll_id} by {connection_id}: option {option_index}")
                        break
        
        elif poll_action == "end":
            # End a poll
            poll_id = poll_data.get("pollId")
            
            if poll_id and room_id in self.room_states:
                for poll in self.room_states[room_id]["polls"]:
                    if poll["id"] == poll_id and poll["active"]:
                        # End the poll
                        poll["active"] = False
                        poll["ended_at"] = asyncio.get_event_loop().time()
                        
                        # Compute results
                        results = [0] * len(poll["options"])
                        for option_index in poll["votes"].values():
                            results[option_index] += 1
                        
                        # Broadcast poll end to all clients in the room
                        await self._broadcast_to_room(room_id, {
                            "type": "poll_ended",
                            "roomId": room_id,
                            "userId": connection_id,
                            "pollId": poll_id,
                            "results": results
                        })
                        
                        logger.info(f"Poll {poll_id} ended by {connection_id}")
                        break
    
    async def _handle_chat_message(self, connection_id: str, room_id: str, message_content: str):
        """
        Handle chat messages.
        
        Args:
            connection_id (str): ID of the client connection.
            room_id (str): ID of the room.
            message_content (str): Message content.
        """
        if room_id not in self.room_connections:
            logger.warning(f"Chat message for non-existent room: {room_id}")
            return
        
        # Create message
        message = {
            "id": str(uuid.uuid4()),
            "sender": connection_id,
            "content": message_content,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Store message
        if room_id in self.room_states:
            self.room_states[room_id]["messages"].append(message)
        
        # Broadcast message to all clients in the room
        await self._broadcast_to_room(room_id, {
            "type": "chat_message",
            "roomId": room_id,
            "message": message
        })
        
        logger.info(f"Chat message in room {room_id} from {connection_id}")
    
    async def _handle_custom_event(self, connection_id: str, event_name: str, event_data: Dict[str, Any]):
        """
        Handle custom events.
        
        Args:
            connection_id (str): ID of the client connection.
            event_name (str): Custom event name.
            event_data (Dict[str, Any]): Custom event data.
        """
        # Check if we have a handler for this event
        if event_name in self.event_handlers:
            # Call event handler
            result = self.event_handlers[event_name](connection_id, event_data)
            
            # Send response if needed
            if result is not None:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    await websocket.send(json.dumps({
                        "type": "custom_event_response",
                        "event": event_name,
                        "data": result
                    }))
        else:
            logger.warning(f"No handler for custom event: {event_name}")
    
    async def _broadcast_to_room(self, room_id: str, message: Dict[str, Any], exclude: List[str] = None):
        """
        Broadcast a message to all clients in a room.
        
        Args:
            room_id (str): ID of the room.
            message (Dict[str, Any]): Message to broadcast.
            exclude (List[str], optional): List of connection IDs to exclude.
        """
        if room_id not in self.room_connections:
            return
        
        exclude = exclude or []
        
        # Convert message to JSON
        message_json = json.dumps(message)
        
        # Send to all connections in the room
        for connection_id in self.room_connections[room_id]:
            if connection_id not in exclude:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    try:
                        await websocket.send(message_json)
                    except Exception as e:
                        logger.error(f"Error sending message to {connection_id}: {str(e)}")
    
    def register_event_handler(self, event_name: str, handler: Callable):
        """
        Register a handler for custom events.
        
        Args:
            event_name (str): Custom event name.
            handler (Callable): Event handler function.
        """
        self.event_handlers[event_name] = handler
        logger.info(f"Registered handler for custom event: {event_name}")
    
    def unregister_event_handler(self, event_name: str):
        """
        Unregister a handler for custom events.
        
        Args:
            event_name (str): Custom event name.
        """
        if event_name in self.event_handlers:
            del self.event_handlers[event_name]
            logger.info(f"Unregistered handler for custom event: {event_name}")