# jitsi_py/utils/config.py

from typing import Dict, Optional, Any
from ..core.client import JitsiServerConfig


class JitsiConfig:
    """Configuration manager for Jitsi settings."""
    
    def __init__(
        self,
        server_config: Optional[JitsiServerConfig] = None,
        app_id: Optional[str] = None,
        api_key: Optional[str] = None,
        jwt_secret: Optional[str] = None,
        additional_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the configuration.
        
        Args:
            server_config: Configuration for the Jitsi server.
            app_id: Application ID for authentication.
            api_key: API key for authenticated requests.
            jwt_secret: Secret for JWT token generation.
            additional_config: Additional configuration options.
        """
        self.server_config = server_config
        self.app_id = app_id
        self.api_key = api_key
        self.jwt_secret = jwt_secret
        self.additional_config = additional_config or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary.
        
        Returns:
            Dictionary representation of the configuration.
        """
        config = {
            "app_id": self.app_id,
            "api_key": self.api_key,
            "jwt_secret": self.jwt_secret,
            **self.additional_config
        }
        
        if self.server_config:
            config["server"] = {
                "type": self.server_config.server_type.value,
                "domain": self.server_config.domain,
                "secure": self.server_config.secure,
                "api_endpoint": self.server_config.api_endpoint
            }
        
        return config
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'JitsiConfig':
        """Create a configuration from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values.
            
        Returns:
            JitsiConfig instance.
        """
        from ..core.client import JitsiServerConfig, JitsiServerType
        
        server_config = None
        if "server" in config_dict:
            server = config_dict["server"]
            server_config = JitsiServerConfig(
                server_type=JitsiServerType(server.get("type", "public")),
                domain=server.get("domain", "meet.jit.si"),
                secure=server.get("secure", True),
                api_endpoint=server.get("api_endpoint")
            )
        
        additional_config = {
            k: v for k, v in config_dict.items() 
            if k not in ["app_id", "api_key", "jwt_secret", "server"]
        }
        
        return cls(
            server_config=server_config,
            app_id=config_dict.get("app_id"),
            api_key=config_dict.get("api_key"),
            jwt_secret=config_dict.get("jwt_secret"),
            additional_config=additional_config
        )
    
    def save_to_file(self, file_path: str) -> None:
        """Save the configuration to a file.
        
        Args:
            file_path: Path to the file.
        """
        import json
        
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'JitsiConfig':
        """Load configuration from a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            JitsiConfig instance.
        """
        import json
        
        with open(file_path, "r") as f:
            config_dict = json.load(f)
        
        return cls.from_dict(config_dict)