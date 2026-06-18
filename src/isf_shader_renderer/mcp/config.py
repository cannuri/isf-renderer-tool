"""MCP server configuration."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class MCPServerConfig:
    """MCP server configuration."""

    # Server settings
    host: str = "localhost"
    port: int = 8000
    enable_http: bool = False

    # Rendering settings
    max_image_size: int = 4096  # Max width/height
    max_frames_per_request: int = 10
    temp_dir: Path = Path("/tmp/isf_renderer")

    # Security
    allowed_origins: List[str] = field(default_factory=list)
    api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    enable_debug: bool = False

    def __post_init__(self):
        """Validate settings.

        Note: the temp directory is created lazily at render time, not here, so
        merely constructing a config has no filesystem side effects.
        """
        if self.max_image_size < 1:
            raise ValueError("max_image_size must be at least 1")

        if self.max_frames_per_request < 1:
            raise ValueError("max_frames_per_request must be at least 1")

        if self.port < 1 or self.port > 65535:
            raise ValueError("port must be between 1 and 65535")
