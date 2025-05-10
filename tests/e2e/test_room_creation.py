# tests/e2e/test_room_creation.py

import pytest
import os
import time
import requests
from urllib.parse import urlparse, parse_qs

from jitsi_py.core.client import JitsiClient, JitsiServerConfig, JitsiServerType

# Skip these tests if E2E_TESTS environment variable is not set
pytestmark = pytest.mark.skipif(
    os.environ.get("E2E_TESTS") != "1",
    reason="E2E tests are only run when E2E_TESTS=1"
)

class TestE2ERoomCreation:
    
    def setup_method(self):
        """Setup test environment."""
        # Get configuration from environment variables
        server_type = os.environ.get("JITSI_SERVER_TYPE", "public")
        domain = os.environ.get("JITSI_DOMAIN", "meet.jit.si")
        jwt_secret = os.environ.get("JITSI_JWT_SECRET")
        
        self.server_config = JitsiServerConfig(
            server_type=JitsiServerType(server_type),
            domain=domain
        )
        
        self.client = JitsiClient(
            server_config=self.server_config,
            jwt_secret=jwt_secret
        )
    
    def test_create_and_join_room(self):
        """Test creating a room and generating join URLs."""
        # Create a unique room name
        room_name = f"test-room-{int(time.time())}"
        
        # Create room
        room = self.client.create_room(room_name)
        
        assert room is not None
        assert room.state.name == room_name
        
        # Generate URLs
        host_url = room.host_url(user_name="Test Host")
        viewer_url = room.join_url(user_name="Test Viewer")
        
        # Verify URLs
        assert host_url.startswith(f"https://{self.server_config.domain}/{room_name}")
        assert viewer_url.startswith(f"https://{self.server_config.domain}/{room_name}")
        
        # If JWT authentication is enabled, verify token presence
        if self.client.jwt_secret:
            parsed_host_url = urlparse(host_url)
            host_params = parse_qs(parsed_host_url.fragment)
            
            parsed_viewer_url = urlparse(viewer_url)
            viewer_params = parse_qs(parsed_viewer_url.fragment)
            
            assert "jwt" in host_params
            assert "jwt" in viewer_params
            
            # Host and viewer should have different tokens
            assert host_params["jwt"] != viewer_params["jwt"]
        
        # Attempt to access the room URLs (just to verify they're valid)
        # This doesn't test the actual video conference, just that the URLs are accessible
        try:
            host_response = requests.head(host_url.split("#")[0])
            assert host_response.status_code in [200, 301, 302]
            
            viewer_response = requests.head(viewer_url.split("#")[0])
            assert viewer_response.status_code in [200, 301, 302]
        except requests.RequestException as e:
            pytest.skip(f"Could not connect to Jitsi server: {str(e)}")