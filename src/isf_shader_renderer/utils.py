"""Utility functions for ISF Shader Renderer."""

import re
from pathlib import Path
from typing import List


def parse_time_range(time_range: str) -> List[float]:
    """
    Parse a time range string into a list of time codes.

    Supports formats like:
    - "0,1,2,3" -> [0.0, 1.0, 2.0, 3.0]
    - "0:3:0.5" -> [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    - "0-3:0.5" -> [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    Args:
        time_range: String representation of time range

    Returns:
        List of time codes
    """
    # Handle comma-separated values
    if "," in time_range:
        return [float(t.strip()) for t in time_range.split(",")]

    # Handle range with step
    range_pattern = r"^(\d+(?:\.\d+)?)\s*[-:]\s*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)$"
    match = re.match(range_pattern, time_range)
    if match:
        start = float(match.group(1))
        end = float(match.group(2))
        step = float(match.group(3))

        times = []
        current = start
        while current <= end:
            times.append(current)
            current += step
        return times

    # Single value
    try:
        return [float(time_range)]
    except ValueError:
        raise ValueError(f"Invalid time range format: {time_range}")


def format_output_path(template: str, frame_number: int, time_code: float) -> str:
    """
    Format output path template with frame number and time code.

    Args:
        template: Path template with format specifiers
        frame_number: Frame number (0-based)
        time_code: Time code for the frame

    Returns:
        Formatted path string
    """
    # Replace common format specifiers
    formatted = template.replace("%d", str(frame_number))
    formatted = formatted.replace("%04d", f"{frame_number:04d}")
    formatted = formatted.replace("%f", f"{time_code:.3f}")
    formatted = formatted.replace("%.3f", f"{time_code:.3f}")

    return formatted


def validate_output_path(path: Path) -> bool:
    """
    Validate that an output path is writable.

    Args:
        path: Path to validate

    Returns:
        True if path is valid and writable
    """
    try:
        # Check if parent directory exists or can be created
        parent = path.parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)

        # Check if we can write to the directory
        if not parent.is_dir():
            return False

        # Try to create a test file
        test_file = parent / f".test_{path.name}"
        test_file.touch()
        test_file.unlink()

        return True
    except (OSError, PermissionError):
        return False


def extract_shader_metadata(shader_content: str) -> dict:
    """
    Extract metadata from ISF shader content.

    Args:
        shader_content: The ISF shader source code

    Returns:
        Dictionary containing extracted metadata
    """
    metadata: dict = {
        "name": None,
        "description": None,
        "author": None,
        "version": None,
        "uniforms": [],
        "inputs": [],
        "outputs": [],
    }

    # Look for ISF metadata comments
    lines = shader_content.splitlines()

    for line in lines:
        line = line.strip()

        # Extract name
        if line.startswith("/*") and "name:" in line.lower():
            match = re.search(r"name:\s*([^*/]+)", line, re.IGNORECASE)
            if match:
                metadata["name"] = match.group(1).strip()

        # Extract description
        elif line.startswith("/*") and "description:" in line.lower():
            match = re.search(r"description:\s*([^*/]+)", line, re.IGNORECASE)
            if match:
                metadata["description"] = match.group(1).strip()

        # Extract author
        elif line.startswith("/*") and "author:" in line.lower():
            match = re.search(r"author:\s*([^*/]+)", line, re.IGNORECASE)
            if match:
                metadata["author"] = match.group(1).strip()

        # Extract version
        elif line.startswith("/*") and "version:" in line.lower():
            match = re.search(r"version:\s*([^*/]+)", line, re.IGNORECASE)
            if match:
                metadata["version"] = match.group(1).strip()

    return metadata


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe file system usage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Remove leading/trailing spaces and dots
    filename = filename.strip(" .")

    # Ensure it's not empty
    if not filename:
        filename = "unnamed"

    return filename


