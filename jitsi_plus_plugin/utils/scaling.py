"""
Scaling utilities for handling high loads and many concurrent users.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

class ScalingManager:
    """
    Manager for automatic scaling of resources.
    Handles load balancing and resource allocation for high concurrency.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the scaling manager.
        
        Args:
            config (Dict[str, Any], optional): Scaling configuration.
        """
        self.config = config or {}
        
        # Default configuration
        self.auto_scaling = self.config.get("auto_scaling", True)
        self.max_participants_per_server = self.config.get("max_participants_per_server", 100)
        self.monitor_interval_seconds = self.config.get("monitor_interval_seconds", 30)
        
        # Server management
        self.jitsi_servers = []
        self.media_servers = []
        
        # Load tracking
        self.server_loads = {}
        self.room_allocations = {}
        
        # Monitoring thread
        self.monitor_thread = None
        self.is_monitoring = False
    
    def initialize(self) -> bool:
        """
        Initialize the scaling manager.
        
        Returns:
            bool: True if initialized successfully, False otherwise.
        """
        # Add initial servers
        if "initial_jitsi_servers" in self.config:
            for server_config in self.config["initial_jitsi_servers"]:
                self.add_jitsi_server(server_config)
        
        if "initial_media_servers" in self.config:
            for server_config in self.config["initial_media_servers"]:
                self.add_media_server(server_config)
        
        # Start monitoring if auto-scaling is enabled
        if self.auto_scaling:
            self.start_monitoring()
        
        logger.info("Scaling manager initialized")
        return True
    
    def add_jitsi_server(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a Jitsi server to the pool.
        
        Args:
            server_config (Dict[str, Any]): Server configuration.
            
        Returns:
            Dict[str, Any]: Server information.
        """
        server_id = server_config.get("id") or f"jitsi-{len(self.jitsi_servers) + 1}"
        
        server_info = {
            "id": server_id,
            "url": server_config.get("url"),
            "capacity": server_config.get("capacity", self.max_participants_per_server),
            "current_load": 0,
            "rooms": [],
            "added_at": time.time(),
            "status": "active"
        }
        
        self.jitsi_servers.append(server_info)
        self.server_loads[server_id] = 0
        
        logger.info(f"Added Jitsi server: {server_id} ({server_info['url']})")
        return server_info
    
    def add_media_server(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a media server to the pool.
        
        Args:
            server_config (Dict[str, Any]): Server configuration.
            
        Returns:
            Dict[str, Any]: Server information.
        """
        server_id = server_config.get("id") or f"media-{len(self.media_servers) + 1}"
        
        server_info = {
            "id": server_id,
            "url": server_config.get("url"),
            "rtmp_port": server_config.get("rtmp_port", 1935),
            "capacity": server_config.get("capacity", 100),  # Streams capacity
            "current_load": 0,
            "streams": [],
            "added_at": time.time(),
            "status": "active"
        }
        
        self.media_servers.append(server_info)
        self.server_loads[server_id] = 0
        
        logger.info(f"Added media server: {server_id} ({server_info['url']})")
        return server_info
    
    def allocate_jitsi_server(self, room_id: str, expected_participants: int = 10) -> Optional[Dict[str, Any]]:
        """
        Allocate a Jitsi server for a room.
        
        Args:
            room_id (str): ID of the room.
            expected_participants (int): Expected number of participants.
            
        Returns:
            Optional[Dict[str, Any]]: Server information or None if no server available.
        """
        # Find least loaded server with enough capacity
        available_servers = [
            server for server in self.jitsi_servers 
            if server["status"] == "active" and 
            (server["current_load"] + expected_participants) <= server["capacity"]
        ]
        
        if not available_servers:
            if self.auto_scaling:
                # Try to provision a new server
                logger.info("No available Jitsi servers, attempting to provision a new one")
                new_server = self._provision_jitsi_server()
                if new_server:
                    available_servers.append(new_server)
            
            if not available_servers:
                logger.error(f"No available Jitsi servers for room {room_id}")
                return None
        
        # Sort by current load
        available_servers.sort(key=lambda s: s["current_load"])
        
        # Allocate the least loaded server
        server = available_servers[0]
        
        # Update server load
        server["current_load"] += expected_participants
        server["rooms"].append(room_id)
        self.server_loads[server["id"]] = server["current_load"] / server["capacity"]
        
        # Record allocation
        self.room_allocations[room_id] = {
            "server_id": server["id"],
            "server_type": "jitsi",
            "allocated_at": time.time(),
            "expected_participants": expected_participants
        }
        
        logger.info(f"Allocated Jitsi server {server['id']} for room {room_id}")
        return server
    
    def allocate_media_server(self, stream_id: str, expected_viewers: int = 100) -> Optional[Dict[str, Any]]:
        """
        Allocate a media server for a stream.
        
        Args:
            stream_id (str): ID of the stream.
            expected_viewers (int): Expected number of viewers.
            
        Returns:
            Optional[Dict[str, Any]]: Server information or None if no server available.
        """
        # Find least loaded server with enough capacity
        available_servers = [
            server for server in self.media_servers 
            if server["status"] == "active" and 
            (server["current_load"] + 1) <= server["capacity"]
        ]
        
        if not available_servers:
            if self.auto_scaling:
                # Try to provision a new server
                logger.info("No available media servers, attempting to provision a new one")
                new_server = self._provision_media_server()
                if new_server:
                    available_servers.append(new_server)
            
            if not available_servers:
                logger.error(f"No available media servers for stream {stream_id}")
                return None
        
        # Sort by current load
        available_servers.sort(key=lambda s: s["current_load"])
        
        # Allocate the least loaded server
        server = available_servers[0]
        
        # Update server load (add 1 for the stream itself)
        server["current_load"] += 1
        server["streams"].append(stream_id)
        self.server_loads[server["id"]] = server["current_load"] / server["capacity"]
        
        # Record allocation
        self.room_allocations[stream_id] = {
            "server_id": server["id"],
            "server_type": "media",
            "allocated_at": time.time(),
            "expected_viewers": expected_viewers
        }
        
        logger.info(f"Allocated media server {server['id']} for stream {stream_id}")
        return server
    
    def deallocate_server(self, resource_id: str) -> bool:
        """
        Deallocate a server for a room or stream.
        
        Args:
            resource_id (str): ID of the room or stream.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if resource_id not in self.room_allocations:
            logger.warning(f"No allocation found for resource: {resource_id}")
            return False
        
        allocation = self.room_allocations[resource_id]
        server_id = allocation["server_id"]
        server_type = allocation["server_type"]
        
        # Find server
        server = None
        if server_type == "jitsi":
            for s in self.jitsi_servers:
                if s["id"] == server_id:
                    server = s
                    break
        elif server_type == "media":
            for s in self.media_servers:
                if s["id"] == server_id:
                    server = s
                    break
        
        if not server:
            logger.warning(f"Server not found: {server_id}")
            del self.room_allocations[resource_id]
            return False
        
        # Update server load
        if server_type == "jitsi":
            server["current_load"] -= allocation.get("expected_participants", 0)
            if resource_id in server["rooms"]:
                server["rooms"].remove(resource_id)
        elif server_type == "media":
            server["current_load"] -= 1  # Remove the stream itself
            if resource_id in server["streams"]:
                server["streams"].remove(resource_id)
        
        # Update load percentage
        self.server_loads[server_id] = max(0, server["current_load"] / server["capacity"])
        
        # Remove allocation
        del self.room_allocations[resource_id]
        
        logger.info(f"Deallocated server {server_id} for resource {resource_id}")
        return True
    
    def start_monitoring(self) -> bool:
        """
        Start monitoring server loads.
        
        Returns:
            bool: True if started successfully, False otherwise.
        """
        if self.is_monitoring:
            logger.warning("Monitoring is already running")
            return False
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Started server load monitoring")
        return True
    
    def stop_monitoring(self) -> bool:
        """
        Stop monitoring server loads.
        
        Returns:
            bool: True if stopped successfully, False otherwise.
        """
        if not self.is_monitoring:
            logger.warning("Monitoring is not running")
            return False
        
        self.is_monitoring = False
        
        logger.info("Stopped server load monitoring")
        return True
    
    def _monitor_loop(self):
        """Monitor server loads and scale as needed."""
        while self.is_monitoring:
            try:
                # Check Jitsi server loads
                for server in self.jitsi_servers:
                    if server["status"] == "active":
                        # Update load percentage
                        load_percentage = server["current_load"] / server["capacity"]
                        self.server_loads[server["id"]] = load_percentage
                        
                        # Check if server is overloaded
                        if load_percentage > 0.9:  # 90% capacity
                            logger.warning(f"Jitsi server {server['id']} is overloaded: {load_percentage:.2%}")
                            
                            if self.auto_scaling:
                                # Provision a new server
                                logger.info("Auto-scaling: Provisioning new Jitsi server")
                                self._provision_jitsi_server()
                
                # Check media server loads
                for server in self.media_servers:
                    if server["status"] == "active":
                        # Update load percentage
                        load_percentage = server["current_load"] / server["capacity"]
                        self.server_loads[server["id"]] = load_percentage
                        
                        # Check if server is overloaded
                        if load_percentage > 0.9:  # 90% capacity
                            logger.warning(f"Media server {server['id']} is overloaded: {load_percentage:.2%}")
                            
                            if self.auto_scaling:
                                # Provision a new server
                                logger.info("Auto-scaling: Provisioning new media server")
                                self._provision_media_server()
                
                # Clean up unused servers
                self._clean_up_servers()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
            
            # Sleep until next interval
            time.sleep(self.monitor_interval_seconds)
    
    def _provision_jitsi_server(self) -> Optional[Dict[str, Any]]:
        """
        Provision a new Jitsi server.
        
        Returns:
            Optional[Dict[str, Any]]: Server information or None if provisioning failed.
        """
        # This would be implemented to integrate with your cloud provider
        # For now, just return None to indicate provisioning is not implemented
        logger.warning("Jitsi server provisioning not implemented")
        return None
    
    def _provision_media_server(self) -> Optional[Dict[str, Any]]:
        """
        Provision a new media server.
        
        Returns:
            Optional[Dict[str, Any]]: Server information or None if provisioning failed.
        """
        # This would be implemented to integrate with your cloud provider
        # For now, just return None to indicate provisioning is not implemented
        logger.warning("Media server provisioning not implemented")
        return None
    
    def _clean_up_servers(self):
        """Clean up unused servers."""
        # Check for idle Jitsi servers
        for server in self.jitsi_servers:
            if server["status"] == "active" and not server["rooms"]:
                # Server has no rooms
                idle_time = time.time() - max([
                    allocation["allocated_at"] 
                    for resource_id, allocation in self.room_allocations.items()
                    if allocation["server_id"] == server["id"] and allocation["server_type"] == "jitsi"
                ] or [server["added_at"]])
                
                # If server has been idle for over an hour and we have more than one server
                if idle_time > 3600 and len([s for s in self.jitsi_servers if s["status"] == "active"]) > 1:
                    logger.info(f"Deactivating idle Jitsi server: {server['id']}")
                    server["status"] = "inactive"
        
        # Check for idle media servers
        for server in self.media_servers:
            if server["status"] == "active" and not server["streams"]:
                # Server has no streams
                idle_time = time.time() - max([
                    allocation["allocated_at"] 
                    for resource_id, allocation in self.room_allocations.items()
                    if allocation["server_id"] == server["id"] and allocation["server_type"] == "media"
                ] or [server["added_at"]])
                
                # If server has been idle for over an hour and we have more than one server
                if idle_time > 3600 and len([s for s in self.media_servers if s["status"] == "active"]) > 1:
                    logger.info(f"Deactivating idle media server: {server['id']}")
                    server["status"] = "inactive"