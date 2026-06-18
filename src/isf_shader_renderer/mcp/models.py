"""Pydantic models for MCP requests and responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RenderRequest(BaseModel):
    """Request model for rendering ISF shaders."""

    shader_content: str = Field(..., description="ISF shader source code")
    time_codes: List[float] = Field(
        ..., description="Time codes for rendering (seconds)"
    )
    width: int = Field(1920, description="Output width in pixels")
    height: int = Field(1080, description="Output height in pixels")
    quality: int = Field(95, ge=1, le=100, description="PNG quality (1-100)")
    verbose: bool = Field(False, description="Enable verbose output")


class RenderResponse(BaseModel):
    """Response model for rendering ISF shaders."""

    success: bool = Field(..., description="Whether the rendering was successful")
    message: str = Field(..., description="Human-readable message")
    rendered_frames: List[str] = Field(
        default_factory=list, description="Base64 encoded PNG images"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Rendering metadata"
    )
    logs: List[str] = Field(
        default_factory=list, description="All stdout/stderr output"
    )
    shader_info: Optional[Dict[str, Any]] = Field(
        None, description="Extracted shader information"
    )


class ValidateRequest(BaseModel):
    """Request model for validating ISF shaders."""

    shader_content: str = Field(..., description="ISF shader source code to validate")


class ValidateResponse(BaseModel):
    """Response model for validating ISF shaders."""

    success: bool = Field(..., description="Whether the shader is valid")
    message: str = Field(..., description="Human-readable message")
    shader_info: Optional[Dict[str, Any]] = Field(
        None, description="Extracted shader information"
    )
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class GetShaderInfoRequest(BaseModel):
    """Request model for getting shader information."""

    shader_content: str = Field(..., description="ISF shader source code")


class GetShaderInfoResponse(BaseModel):
    """Response model for getting shader information."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message")
    shader_info: Optional[Dict[str, Any]] = Field(
        None, description="Extracted shader information"
    )
    errors: List[str] = Field(
        default_factory=list, description="Any errors encountered"
    )


class Resource(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    # Add other fields as needed (e.g., mime_type, size, etc.)
