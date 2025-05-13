"""
Broadcast controller for managing live streams.
"""

import logging
import uuid
import time
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

class BroadcastController:
    """
    Controller for managing broadcasts and live streams.
    Integrates Jitsi with media server for broadcasting.
    """
    
    def __init__(self, jitsi_connector, media_server, signaling_server):
        """
        Initialize the broadcast controller.
        
        Args:
            jitsi_connector: Jitsi connector instance.
            media_server: Media server instance.
            signaling_server: Signaling server instance.
        """
        self.jitsi = jitsi_connector
        self.media_server = media_server
        self.signaling = signaling_server
        self.active_broadcasts = {}
    
    def create_broadcast(self, name: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new broadcast.
        
        Args:
            name (str): Name for the broadcast.
            config (Dict[str, Any], optional): Broadcast configuration.
            
        Returns:
            Dict[str, Any]: Broadcast information.
        """
        config = config or {}
        
        # Generate broadcast ID
        broadcast_id = str(uuid.uuid4())
        
        # Create Jitsi room
        room_info = self.jitsi.create_room(f"broadcast-{broadcast_id}")
        
        # Configure features
        features = config.get("features", {})
        if features:
            self.jitsi.configure_room(room_info["room_name"], features)
        
        # Create stream in media server
        stream_type = config.get("stream_type", "live_record")
        stream_info = self.media_server.create_stream(f"{name}-{broadcast_id}", stream_type)
        
        # Store broadcast information
        broadcast_info = {
            "id": broadcast_id,
            "name": name,
            "room_name": room_info["room_name"],
            "jitsi_url": self.jitsi.get_jitsi_url(room_info["room_name"]),
            "stream_key": stream_info["key"],
            "rtmp_url": stream_info["rtmp_url"],
            "hls_url": stream_info["hls_url"],
            "created_at": time.time(),
            "features": room_info["features"],
            "max_hosts": config.get("max_hosts", 10),
            "max_viewers": config.get("max_viewers", 10000),
            "hosts": {},
            "viewers": 0,
            "status": "created",
            "recording": config.get("recording", False)
        }
        
        self.active_broadcasts[broadcast_id] = broadcast_info
        
        logger.info(f"Created broadcast: {name} ({broadcast_id})")
        return broadcast_info
    
    def start_broadcast(self, broadcast_id: str) -> bool:
        """
        Start a broadcast.
        
        Args:
            broadcast_id (str): ID of the broadcast.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if broadcast_id not in self.active_broadcasts:
            logger.warning(f"Broadcast not found: {broadcast_id}")
            return False
        
        broadcast_info = self.active_broadcasts[broadcast_id]
        
        # Start stream in media server
        result = self.media_server.start_stream(broadcast_info["stream_key"])
        
        if result:
            # Update broadcast status
            broadcast_info["status"] = "live"
            broadcast_info["started_at"] = time.time()
            
            logger.info(f"Started broadcast: {broadcast_info['name']} ({broadcast_id})")
            return True
        
        return False
    
    def stop_broadcast(self, broadcast_id: str) -> bool:
        """
        Stop a broadcast.
        
        Args:
            broadcast_id (str): ID of the broadcast.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if broadcast_id not in self.active_broadcasts:
            logger.warning(f"Broadcast not found: {broadcast_id}")
            return False
        
        broadcast_info = self.active_broadcasts[broadcast_id]
        
        # Stop stream in media server
        result = self.media_server.stop_stream(broadcast_info["stream_key"])
        
        if result:
            # Update broadcast status
            broadcast_info["status"] = "ended"
            broadcast_info["ended_at"] = time.time()
            
            logger.info(f"Stopped broadcast: {broadcast_info['name']} ({broadcast_id})")
            return True
        
        return False
    
    def add_host(self, broadcast_id: str, host_name: str, host_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Add a host to a broadcast.
        
        Args:
            broadcast_id (str): ID of the broadcast.
            host_name (str): Name of the host.
            host_config (Dict[str, Any], optional): Host configuration.
            
        Returns:
            Dict[str, Any]: Host information.
        """
        if broadcast_id not in self.active_broadcasts:
            raise ValueError(f"Broadcast not found: {broadcast_id}")
        
        broadcast_info = self.active_broadcasts[broadcast_id]
        
        # Check if broadcast has reached max hosts
        if len(broadcast_info["hosts"]) >= broadcast_info["max_hosts"]:
            raise ValueError(f"Broadcast has reached maximum number of hosts: {broadcast_id}")
        
        # Join Jitsi room as host
        host_info = self.jitsi.join_room(broadcast_info["room_name"], host_name)
        
        # Configure host features
        if host_config:
            features = host_config.get("features", {})
            for feature, enabled in features.items():
                self.jitsi.toggle_participant_feature(broadcast_info["room_name"], host_info["id"], feature, enabled)
                host_info["features"][feature] = enabled
        
        # Add to broadcast hosts
        broadcast_info["hosts"][host_info["id"]] = host_info
        
        logger.info(f"Host {host_name} added to broadcast {broadcast_id}")
        return host_info
    
    def remove_host(self, broadcast_id: str, host_id: str) -> bool:
        """
        Remove a host from a broadcast.
        
        Args:
            broadcast_id (str): ID of the broadcast.
            host_id (str): ID of the host.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if broadcast_id not in self.active_broadcasts:
            logger.warning(f"Broadcast not found: {broadcast_id}")
            return False
        
        broadcast_info = self.active_broadcasts[broadcast_id]
        
        # Leave Jitsi room
        result = self.jitsi.leave_room(broadcast_info["room_name"], host_id)
        
        if result:
            # Remove from broadcast hosts
            if host_id in broadcast_info["hosts"]:
                del broadcast_info["hosts"][host_id]
            
            logger.info(f"Host {host_id} removed from broadcast {broadcast_id}")
            return True
        
        return False
    
    def get_broadcast_info(self, broadcast_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a broadcast.
        
        Args:
            broadcast_id (str): ID of the broadcast.
            
        Returns:
            Optional[Dict[str, Any]]: Broadcast information or None if not found.
        """
        return self.active_broadcasts.get(broadcast_id)
    
    def list_active_broadcasts(self) -> List[Dict[str, Any]]:
        """
        List all active broadcasts.
        
        Returns:
            List[Dict[str, Any]]: List of active broadcast information.
        """
        return [broadcast for broadcast in self.active_broadcasts.values() 
                if broadcast["status"] == "live"]
    
    def toggle_broadcast_feature(self, broadcast_id: str, feature: str, enabled: bool) -> bool:
        """
        Toggle a feature for a broadcast.
        
        Args:
            broadcast_id (str): ID of the broadcast.
            feature (str): Feature to toggle.
            enabled (bool): Whether the feature is enabled.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if broadcast_id not in self.active_broadcasts:
            logger.warning(f"Broadcast not found: {broadcast_id}")
            return False
        
        broadcast_info = self.active_broadcasts[broadcast_id]
        
        # Toggle feature in Jitsi room
        result = self.jitsi.configure_room(broadcast_info["room_name"], {feature: enabled})
        
        if result:
            # Update broadcast information
            broadcast_info["features"][feature] = enabled
            
            logger.info(f"Broadcast {broadcast_id} feature {feature} set to {enabled}")
            return True
        
        return False
    
    def toggle_host_feature(self, broadcast_id: str, host_id: str, feature: str, enabled: bool) -> bool:
        """
        Toggle a feature for a host.
        
        Args:
            broadcast_id (str): ID of the broadcast.
            host_id (str): ID of the host.
            feature (str): Feature to toggle.
            enabled (bool): Whether the feature is enabled.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if broadcast_id not in self.active_broadcasts:
            logger.warning(f"Broadcast not found: {broadcast_id}")
            return False
        
        broadcast_info = self.active_broadcasts[broadcast_id]
        
        # Toggle feature for host
        result = self.jitsi.toggle_participant_feature(broadcast_info["room_name"], host_id, feature, enabled)
        
        if result:
            # Update host information
            if host_id in broadcast_info["hosts"]:
                broadcast_info["hosts"][host_id]["features"][feature] = enabled
            
            logger.info(f"Host {host_id} feature {feature} set to {enabled} in broadcast {broadcast_id}")
            return True
        
        return False
    
    def update_viewer_count(self, broadcast_id: str, viewers: int) -> bool:
        """
        Update the viewer count for a broadcast.
        
        Args:
            broadcast_id (str): ID of the broadcast.
            viewers (int): Number of viewers.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if broadcast_id not in self.active_broadcasts:
            logger.warning(f"Broadcast not found: {broadcast_id}")
            return False
        
        # Update viewer count
        self.active_broadcasts[broadcast_id]["viewers"] = viewers
        
        logger.info(f"Updated viewer count for broadcast {broadcast_id}: {viewers}")
        return True
    
    def get_recording_url(self, broadcast_id: str) -> Optional[str]:
        """
        Get the recording URL for a broadcast.
        
        Args:
            broadcast_id (str): ID of the broadcast.
            
        Returns:
            Optional[str]: Recording URL or None if not available.
        """
        if broadcast_id not in self.active_broadcasts:
            logger.warning(f"Broadcast not found: {broadcast_id}")
            return None
        
        broadcast_info = self.active_broadcasts[broadcast_id]
        
        # Check if broadcast has ended and was recorded
        if broadcast_info["status"] == "ended" and broadcast_info["recording"]:
            # Look up VOD entry in media server
            for vod_entry in self.media_server.list_vod_entries():
                if vod_entry.get("source_stream") == broadcast_info["stream_key"]:
                    return vod_entry.get("url")
        
        return None