"""
Configuration management for Jitsi Plus Plugin.
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "jitsi": {
        "server_url": "https://meet.jit.si",
        "room_prefix": "jitsi-plus-",
        "use_ssl": True
    },
    "media_server": {
        "server_url": "https://media.example.com",
        "rtmp_port": 1935,
        "hls_segment_duration": 4,
        "recording_enabled": True,
        "recording_directory": "/var/recordings"
    },
    "signaling": {
        "host": "0.0.0.0",
        "port": 8080,
        "use_ssl": False,
        "ssl_cert": "",
        "ssl_key": ""
    },
    "scaling": {
        "auto_scaling": True,
        "max_participants_per_server": 100,
        "monitor_interval_seconds": 30
    },
    "features": {
        "whiteboard_enabled": True,
        "polls_enabled": True,
        "chat_enabled": True,
        "recording_enabled": True,
        "transcription_enabled": False
    }
}

def load_config(config_path=None):
    """
    Load configuration from file or return default configuration.
    
    Args:
        config_path (str, optional): Path to configuration file.
        
    Returns:
        dict: Configuration dictionary.
    """
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
            
            # Merge with default config
            merged_config = DEFAULT_CONFIG.copy()
            for key, section in user_config.items():
                if key in merged_config and isinstance(merged_config[key], dict):
                    merged_config[key].update(section)
                else:
                    merged_config[key] = section
            
            logger.info(f"Loaded configuration from {config_path}")
            return merged_config
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {str(e)}")
            return DEFAULT_CONFIG
    else:
        if config_path:
            logger.warning(f"Config file {config_path} not found, using default configuration")
        return DEFAULT_CONFIG

def save_config(config, config_path):
    """
    Save configuration to file.
    
    Args:
        config (dict): Configuration dictionary.
        config_path (str): Path to save configuration file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"Saved configuration to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving config to {config_path}: {str(e)}")
        return False