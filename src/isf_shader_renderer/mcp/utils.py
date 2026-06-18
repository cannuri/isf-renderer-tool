"""MCP-specific utilities."""

import base64
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Re-exported for backward compatibility; the canonical definitions live in
# isf_shader_renderer.errors.
from ..errors import ISFShaderError, RenderingError, ShaderValidationError

__all__ = [
    "validate_shader_content",
    "extract_shader_metadata",
    "sanitize_filename",
    "create_temp_file",
    "encode_image_to_base64",
    "decode_base64_to_image",
    "ISFShaderError",
    "ShaderValidationError",
    "RenderingError",
]


def validate_shader_content(shader_content: str) -> List[str]:
    """Validate shader content and return list of errors."""
    errors = []

    if not shader_content:
        errors.append("Shader content is empty")
        return errors

    if not shader_content.strip():
        errors.append("Shader content contains only whitespace")
        return errors

    # Basic ISF structure validation
    content = shader_content.strip()

    # Check for ISF header
    if not content.startswith("/*{") and not content.startswith("/*"):
        errors.append("Shader does not appear to have ISF header")

    # Check for main function
    if "void main()" not in content and "void main (" not in content:
        errors.append("Shader does not contain main function")

    # Check for gl_FragColor assignment
    if "gl_FragColor" not in content:
        errors.append("Shader does not assign to gl_FragColor")

    return errors


def extract_shader_metadata(shader_content: str) -> Dict[str, Any]:
    """Extract metadata from ISF shader."""
    metadata = {
        "type": "ISF",
        "size": len(shader_content),
        "lines": len(shader_content.splitlines()),
        "has_time_uniform": "TIME" in shader_content.upper(),
        "has_resolution_uniform": "RENDERSIZE" in shader_content.upper(),
        "has_mouse_uniform": "MOUSE" in shader_content.upper(),
        "has_date_uniform": "DATE" in shader_content.upper(),
    }

    # Try to extract ISF JSON header
    try:
        if shader_content.startswith("/*{"):
            # Find the end of the JSON header
            end_idx = shader_content.find("}*/")
            if end_idx != -1:
                json_str = shader_content[2 : end_idx + 1]
                isf_data = json.loads(json_str)
                metadata["isf_header"] = isf_data

                # Extract common fields
                if "DESCRIPTION" in isf_data:
                    metadata["description"] = isf_data["DESCRIPTION"]
                if "CREDIT" in isf_data:
                    metadata["credit"] = isf_data["CREDIT"]
                if "CATEGORIES" in isf_data:
                    metadata["categories"] = isf_data["CATEGORIES"]
                if "INPUTS" in isf_data:
                    metadata["input_count"] = len(isf_data["INPUTS"])
                if "PASSES" in isf_data:
                    metadata["pass_count"] = len(isf_data["PASSES"])
    except (json.JSONDecodeError, KeyError):
        # If JSON parsing fails, continue without ISF header
        pass

    return metadata


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    import re

    # Replace each unsafe character with a single underscore (no collapse)
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    return sanitized


def create_temp_file(suffix: str = ".png", directory: Optional[Path] = None) -> Path:
    """Create a temporary file path and return it, but do not create the file."""
    import tempfile
    import uuid

    if directory is None:
        directory = Path(tempfile.gettempdir()) / "isf_renderer"
    directory.mkdir(parents=True, exist_ok=True)
    # Generate a unique filename
    unique_name = f"tmp{uuid.uuid4().hex}{suffix}"
    temp_path = directory / unique_name
    return temp_path


def encode_image_to_base64(image_path: Path) -> str:
    """Encode image file to base64 string."""
    with open(image_path, "rb") as f:
        image_data = f.read()
        return base64.b64encode(image_data).decode()


def decode_base64_to_image(base64_data: str, output_path: Path) -> None:
    """Decode base64 string to image file."""
    image_data = base64.b64decode(base64_data)
    with open(output_path, "wb") as f:
        f.write(image_data)
