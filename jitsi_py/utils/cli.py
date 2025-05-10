# jitsi_py/utils/cli.py

import argparse
import json
import os
import sys
import yaml
from typing import Dict, Optional, List, Any

from ..core.client import JitsiClient, JitsiServerConfig, JitsiServerType

def create_config_parser():
    """Create a parser for configuration commands."""
    parser = argparse.ArgumentParser(description="Jitsi Python Client CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize configuration")
    init_parser.add_argument(
        "--server-type",
        choices=["public", "self_hosted", "docker"],
        default="public",
        help="Server type"
    )
    init_parser.add_argument("--domain", help="Jitsi domain")
    init_parser.add_argument("--app-id", help="Application ID")
    init_parser.add_argument("--api-key", help="API key")
    init_parser.add_argument("--jwt-secret", help="JWT secret")
    
    # Room commands
    room_parser = subparsers.add_parser("room", help="Room management")
    room_subparsers = room_parser.add_subparsers(dest="room_command", help="Room command")
    
    # Create room
    create_room_parser = room_subparsers.add_parser("create", help="Create a room")
    create_room_parser.add_argument("name", help="Room name")
    create_room_parser.add_argument("--expiry", type=int, help="Expiry time in seconds")
    create_room_parser.add_argument(
        "--features",
        help="Features JSON string or file path"
    )
    
    # Get room
    get_room_parser = room_subparsers.add_parser("get", help="Get a room")
    get_room_parser.add_argument("name", help="Room name")
    
    # List rooms
    list_rooms_parser = room_subparsers.add_parser("list", help="List rooms")
    
    # Recording commands
    recording_parser = subparsers.add_parser("recording", help="Recording management")
    recording_subparsers = recording_parser.add_subparsers(
        dest="recording_command",
        help="Recording command"
    )
    
    # Start recording
    start_recording_parser = recording_subparsers.add_parser("start", help="Start recording")
    start_recording_parser.add_argument("room", help="Room name")
    start_recording_parser.add_argument(
        "--format",
        choices=["mp4", "webm", "ogg"],
        default="mp4",
        help="Recording format"
    )
    start_recording_parser.add_argument(
        "--storage",
        choices=["local", "s3", "dropbox"],
        default="local",
        help="Storage provider"
    )
    
    # Stop recording
    stop_recording_parser = recording_subparsers.add_parser("stop", help="Stop recording")
    stop_recording_parser.add_argument("room", help="Room name")
    
    # List recordings
    list_recordings_parser = recording_subparsers.add_parser("list", help="List recordings")
    list_recordings_parser.add_argument("room", help="Room name")
    
    # URL commands
    url_parser = subparsers.add_parser("url", help="URL generation")
    url_subparsers = url_parser.add_subparsers(
        dest="url_command",
        help="URL command"
    )
    
    # Generate URL
    generate_url_parser = url_subparsers.add_parser("generate", help="Generate a room URL")
    generate_url_parser.add_argument("room", help="Room name")
    generate_url_parser.add_argument("--user-name", help="User name")
    generate_url_parser.add_argument("--user-email", help="User email")
    generate_url_parser.add_argument("--role", help="User role")
    
    return parser

def load_config():
    """Load configuration."""
    config_paths = [
        os.path.join(os.getcwd(), ".jitsi.yaml"),
        os.path.join(os.getcwd(), ".jitsi.yml"),
        os.path.join(os.getcwd(), ".jitsi.json"),
        os.path.expanduser("~/.jitsi.yaml"),
        os.path.expanduser("~/.jitsi.yml"),
        os.path.expanduser("~/.jitsi.json"),
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                if path.endswith(".json"):
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
    
    return {}

def save_config(config):
    """Save configuration."""
    config_path = os.path.join(os.getcwd(), ".jitsi.yaml")
    
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

def get_client_from_config(config):
    """Get a JitsiClient instance from configuration."""
    server_type = config.get("server_type", "public")
    server_config = JitsiServerConfig(
        server_type=JitsiServerType(server_type),
        domain=config.get("domain", "meet.jit.si"),
        secure=config.get("secure", True),
        api_endpoint=config.get("api_endpoint")
    )
    
    return JitsiClient(
        server_config=server_config,
        app_id=config.get("app_id"),
        api_key=config.get("api_key"),
        jwt_secret=config.get("jwt_secret")
    )

def main():
    """Main CLI entry point."""
    parser = create_config_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    config = load_config()
    
    if args.command == "init":
        config["server_type"] = args.server_type
        
        if args.domain:
            config["domain"] = args.domain
        
        if args.app_id:
            config["app_id"] = args.app_id
        
        if args.api_key:
            config["api_key"] = args.api_key
        
        if args.jwt_secret:
            config["jwt_secret"] = args.jwt_secret
        
        save_config(config)
        print("Configuration saved successfully")
        return
    
    client = get_client_from_config(config)
    
    if args.command == "room":
        if args.room_command == "create":
            features = {}
            
            if args.features:
                if os.path.exists(args.features):
                    with open(args.features, "r") as f:
                        if args.features.endswith(".json"):
                            features = json.load(f)
                        else:
                            features = yaml.safe_load(f)
                else:
                    features = json.loads(args.features)
            
            room = client.create_room(
                room_name=args.name,
                features=features,
                expiry=args.expiry
            )
            
            print(f"Room created: {args.name}")
            print(f"Host URL: {room.host_url()}")
            print(f"Guest URL: {room.join_url()}")
        
        elif args.room_command == "get":
            room = client.get_room(args.name)
            print(f"Room: {args.name}")
            print(f"Host URL: {room.host_url()}")
            print(f"Guest URL: {room.join_url()}")
    
    elif args.command == "url":
        if args.url_command == "generate":
            room = client.get_room(args.room)
            url = room.join_url(
                user_name=args.user_name,
                user_email=args.user_email,
                role=args.role
            )
            
            print(url)

if __name__ == "__main__":
    main()