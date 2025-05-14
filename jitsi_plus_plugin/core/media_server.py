"""
Media server module for handling streaming, recording, and VOD functionality.
"""

import logging
import requests
import json
import os
import time
import subprocess
import threading
import asyncio
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

class MediaServer:
    """
    Media server component for handling video streaming, recording,
    and video-on-demand functionality.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the media server.
        
        Args:
            config (Dict[str, Any]): Configuration for media server.
        """
        self.config = config
        self.server_url = config.get("server_url", "https://media.example.com")
        self.rtmp_port = config.get("rtmp_port", 1935)
        self.hls_segment_duration = config.get("hls_segment_duration", 4)
        self.recording_enabled = config.get("recording_enabled", True)
        self.recording_directory = config.get("recording_directory", "/var/recordings")
        
        # Streaming management
        self.active_streams = {}
        self.vod_entries = {}
        self.recording_processes = {}
        
        # Connection status
        self.connected = False
        
        # Callbacks
        self.on_stream_started = None
        self.on_stream_ended = None
        self.on_recording_completed = None
    
    def initialize(self) -> bool:
        """
        Initialize the media server connection.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Test connection to media server
            response = requests.get(f"{self.server_url}/api/status", timeout=5)
            if response.status_code == 200:
                logger.info(f"Successfully connected to media server at {self.server_url}")
                self.connected = True
                
                # Create recording directory if it doesn't exist and is enabled
                if self.recording_enabled and not os.path.exists(self.recording_directory):
                    os.makedirs(self.recording_directory, exist_ok=True)
                
                return True
            else:
                logger.error(f"Failed to connect to media server: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to media server: {str(e)}")
            return False
    
    def create_stream(self, stream_name: str, stream_type: str = "live") -> Dict[str, Any]:
        """
        Create a new stream.
        
        Args:
            stream_name (str): Name for the stream.
            stream_type (str): Type of stream ('live', 'record', 'live_record').
            
        Returns:
            Dict[str, Any]: Stream information dictionary.
        """
        stream_key = f"{int(time.time())}-{stream_name}"
        
        stream_info = {
            "name": stream_name,
            "key": stream_key,
            "type": stream_type,
            "created_at": time.time(),
            "status": "created",
            "rtmp_url": f"rtmp://{self.server_url.replace('https://', '').replace('http://', '')}:{self.rtmp_port}/live/{stream_key}",
            "hls_url": f"{self.server_url}/hls/{stream_key}.m3u8",
            "recording_path": None
        }
        
        # Set recording path if applicable
        if stream_type in ["record", "live_record"] and self.recording_enabled:
            stream_info["recording_path"] = os.path.join(self.recording_directory, f"{stream_key}.mp4")
        
        # Add to active streams
        self.active_streams[stream_key] = stream_info
        
        logger.info(f"Created stream: {stream_name} ({stream_key})")
        return stream_info
    
    def start_stream(self, stream_key: str) -> bool:
        """
        Start a previously created stream.
        
        Args:
            stream_key (str): Key of the stream to start.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if stream_key in self.active_streams:
            stream_info = self.active_streams[stream_key]
            
            # Start recording if needed
            if stream_info["type"] in ["record", "live_record"] and self.recording_enabled:
                self._start_recording(stream_key)
            
            # Update stream status
            stream_info["status"] = "active"
            stream_info["started_at"] = time.time()
            
            # Trigger callback if set
            if self.on_stream_started:
                self.on_stream_started(stream_info)
            
            logger.info(f"Started stream: {stream_info['name']} ({stream_key})")
            return True
        
        logger.warning(f"Failed to start stream: {stream_key} not found")
        return False
    
    def stop_stream(self, stream_key: str) -> bool:
        """
        Stop an active stream.
        
        Args:
            stream_key (str): Key of the stream to stop.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if stream_key in self.active_streams:
            stream_info = self.active_streams[stream_key]
            
            # Stop recording if active
            if stream_key in self.recording_processes:
                self._stop_recording(stream_key)
            
            # Update stream status
            stream_info["status"] = "stopped"
            stream_info["ended_at"] = time.time()
            
            # Move to VOD if recorded
            if stream_info["recording_path"] and os.path.exists(stream_info["recording_path"]):
                vod_id = f"vod-{stream_key}"
                self.vod_entries[vod_id] = {
                    "id": vod_id,
                    "name": stream_info["name"],
                    "source_stream": stream_key,
                    "created_at": time.time(),
                    "duration": stream_info.get("ended_at", time.time()) - stream_info.get("started_at", time.time()),
                    "file_path": stream_info["recording_path"],
                    "url": f"{self.server_url}/vod/{vod_id}.mp4"
                }
                
                logger.info(f"Created VOD entry for stream: {stream_info['name']} ({vod_id})")
            
            # Trigger callback if set
            if self.on_stream_ended:
                self.on_stream_ended(stream_info)
            
            logger.info(f"Stopped stream: {stream_info['name']} ({stream_key})")
            return True
        
        logger.warning(f"Failed to stop stream: {stream_key} not found")
        return False
    
    def get_stream_info(self, stream_key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a stream.
        
        Args:
            stream_key (str): Key of the stream.
            
        Returns:
            Optional[Dict[str, Any]]: Stream information or None if not found.
        """
        return self.active_streams.get(stream_key)
    
    def list_active_streams(self) -> List[Dict[str, Any]]:
        """
        List all active streams.
        
        Returns:
            List[Dict[str, Any]]: List of active stream information.
        """
        return [stream for stream in self.active_streams.values() if stream["status"] == "active"]
    
    def create_vod_entry(self, name: str, file_path: str) -> Dict[str, Any]:
        """
        Create a VOD entry manually from a file.
        
        Args:
            name (str): Name for the VOD entry.
            file_path (str): Path to video file.
            
        Returns:
            Dict[str, Any]: VOD entry information.
        """
        if not os.path.exists(file_path):
            logger.error(f"VOD file not found: {file_path}")
            raise FileNotFoundError(f"VOD file not found: {file_path}")
        
        vod_id = f"vod-{int(time.time())}-{name}"
        
        vod_info = {
            "id": vod_id,
            "name": name,
            "source_stream": None,
            "created_at": time.time(),
            "duration": None,  # Will be set after processing
            "file_path": file_path,
            "url": f"{self.server_url}/vod/{vod_id}.mp4",
            "status": "processing"
        }
        
        # Start a thread to process the file (get duration, create thumbnails, etc.)
        threading.Thread(target=self._process_vod_file, args=(vod_id, file_path)).start()
        
        # Add to VOD entries
        self.vod_entries[vod_id] = vod_info
        
        logger.info(f"Created VOD entry: {name} ({vod_id})")
        return vod_info
    
    def get_vod_info(self, vod_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a VOD entry.
        
        Args:
            vod_id (str): ID of the VOD entry.
            
        Returns:
            Optional[Dict[str, Any]]: VOD entry information or None if not found.
        """
        return self.vod_entries.get(vod_id)
    
    def list_vod_entries(self) -> List[Dict[str, Any]]:
        """
        List all VOD entries.
        
        Returns:
            List[Dict[str, Any]]: List of VOD entry information.
        """
        return list(self.vod_entries.values())
    
    def configure_ad_settings(self, vod_id: str, ad_config: Dict[str, Any]) -> bool:
        """
        Configure advertisement settings for a VOD entry.
        
        Args:
            vod_id (str): ID of the VOD entry.
            ad_config (Dict[str, Any]): Advertisement configuration.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if vod_id in self.vod_entries:
            # Save ad configuration
            self.vod_entries[vod_id]["ad_config"] = {
                "pre_roll": ad_config.get("pre_roll", []),
                "mid_roll": ad_config.get("mid_roll", []),
                "post_roll": ad_config.get("post_roll", []),
                "custom": ad_config.get("custom", [])
            }
            
            logger.info(f"Configured ad settings for VOD: {vod_id}")
            return True
        
        logger.warning(f"Failed to configure ad settings: VOD {vod_id} not found")
        return False
    
    def delete_vod_entry(self, vod_id: str, delete_file: bool = False) -> bool:
        """
        Delete a VOD entry.
        
        Args:
            vod_id (str): ID of the VOD entry.
            delete_file (bool): Whether to delete the physical file as well.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if vod_id in self.vod_entries:
            vod_info = self.vod_entries[vod_id]
            
            # Delete physical file if requested
            if delete_file and vod_info["file_path"] and os.path.exists(vod_info["file_path"]):
                try:
                    os.remove(vod_info["file_path"])
                    logger.info(f"Deleted VOD file: {vod_info['file_path']}")
                except Exception as e:
                    logger.error(f"Error deleting VOD file: {str(e)}")
            
            # Remove from VOD entries
            del self.vod_entries[vod_id]
            
            logger.info(f"Deleted VOD entry: {vod_id}")
            return True
        
        logger.warning(f"Failed to delete VOD entry: {vod_id} not found")
        return False
    
    def _start_recording(self, stream_key: str):
        """
        Start recording a stream using FFmpeg.
        
        Args:
            stream_key (str): Key of the stream to record.
        """
        if stream_key not in self.active_streams:
            return
        
        stream_info = self.active_streams[stream_key]
        output_path = stream_info["recording_path"]
        
        if not output_path:
            logger.warning(f"No recording path set for stream {stream_key}")
            return
        
        try:
            # Create FFmpeg command
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", stream_info["rtmp_url"],
                "-c:v", "copy",
                "-c:a", "copy",
                output_path
            ]
            
            # Start FFmpeg process
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
            # Save process for later termination
            self.recording_processes[stream_key] = process
            
            logger.info(f"Started recording for stream: {stream_info['name']} ({stream_key})")
        except Exception as e:
            logger.error(f"Error starting recording for stream {stream_key}: {str(e)}")
    
    def _stop_recording(self, stream_key: str):
        """
        Stop recording a stream.
        
        Args:
            stream_key (str): Key of the stream to stop recording.
        """
        if stream_key in self.recording_processes:
            process = self.recording_processes[stream_key]
            
            try:
                # Terminate FFmpeg process gracefully
                process.terminate()
                
                try:
                    # Wait for process to terminate
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired as e:
                    # If process is still running, kill it forcefully
                    process.kill()
                    logger.info(f"Force killed recording process for stream: {stream_key}")
                
                # Remove from recording processes
                del self.recording_processes[stream_key]
                
                # Trigger callback if set
                if self.on_recording_completed and stream_key in self.active_streams:
                    stream_info = self.active_streams[stream_key]
                    self.on_recording_completed(stream_info)
                
                logger.info(f"Stopped recording for stream: {stream_key}")
            except Exception as e:
                logger.error(f"Error stopping recording for stream {stream_key}: {str(e)}")

    def _process_vod_file(self, vod_id: str, file_path: str):
        """
        Process a VOD file to extract metadata.
        
        Args:
            vod_id (str): ID of the VOD entry.
            file_path (str): Path to video file.
        """
        if vod_id not in self.vod_entries:
            return
        
        try:
            # Get duration using FFprobe
            ffprobe_cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            
            result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            duration = float(result.stdout.strip())
            
            # Update VOD entry with duration
            self.vod_entries[vod_id]["duration"] = duration
            self.vod_entries[vod_id]["status"] = "ready"
            
            # Generate thumbnail
            thumbnail_path = os.path.join(os.path.dirname(file_path), f"{vod_id}_thumbnail.jpg")
            
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", file_path,
                "-ss", str(min(30, duration / 2)),  # Take thumbnail from middle or 30 seconds in
                "-vframes", "1",
                thumbnail_path
            ]
            
            subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Add thumbnail URL to VOD entry
            self.vod_entries[vod_id]["thumbnail_url"] = f"{self.server_url}/thumbnails/{os.path.basename(thumbnail_path)}"
            
            logger.info(f"Processed VOD file for {vod_id}: duration={duration}s")
        except Exception as e:
            logger.error(f"Error processing VOD file for {vod_id}: {str(e)}")
            self.vod_entries[vod_id]["status"] = "error"
    
    def shutdown(self):
        """Shutdown media server and clean up resources."""
        # Stop all recordings
        for stream_key in list(self.recording_processes.keys()):
            self._stop_recording(stream_key)
        
        # Stop all active streams
        for stream_key in list(self.active_streams.keys()):
            if self.active_streams[stream_key]["status"] == "active":
                self.stop_stream(stream_key)
        
        logger.info("Media server shutdown complete")