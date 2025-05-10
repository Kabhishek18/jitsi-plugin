# Jitsi-Py Plugin Documentation

## Introduction

Jitsi-Py is a comprehensive Python package that integrates with Jitsi Meet to provide powerful video/audio communication capabilities in your Python applications. It simplifies the process of creating and managing video conferences, controlling rooms, and implementing advanced features like recording, streaming, and collaboration tools.

This documentation will guide you through the installation, configuration, and usage of the Jitsi-Py plugin with practical examples.

## Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [Room Management](#room-management)
4. [Authentication and Security](#authentication-and-security)
5. [Advanced Features](#advanced-features)
6. [Framework Integrations](#framework-integrations)
   - [Django Integration](#django-integration)
   - [FastAPI Integration](#fastapi-integration)
7. [Command-Line Interface](#command-line-interface)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)
10. [Conclusion](#conclusion)

## Installation

### Requirements

- Python 3.8 or higher
- A Jitsi Meet instance (either the public `meet.jit.si` or your self-hosted server)

### Installing the Package

```bash
# Basic installation
pip install jitsi-py

# With optional dependencies
pip install jitsi-py[django]  # Django integration
pip install jitsi-py[fastapi]  # FastAPI integration
pip install jitsi-py[aws]  # AWS S3 for recording storage
pip install jitsi-py[ai]  # AI features (transcription, etc.)

# Install all extras
pip install jitsi-py[all]
```

## Basic Usage

### Creating a Simple Conference

```python
from jitsi_py import JitsiClient

# Initialize client (defaults to public Jitsi Meet server)
client = JitsiClient()

# Create a room
room = client.create_room("my-meeting-room")

# Generate URLs for joining
host_url = room.host_url(user_name="Meeting Host")
guest_url = room.join_url(user_name="Guest User")

print(f"Host URL: {host_url}")
print(f"Guest URL: {guest_url}")
```

### Using a Custom Jitsi Server

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
room = client.create_room("my-meeting-room")
```

## Room Management

### Creating Rooms with Expiry

```python
import time
from jitsi_py import JitsiClient

client = JitsiClient()

# Create a room that expires in 1 hour (3600 seconds)
room = client.create_room(
    room_name="temporary-meeting",
    expiry=3600
)

# Check room expiry
expires_at = room.state.expires_at
print(f"Room expires at: {expires_at}")
print(f"Is expired: {room.state.is_expired}")

# Get room URL
join_url = room.join_url(user_name="Participant")
```

### Configuring Room Features

```python
from jitsi_py import JitsiClient
from jitsi_py.features.audio import AudioConfig
from jitsi_py.features.video import VideoConfig, VideoQuality

client = JitsiClient()

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

# Create room with features
room = client.create_room(
    room_name="feature-rich-room",
    features=features
)

# Generate URL with the configured features
join_url = room.join_url(user_name="Participant")
```

### Creating Breakout Rooms

```python
from jitsi_py import JitsiClient

client = JitsiClient()

# Create main room
main_room = client.create_room("main-conference")

# Create breakout rooms
breakout_room1 = main_room.create_breakout_room("team-a")
breakout_room2 = main_room.create_breakout_room("team-b")

# Generate join URLs for each room
main_url = main_room.join_url(user_name="Moderator", role="host")
breakout1_url = breakout_room1.join_url(user_name="Team A Member")
breakout2_url = breakout_room2.join_url(user_name="Team B Member")
```

## Authentication and Security

### Using JWT Authentication

```python
from jitsi_py import JitsiClient, JitsiServerConfig, JitsiServerType

# Configure Jitsi server with JWT authentication
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

# Create a room
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

### Creating and Verifying Tokens Manually

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

## Advanced Features

### Recording Meetings

```python
from jitsi_py import JitsiClient
from jitsi_py.features.recording import RecordingConfig, RecordingFormat, StorageProvider

client = JitsiClient(
    # Configure your client with appropriate credentials
)

# Configure recording options
recording_config = RecordingConfig(
    enabled=True,
    format=RecordingFormat.MP4,
    storage=StorageProvider.S3,
    storage_config={
        "bucket": "meeting-recordings",
        "region": "us-west-2",
        "access_key": "YOUR_ACCESS_KEY",
        "secret_key": "YOUR_SECRET_KEY"
    },
    auto_start=False,
    include_chat=True,
    host_control_only=True
).to_dict()

# Create room with recording enabled
room = client.create_room(
    room_name="recorded-meeting",
    features={"recording": recording_config}
)

# Generate URL for host (who can control recording)
host_url = room.host_url(user_name="Meeting Host")

# Start recording (using the REST API)
from jitsi_py.api.rest import JitsiRestClient

rest_client = JitsiRestClient(
    api_endpoint="https://api.example.com/jitsi",
    jwt_token=token  # Use a valid JWT token with host privileges
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

```python
from jitsi_py import JitsiClient
from jitsi_py.features.streaming import StreamingConfig, StreamingService, StreamingMode

client = JitsiClient()

# Configure streaming
streaming_config = StreamingConfig(
    enabled=True,
    mode=StreamingMode.BROADCAST,  # One-way streaming
    service=StreamingService.YOUTUBE,
    key="your-youtube-stream-key",
    public=True,
    low_latency=True
).to_dict()

# Create room with streaming enabled
room = client.create_room(
    room_name="live-stream",
    features={"streaming": streaming_config}
)

# Generate URL for host (who can control streaming)
host_url = room.host_url(user_name="Broadcaster")

# Generate URL for viewers
viewer_url = room.join_url(user_name="Viewer", role="viewer")
```

### Real-time Transcription

```python
from jitsi_py import JitsiClient
from jitsi_py.api.rest import JitsiRestClient

client = JitsiClient()
room = client.create_room("transcribed-meeting")

# Configure transcription using the REST API
rest_client = JitsiRestClient(
    api_endpoint="https://api.example.com/jitsi",
    jwt_token=token  # Use a valid JWT token
)

# Start transcription
rest_client.start_transcription(
    room_name="transcribed-meeting",
    options={
        "language": "en-US",
        "model": "whisper-small",
        "translation_enabled": True,
        "translation_languages": ["es", "fr"]
    }
)

# Later, get the transcription
transcription = rest_client.get_transcription("transcribed-meeting")

# Stop transcription
rest_client.stop_transcription("transcribed-meeting")
```

## Framework Integrations

### Django Integration

We provide a ready-to-use Django app that integrates with Jitsi-Py to add video conferencing capabilities to your Django project.

1. First, install Jitsi-Py with Django integration:
   ```bash
   pip install jitsi-py[django]
   ```

2. Download the Django integration package from our [GitHub repository](https://github.com/Kabhishek18/jitsi-plugin/raw/main/docs/jitsi_meetings.zip) and extract it to your Django project.

3. Add it to your INSTALLED_APPS:
   ```python
   INSTALLED_APPS = [
       # ...
       'jitsi_meetings',
       # ...
   ]
   ```

4. See our [detailed Django integration guide](https://github.com/Kabhishek18/jitsi-plugin/blob/main/docs/django-integration.md) for complete setup instructions.

### FastAPI Integration

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

# Sample user data (in a real app, this would be from a database)
users = {
    "johndoe": {
        "name": "John Doe",
        "email": "john@example.com",
        "is_admin": True
    }
}

# Routes
@app.get("/rooms/{room_name}/join")
async def join_room(room_name: str, token: str = Depends(oauth2_scheme)):
    # In a real app, validate the token and get user details
    username = "johndoe"  # Example: extract from token
    
    if username not in users:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    user = users[username]
    role = "host" if user["is_admin"] else "viewer"
    
    room = jitsi_client.get_room(room_name)
    join_url = room.join_url(
        user_name=user["name"],
        user_email=user["email"],
        role=role
    )
    
    return {"join_url": join_url}

@app.post("/rooms")
async def create_room(room_name: str, token: str = Depends(oauth2_scheme)):
    # Validate user permissions (example)
    username = "johndoe"  # Extract from token
    if username not in users or not users[username]["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to create rooms")
    
    room = jitsi_client.create_room(room_name)
    
    return {
        "room_name": room.state.name,
        "host_url": room.host_url(user_name=users[username]["name"]),
        "guest_url": room.join_url(role="viewer")
    }

@app.post("/rooms/{room_name}/recording/start")
async def start_recording(room_name: str, token: str = Depends(oauth2_scheme)):
    # Validate admin permissions
    username = "johndoe"  # Extract from token
    if username not in users or not users[username]["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Create REST client with admin token
    from jitsi_py.api.rest import JitsiRestClient
    rest_client = JitsiRestClient(
        api_endpoint="https://api.example.com/jitsi",
        jwt_token=token
    )
    
    try:
        response = rest_client.start_recording(room_name)
        return {"status": "recording started", "recording_id": response.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Command-Line Interface

Jitsi-Py includes a command-line interface for common operations:

```bash
# Initialize configuration
jitsi-py init --server-type=self_hosted --domain=meet.example.com --jwt-secret=your_secret

# Create a room
jitsi-py room create my-meeting

# Generate a URL
jitsi-py url generate my-meeting --user-name="John Doe" --role=host

# List rooms (if supported by server)
jitsi-py room list

# Start recording
jitsi-py recording start my-meeting --format=mp4

# Stop recording
jitsi-py recording stop my-meeting
```

## API Reference

### Core Classes

#### JitsiClient

The main entry point for interacting with Jitsi Meet.

```python
JitsiClient(
    server_config=None,  # JitsiServerConfig object
    app_id=None,         # Application ID for JWT auth
    api_key=None,        # API key for REST API
    jwt_secret=None      # Secret for JWT token generation
)
```

Methods:
- `create_room(room_name, features=None, expiry=None)`: Create a new room
- `get_room(room_name)`: Get an existing room
- `generate_room_url(room_name, user_name=None, user_email=None, user_avatar=None, role=None, token=None, features=None)`: Generate a URL for joining a room

#### Room

Represents a Jitsi room.

Methods:
- `join_url(user_name=None, user_email=None, user_avatar=None, role="viewer", features=None)`: Generate a URL for joining the room
- `host_url(user_name=None, user_email=None, user_avatar=None, features=None)`: Generate a URL for joining as a host
- `create_breakout_room(room_name)`: Create a breakout room

#### JitsiRestClient

Client for interacting with the Jitsi REST API.

```python
JitsiRestClient(
    api_endpoint,    # API endpoint URL
    api_key=None,    # API key
    jwt_token=None   # JWT token
)
```

Methods:
- `create_room(room_name, options=None)`: Create a room
- `get_room(room_name)`: Get room details
- `update_room(room_name, options)`: Update room settings
- `delete_room(room_name)`: Delete a room
- `get_participants(room_name)`: Get room participants
- `kick_participant(room_name, participant_id)`: Remove a participant
- `mute_participant(room_name, participant_id, mute_audio=True, mute_video=False)`: Mute a participant
- `start_recording(room_name, options=None)`: Start recording
- `stop_recording(room_name)`: Stop recording
- `get_recordings(room_name)`: Get room recordings
- ...and many more

## Troubleshooting

### Common Issues

#### Connection Problems

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

#### JWT Authentication Errors

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

#### Debugging REST API Calls

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

## Conclusion

The Jitsi-Py plugin provides a robust and flexible way to integrate Jitsi Meet video conferencing into your Python applications. From simple room creation to advanced features like recording, streaming, and framework integrations, this plugin offers comprehensive tools to enhance your communication solutions.

For more information, check out the official repository, contribute to the project, or contact the maintainers with any questions or suggestions.