def get_file_extension(format_name: str) -> str:
    """
    Get file extension for a given format name.

    Args:
        format_name: Format name (e.g., 'png', 'jpg', 'jpeg')

    Returns:
        File extension with leading dot
    """
    format_map = {
        "png": ".png",
        "jpg": ".jpg",
        "jpeg": ".jpg",
        "bmp": ".bmp",
        "tiff": ".tiff",
        "tga": ".tga",
    }
    return format_map.get(format_name.lower(), ".png")


def calculate_frame_count(start_time: float, end_time: float, fps: float) -> int:
    """
    Calculate the number of frames for a time range.

    Args:
        start_time: Start time in seconds
        end_time: End time in seconds
        fps: Frames per second

    Returns:
        Number of frames
    """
    duration = end_time - start_time
    return int(duration * fps) + 1


def generate_time_codes(start_time: float, end_time: float, fps: float) -> List[float]:
    """
    Generate a list of time codes for a time range.

    Args:
        start_time: Start time in seconds
        end_time: End time in seconds
        fps: Frames per second

    Returns:
        List of time codes
    """
    frame_count = calculate_frame_count(start_time, end_time, fps)
    return [start_time + (i / fps) for i in range(frame_count)]


def format_error_for_ai(error: Exception, context: str = "") -> str:
    """
    Format an error message for AI-friendly output.

    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred

    Returns:
        Natural language error description
    """
    error_message = str(error)

    # Common error patterns and their AI-friendly descriptions
    if "main" in error_message.lower() and "function" in error_message.lower():
        return "The shader is missing a main function. ISF shaders require a 'void main()' function to define the fragment shader entry point."

    if "syntax" in error_message.lower():
        return f"The shader contains syntax errors: {error_message}. Please check the GLSL syntax and ensure all brackets, semicolons, and function calls are properly formatted."

    if "uniform" in error_message.lower() and "not found" in error_message.lower():
        return f"The shader references a uniform variable that is not defined: {error_message}. Make sure all uniform variables are properly declared."

    if "texture" in error_message.lower() and "not found" in error_message.lower():
        return f"The shader references a texture that is not available: {error_message}. Ensure all texture inputs are properly defined in the ISF metadata."

    if "compilation" in error_message.lower():
        return f"The shader failed to compile: {error_message}. This usually indicates syntax errors, undefined variables, or unsupported GLSL features."

    if "validation" in error_message.lower():
        return f"Shader validation failed: {error_message}. The shader may be missing required components or have invalid ISF metadata."

    if "file" in error_message.lower() and "not found" in error_message.lower():
        return f"File not found: {error_message}. Please check that the file path is correct and the file exists."

    if "permission" in error_message.lower():
        return f"Permission denied: {error_message}. The program cannot access the specified file or directory."

    if "import" in error_message.lower() and "vvisf" in error_message.lower():
        return f"VVISF library not available: {error_message}. The pyvvisf library is required for ISF shader rendering but is not installed or accessible."

    if "opengl" in error_message.lower() or "glfw" in error_message.lower():
        return f"OpenGL/GLFW error: {error_message}. This may indicate graphics driver issues or missing OpenGL support."

    if "memory" in error_message.lower():
        return f"Memory allocation error: {error_message}. The requested render size may be too large for available system memory."

    # Generic error formatting
    if context:
        return f"Error occurred during {context}: {error_message}"
    else:
        return f"An error occurred: {error_message}"


def format_success_for_ai(frames_rendered: int, output_path: str = "") -> str:
    """
    Format a success message for AI processing.

    Args:
        frames_rendered: Number of frames successfully rendered
        output_path: Path where output was saved

    Returns:
        Natural language success description
    """
    if frames_rendered == 1:
        if output_path:
            return f"Successfully rendered 1 frame to {output_path}"
        else:
            return "Successfully rendered 1 frame"
    else:
        if output_path:
            return f"Successfully rendered {frames_rendered} frames to {output_path}"
        else:
            return f"Successfully rendered {frames_rendered} frames"
