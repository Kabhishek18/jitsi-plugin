"""
Video on Demand (VOD) controller for managing VOD content.
"""

import logging
import os
import uuid
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

class VideoOnDemand:
    """
    Controller for managing Video on Demand (VOD) content.
    Handles video uploads, playback, and advertisement integration.
    """
    
    def __init__(self, media_server):
        """
        Initialize the VOD controller.
        
        Args:
            media_server: Media server instance.
        """
        self.media_server = media_server
        self.vod_playlists = {}
    
    def create_vod_entry(self, name: str, file_path: str) -> Dict[str, Any]:
        """
        Create a VOD entry from a file.
        
        Args:
            name (str): Name for the VOD entry.
            file_path (str): Path to video file.
            
        Returns:
            Dict[str, Any]: VOD entry information.
        """
        # Create VOD entry in media server
        vod_info = self.media_server.create_vod_entry(name, file_path)
        
        logger.info(f"Created VOD entry: {name} ({vod_info['id']})")
        return vod_info
    
    def get_vod_info(self, vod_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a VOD entry.
        
        Args:
            vod_id (str): ID of the VOD entry.
            
        Returns:
            Optional[Dict[str, Any]]: VOD entry information or None if not found.
        """
        return self.media_server.get_vod_info(vod_id)
    
    def list_vod_entries(self) -> List[Dict[str, Any]]:
        """
        List all VOD entries.
        
        Returns:
            List[Dict[str, Any]]: List of VOD entry information.
        """
        return self.media_server.list_vod_entries()
    
    def delete_vod_entry(self, vod_id: str, delete_file: bool = False) -> bool:
        """
        Delete a VOD entry.
        
        Args:
            vod_id (str): ID of the VOD entry.
            delete_file (bool): Whether to delete the physical file as well.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        return self.media_server.delete_vod_entry(vod_id, delete_file)
    
    def configure_ad_settings(self, vod_id: str, ad_config: Dict[str, Any]) -> bool:
        """
        Configure advertisement settings for a VOD entry.
        
        Args:
            vod_id (str): ID of the VOD entry.
            ad_config (Dict[str, Any]): Advertisement configuration.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        return self.media_server.configure_ad_settings(vod_id, ad_config)
    
    def create_playlist(self, name: str, vod_ids: List[str] = None) -> Dict[str, Any]:
        """
        Create a VOD playlist.
        
        Args:
            name (str): Name for the playlist.
            vod_ids (List[str], optional): List of VOD IDs to include.
            
        Returns:
            Dict[str, Any]: Playlist information.
        """
        playlist_id = str(uuid.uuid4())
        
        playlist_info = {
            "id": playlist_id,
            "name": name,
            "created_at": self.media_server.active_streams.get("time", 0) or 0,
            "vod_entries": [],
            "ad_config": None
        }
        
        # Add VOD entries if provided
        if vod_ids:
            for vod_id in vod_ids:
                vod_info = self.media_server.get_vod_info(vod_id)
                if vod_info:
                    playlist_info["vod_entries"].append(vod_info)
        
        # Store playlist
        self.vod_playlists[playlist_id] = playlist_info
        
        logger.info(f"Created VOD playlist: {name} ({playlist_id})")
        return playlist_info
    
    def add_to_playlist(self, playlist_id: str, vod_id: str) -> bool:
        """
        Add a VOD entry to a playlist.
        
        Args:
            playlist_id (str): ID of the playlist.
            vod_id (str): ID of the VOD entry.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if playlist_id not in self.vod_playlists:
            logger.warning(f"Playlist not found: {playlist_id}")
            return False
        
        vod_info = self.media_server.get_vod_info(vod_id)
        if not vod_info:
            logger.warning(f"VOD entry not found: {vod_id}")
            return False
        
        # Add VOD to playlist
        playlist_info = self.vod_playlists[playlist_id]
        
        # Check if already in playlist
        for entry in playlist_info["vod_entries"]:
            if entry["id"] == vod_id:
                logger.warning(f"VOD entry already in playlist: {vod_id}")
                return True
        
        playlist_info["vod_entries"].append(vod_info)
        
        logger.info(f"Added VOD {vod_id} to playlist {playlist_id}")
        return True
    
    def remove_from_playlist(self, playlist_id: str, vod_id: str) -> bool:
        """
        Remove a VOD entry from a playlist.
        
        Args:
            playlist_id (str): ID of the playlist.
            vod_id (str): ID of the VOD entry.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if playlist_id not in self.vod_playlists:
            logger.warning(f"Playlist not found: {playlist_id}")
            return False
        
        # Remove VOD from playlist
        playlist_info = self.vod_playlists[playlist_id]
        playlist_info["vod_entries"] = [entry for entry in playlist_info["vod_entries"] 
                                       if entry["id"] != vod_id]
        
        logger.info(f"Removed VOD {vod_id} from playlist {playlist_id}")
        return True
    
    def get_playlist_info(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a playlist.
        
        Args:
            playlist_id (str): ID of the playlist.
            
        Returns:
            Optional[Dict[str, Any]]: Playlist information or None if not found.
        """
        return self.vod_playlists.get(playlist_id)
    
    def list_playlists(self) -> List[Dict[str, Any]]:
        """
        List all playlists.
        
        Returns:
            List[Dict[str, Any]]: List of playlist information.
        """
        return list(self.vod_playlists.values())
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist.
        
        Args:
            playlist_id (str): ID of the playlist.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if playlist_id in self.vod_playlists:
            del self.vod_playlists[playlist_id]
            
            logger.info(f"Deleted playlist: {playlist_id}")
            return True
        
        logger.warning(f"Playlist not found: {playlist_id}")
        return False
    
    def configure_playlist_ad_settings(self, playlist_id: str, ad_config: Dict[str, Any]) -> bool:
        """
        Configure advertisement settings for a playlist.
        
        Args:
            playlist_id (str): ID of the playlist.
            ad_config (Dict[str, Any]): Advertisement configuration.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if playlist_id not in self.vod_playlists:
            logger.warning(f"Playlist not found: {playlist_id}")
            return False
        
        # Save ad configuration
        self.vod_playlists[playlist_id]["ad_config"] = {
            "pre_roll": ad_config.get("pre_roll", []),
            "mid_roll": ad_config.get("mid_roll", []),
            "post_roll": ad_config.get("post_roll", []),
            "custom": ad_config.get("custom", [])
        }
        
        logger.info(f"Configured ad settings for playlist: {playlist_id}")
        return True
    
    def create_player_config(self, vod_id: str = None, playlist_id: str = None) -> Dict[str, Any]:
        """
        Create player configuration for a VOD entry or playlist.
        
        Args:
            vod_id (str, optional): ID of the VOD entry.
            playlist_id (str, optional): ID of the playlist.
            
        Returns:
            Dict[str, Any]: Player configuration.
        """
        if not vod_id and not playlist_id:
            raise ValueError("Either vod_id or playlist_id must be provided")
        
        if vod_id and playlist_id:
            raise ValueError("Only one of vod_id or playlist_id should be provided")
        
        player_config = {
            "type": "vod" if vod_id else "playlist",
            "autoplay": True,
            "controls": True,
            "responsive": True,
            "fluid": True,
            "sources": [],
            "ad_config": None
        }
        
        if vod_id:
            # Single VOD entry
            vod_info = self.media_server.get_vod_info(vod_id)
            if not vod_info:
                raise ValueError(f"VOD entry not found: {vod_id}")
            
            player_config["sources"].append({
                "src": vod_info["url"],
                "type": "video/mp4"
            })
            
            player_config["ad_config"] = vod_info.get("ad_config")
        
        else:
            # Playlist
            playlist_info = self.vod_playlists.get(playlist_id)
            if not playlist_info:
                raise ValueError(f"Playlist not found: {playlist_id}")
            
            for vod_info in playlist_info["vod_entries"]:
                player_config["sources"].append({
                    "src": vod_info["url"],
                    "type": "video/mp4"
                })
            
            player_config["ad_config"] = playlist_info.get("ad_config")
        
        return player_config