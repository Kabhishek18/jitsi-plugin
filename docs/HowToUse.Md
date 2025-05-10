# How to Use Jitsi-Py

This guide provides step-by-step instructions for installing, configuring, and using the Jitsi-Py package in your Python applications.

## Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [Configuration](#configuration)
4. [Room Management](#room-management)
5. [Authentication and Security](#authentication-and-security)
6. [Framework Integrations](#framework-integrations)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)

## Installation

### Requirements

Before installing Jitsi-Py, ensure you have:

- Python 3.8 or higher
- Access to a Jitsi Meet instance (either public `meet.jit.si` or your own self-hosted server)

### Install the Package

Install the package using pip:

```bash
# Basic installation
pip install jitsi-py

# With framework integrations
pip install jitsi-py[django]  # Django integration
pip install jitsi-py[fastapi]  # FastAPI integration

# With storage options
pip install jitsi-py[aws]  # AWS S3 for recording storage

# With AI features
pip install jitsi-py[ai]  # AI features (transcription, etc.)

# Install all extras
pip install jitsi-py[all]
```

## Basic Usage

### Creating Your First Meeting

Here's a simple example to create a Jitsi meeting and get the joining links:

```python
from jitsi_py import JitsiClient

# Initialize client (defaults to public Jitsi Meet server)
client = JitsiClient()

# Create a room
room = client.create_room("my-first-meeting")

# Generate URLs for joining
host_url = room.host_url(user_name="Meeting Host")
guest_url = room.join_url(user_name="Guest User")

print(f"Host URL: {host_url}")
print(f"Guest URL: {guest_url}")
```

### Using a Custom Jitsi Server

If you have your own Jitsi server, configure it like this:

```python
from jitsi_py import JitsiClient, JitsiServerConfig, JitsiServerType

# Configure your own Jitsi server
server_config = JitsiServerConfig(
    server_type=JitsiServerType.SELF_HOSTED,
    domain="meet.example.com",
    secure=True  # Use HTTPS
)

# Create a client with custom server
client = JitsiClient(server_config=server_config)

# Now create rooms as usual
room = client.create_room("my-meeting")
```

## Configuration

### Configuration Options

Jitsi-Py can be configured with various options:

```python
from jitsi_py import JitsiClient, JitsiServerConfig, JitsiServerType

# Basic server configuration options
server_config = JitsiServerConfig(
    server_type=JitsiServerType.SELF_HOSTED,  # Options: PUBLIC, SELF_HOSTED, DOCKER
    domain="meet.example.com",  # Your Jitsi domain
    secure=True,  # Use HTTPS (default: True)
    api_endpoint="https://api.example.com/jitsi"  # Optional: REST API endpoint
)

# Client configuration options
client = JitsiClient(
    server_config=server_config,  # Server configuration
    app_id="my_app_id",  # For JWT authentication
    api_key="my_api_key",  # For REST API access
    jwt_secret="my_jwt_secret"  # For JWT token generation
)
```

### Saving and Loading Configuration

You can save and load configuration:

```python
from jitsi_py.utils.config import JitsiConfig

# Create configuration
config = JitsiConfig(
    server_config=server_config,
    app_id="my_app_id",
    jwt_secret="my_jwt_secret"
)

# Save to file
config.save_to_file("jitsi_config.json")

# Load from file
loaded_config = JitsiConfig.load_from_file("jitsi_config.json")
```

## Room Management

### Creating Rooms with Options

Create rooms with specific features and expiry:

```python
from jitsi_py import JitsiClient
from jitsi_py.features.audio import AudioConfig
from jitsi_py.features.video import VideoConfig, VideoQuality

# Configure features
features = {
    "audio": AudioConfig(
        enabled=True,
        muted=False,
        auto_mute_on_join=True,
        noise_suppression=True
    ).to_dict(),
    
    "video": VideoConfig(
        enabled=True,
        muted=False,
        quality=VideoQuality.HIGH,
        background_blur=True
    ).to_dict(),
    
    # UI customization
    "ui": {
        "hide_buttons": ["settings", "invite", "feedback"]
    }
}

# Create room with features and expiry (in seconds)
client = JitsiClient()
room = client.create_room(
    room_name="feature-rich-room",
    features=features,
    expiry=3600  # 1 hour
)

# Check room expiry
print(f"Room expires at: {room.state.expires_at}")
print(f"Is expired: {room.state.is_expired}")
```

### Creating Breakout Rooms

Create breakout rooms from a main room:

```python
from jitsi_py import JitsiClient

client = JitsiClient()

# Create main room
main_room = client.create_room("main-meeting")

# Create breakout rooms
team_a_room = main_room.create_breakout_room("team-a")
team_b_room = main_room.create_breakout_room("team-b")

# Generate join URLs
main_url = main_room.host_url(user_name="Moderator")
team_a_url = team_a_room.join_url(user_name="Team A Member")
team_b_url = team_b_room.join_url(user_name="Team B Member")
```

## Authentication and Security

### Using JWT Authentication

JWT authentication provides secure access to your Jitsi rooms:

```python
from jitsi_py import JitsiClient, JitsiServerConfig, JitsiServerType

# Configure client with JWT authentication
server_config = JitsiServerConfig(
    server_type=JitsiServerType.SELF_HOSTED,
    domain="meet.example.com",
    secure=True
)

client = JitsiClient(
    server_config=server_config,
    app_id="my_app_id",
    jwt_secret="my_jwt_secret"
)

# Create a secure room
room = client.create_room("secure-meeting")

# Generate authenticated URLs with different roles
admin_url = room.join_url(
    user_name="Admin User",
    user_email="admin@example.com",
    role="host"
)

viewer_url = room.join_url(
    user_name="Viewer User",
    user_email="viewer@example.com",
    role="viewer"
)
```

### Managing Tokens Manually

For advanced token management:

```python
from jitsi_py.security.tokens import generate_jwt_token, verify_jwt_token

# Generate a token
jwt_secret = "my_jwt_secret"
token = generate_jwt_token(
    jwt_secret=jwt_secret,
    app_id="my_app_id",
    room_name="secure-room",
    user_id="user123",
    user_name="John Doe",
    user_email="john@example.com",
    role="host",
    expiry=3600  # 1 hour
)

# Verify a token
token_obj = verify_jwt_token(token, jwt_secret)

if token_obj.is_valid:
    print(f"Token is valid for room: {token_obj.room}")
    print(f"User ID: {token_obj.user_id}")
    print(f"Role: {token_obj.role}")
else:
    print("Token is invalid or expired")
```

## Framework Integrations

### Django Integration

See [Django Integration](django-integration.md) for detailed instructions.

### FastAPI Integration

Basic FastAPI integration:

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jitsi_py import JitsiClient, JitsiServerConfig, JitsiServerType

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize Jitsi client
jitsi_client = JitsiClient(
    server_config=JitsiServerConfig(
        server_type=JitsiServerType.SELF_HOSTED,
        domain="meet.example.com"
    ),
    jwt_secret="your_jwt_secret"
)

@app.get("/rooms/{room_name}/join")
async def join_room(room_name: str, token: str = Depends(oauth2_scheme)):
    # Validate user (in a real app, extract user details from token)
    user_name = "Example User"
    user_email = "user@example.com"
    
    room = jitsi_client.get_room(room_name)
    join_url = room.join_url(
        user_name=user_name,
        user_email=user_email,
        role="viewer"
    )
    
    return {"join_url": join_url}

@app.post("/rooms")
async def create_room(room_name: str, token: str = Depends(oauth2_scheme)):
    room = jitsi_client.create_room(room_name)
    
    return {
        "room_name": room.state.name,
        "host_url": room.host_url(user_name="Host"),
        "guest_url": room.join_url(role="viewer")
    }
```

## Advanced Features

### Recording Meetings

Configure and manage recordings:

```python
from jitsi_py import JitsiClient
from jitsi_py.features.recording import RecordingConfig, RecordingFormat, StorageProvider
from jitsi_py.api.rest import JitsiRestClient

# Configure recording
recording_config = RecordingConfig(
    enabled=True,
    format=RecordingFormat.MP4,
    storage=StorageProvider.S3,
    storage_config={
        "bucket": "meeting-recordings",
        "region": "us-west-2"
    },
    auto_start=False,
    include_chat=True,
    host_control_only=True
).to_dict()

# Create room with recording enabled
client = JitsiClient()
room = client.create_room(
    room_name="recorded-meeting",
    features={"recording": recording_config}
)

# Create REST client for controlling recording
rest_client = JitsiRestClient(
    api_endpoint="https://api.example.com/jitsi",
    jwt_token=token  # Use a valid JWT token
)

# Start recording
response = rest_client.start_recording(
    room_name="recorded-meeting",
    options={"format": "mp4"}
)

# Later, stop recording
rest_client.stop_recording("recorded-meeting")

# Get recordings
recordings = rest_client.get_recordings("recorded-meeting")
```

### Streaming to External Platforms

Configure streaming to platforms like YouTube:

```python
from jitsi_py import JitsiClient
from jitsi_py.features.streaming import StreamingConfig, StreamingService, StreamingMode

# Configure streaming
streaming_config = StreamingConfig(
    enabled=True,
    mode=StreamingMode.BROADCAST,
    service=StreamingService.YOUTUBE,
    key="your-youtube-stream-key",
    public=True
).to_dict()

# Create room with streaming enabled
client = JitsiClient()
room = client.create_room(
    room_name="livestream",
    features={"streaming": streaming_config}
)
```

## Troubleshooting

### Connection Issues

If you're having trouble connecting to your Jitsi server:

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check server configuration
from jitsi_py import JitsiClient, JitsiServerConfig, JitsiServerType

server_config = JitsiServerConfig(
    server_type=JitsiServerType.SELF_HOSTED,
    domain="meet.example.com",
    secure=True
)

print(f"Base URL: {server_config.base_url}")
```

### JWT Authentication Issues

If you're experiencing JWT authentication issues:

```python
from jitsi_py.security.tokens import generate_jwt_token, verify_jwt_token
import time
import json

# Generate a test token
jwt_secret = "your_jwt_secret"
token = generate_jwt_token(
    jwt_secret=jwt_secret,
    app_id="your_app_id",
    room_name="test-room",
    expiry=600  # Short expiry for testing
)

# Verify the token
token_obj = verify_jwt_token(token, jwt_secret)
print(f"Token valid: {token_obj.is_valid}")

# Check token contents
import jwt
decoded = jwt.decode(
    token, 
    jwt_secret, 
    algorithms=["HS256"], 
    options={"verify_aud": False}
)
print(json.dumps(decoded, indent=2))
```

### REST API Issues

To debug REST API issues:

```python
import logging
import http.client as http_client

# Enable HTTP request/response logging
http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

# Make your API call
from jitsi_py.api.rest import JitsiRestClient
client = JitsiRestClient(api_endpoint="https://api.example.com/jitsi")
response = client.get_room("test-room")
```

For more detailed information, refer to the API documentation and specific integration guides in this documentation folder.