"""MCP handlers for ISF shader operations."""

import contextlib
import shutil
import tempfile
import traceback
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import ShaderConfig, ShaderRendererConfig
from ..errors import ISFShaderError, ShaderValidationError
from ..renderer import ShaderRenderer
from .models import (
    GetShaderInfoRequest,
    GetShaderInfoResponse,
    RenderRequest,
    Resource,
    ValidateRequest,
    ValidateResponse,
)
from .utils import encode_image_to_base64


class ISFShaderHandlers:
    """Handlers for MCP requests."""

    def __init__(self) -> None:
        """Initialize handlers with default configuration."""
        self.config = ShaderRendererConfig()
        self.renderer = ShaderRenderer(self.config)

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls."""
        if name == "render_shader":
            return await self._render_shader(arguments)
        elif name == "validate_shader":
            return await self._validate_shader(arguments)
        elif name == "get_shader_info":
            return await self._get_shader_info(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _render_shader(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Render an ISF shader at the requested time codes.

        Frames are rendered into a private temporary directory, base64-encoded
        into the response, and the directory is removed before returning, so the
        server never leaks files to disk.
        """
        try:
            request = RenderRequest(**arguments)
        except Exception as e:  # pydantic validation error
            return self._error_result(
                f"Invalid render request: {e}",
                {"type": type(e).__name__, "message": str(e)},
            )

        if not request.shader_content.strip():
            return self._error_result(
                "Invalid shader content: the shader is empty or contains only whitespace.",
                ShaderValidationError(
                    "Shader content is empty or contains only whitespace."
                ).to_dict(),
            )

        shader_config = ShaderConfig(
            input="<mcp>",
            output="",
            times=list(request.time_codes),
            width=request.width,
            height=request.height,
            quality=request.quality,
        )

        output_dir = Path(tempfile.mkdtemp(prefix="isf_render_"))
        # Capture stray stdout/stderr per call (protects the stdio MCP protocol
        # stream and surfaces backend chatter in the response logs).
        captured = StringIO()
        try:
            rendered_frames: List[str] = []
            rendered_files: List[Dict[str, Any]] = []
            with (
                contextlib.redirect_stdout(captured),
                contextlib.redirect_stderr(captured),
            ):
                for i, time_code in enumerate(request.time_codes):
                    filename = f"frame_{i:03d}_t{time_code:.2f}.png"
                    output_path = output_dir / filename
                    self.renderer.render_frame(
                        request.shader_content, time_code, output_path, shader_config
                    )
                    rendered_frames.append(encode_image_to_base64(output_path))
                    rendered_files.append(
                        {
                            "filename": filename,
                            "size": output_path.stat().st_size,
                            "time_code": time_code,
                        }
                    )
                shader_info = self.renderer.get_shader_info(request.shader_content)

            time_codes = list(request.time_codes)
            return {
                "success": True,
                "message": f"Successfully rendered {len(rendered_files)} frame(s).",
                "rendered_frames": rendered_frames,
                "metadata": {
                    "width": request.width,
                    "height": request.height,
                    "quality": request.quality,
                    "dimensions": f"{request.width}x{request.height}",
                    "frame_count": len(rendered_files),
                    "time_codes": time_codes,
                    "time_range": (
                        [min(time_codes), max(time_codes)] if time_codes else []
                    ),
                    "rendered_files": rendered_files,
                },
                "logs": captured.getvalue().splitlines(),
                "shader_info": shader_info,
            }
        except ISFShaderError as e:
            return self._error_result(
                self._format_error_message_for_ai(e.message, e.to_dict()),
                e.to_dict(),
                logs=captured.getvalue().splitlines(),
            )
        except Exception as e:
            details = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
            }
            return self._error_result(
                self._format_error_message_for_ai(str(e), details),
                details,
                logs=captured.getvalue().splitlines(),
            )
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)

    async def _validate_shader(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an ISF shader and extract its metadata."""
        try:
            request = ValidateRequest(**arguments)
        except Exception as e:
            return ValidateResponse(
                success=False,
                message=f"Invalid validate request: {e}",
                shader_info=None,
                errors=[str(e)],
                warnings=[],
            ).model_dump()

        content = request.shader_content
        errors: List[str] = []
        warnings: List[str] = []

        if not content.strip():
            errors.append("Shader content is empty")

        # Single compile attempt — no second render needed to get the details.
        validation_error = self.renderer.validate_shader_detailed(content)
        is_valid = validation_error is None
        if not is_valid:
            errors.append("Shader validation failed")

        shader_info = self.renderer.get_shader_info(content)

        upper = content.upper()
        if "TIME" not in upper:
            warnings.append("No TIME uniform found - shader may not animate")
        if "RENDERSIZE" not in upper:
            warnings.append(
                "No RENDERSIZE uniform found - shader may not be responsive"
            )

        response = ValidateResponse(
            success=is_valid and not errors,
            message="Shader validation completed",
            shader_info=shader_info,
            errors=errors,
            warnings=warnings,
        ).model_dump()
        if validation_error is not None:
            response["error_details"] = validation_error.to_dict()
        return response

    async def _get_shader_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from an ISF shader."""
        try:
            request = GetShaderInfoRequest(**arguments)
        except Exception as e:
            return GetShaderInfoResponse(
                success=False,
                message=f"Invalid request: {e}",
                shader_info=None,
                errors=[str(e)],
            ).model_dump()

        shader_info = self.renderer.get_shader_info(request.shader_content)
        return GetShaderInfoResponse(
            success=True,
            message="Shader information extracted successfully",
            shader_info=shader_info,
            errors=[],
        ).model_dump()

    @staticmethod
    def _error_result(
        message: str,
        error_details: Optional[Dict[str, Any]] = None,
        logs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build a render failure response with a shape consistent with success."""
        return {
            "success": False,
            "message": message,
            "rendered_frames": [],
            "metadata": {},
            "logs": logs if logs is not None else [f"ERROR: {message}"],
            "shader_info": None,
            "error_details": error_details,
        }

    async def list_resources(self) -> List[Resource]:
        """List available resources (shader examples)."""
        return [
            Resource(
                uri="isf://examples/basic",
                name="Basic ISF Shader Example",
                description="A simple ISF shader example with basic color output",
            ),
            Resource(
                uri="isf://examples/animated",
                name="Animated ISF Shader Example",
                description="An animated ISF shader example with time-based animation",
            ),
            Resource(
                uri="isf://examples/gradient",
                name="Gradient ISF Shader Example",
                description="A gradient-based ISF shader example",
            ),
        ]

    async def read_resource(self, uri: str) -> bytes:
        """Read resource content (shader examples)."""
        uri_str = str(uri)
        examples = {
            "isf://examples/basic": self._get_basic_shader_example,
            "isf://examples/animated": self._get_animated_shader_example,
            "isf://examples/gradient": self._get_gradient_shader_example,
        }
        if uri_str not in examples:
            raise ValueError(f"Unknown resource: {uri_str}")
        return examples[uri_str]().encode()

    def _get_basic_shader_example(self) -> str:
        """Get basic shader example."""
        return """/*{
    "DESCRIPTION": "Basic ISF Shader Example",
    "CREDIT": "Generated by ISF Shader Renderer",
    "CATEGORIES": ["Basic"],
    "INPUTS": []
}*/

void main() {
    vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy;
    vec3 color = vec3(uv.x, uv.y, 0.5);
    gl_FragColor = vec4(color, 1.0);
}"""

    def _get_animated_shader_example(self) -> str:
        """Get animated shader example."""
        return """/*{
    "DESCRIPTION": "Animated ISF Shader Example",
    "CREDIT": "Generated by ISF Shader Renderer",
    "CATEGORIES": ["Animation"],
    "INPUTS": []
}*/

void main() {
    vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy;

    // Create animated wave pattern
    float wave = sin(uv.x * 10.0 + TIME * 2.0) * 0.5 + 0.5;
    wave += sin(uv.y * 8.0 + TIME * 1.5) * 0.5 + 0.5;

    vec3 color = vec3(wave, wave * 0.5, wave * 0.8);
    gl_FragColor = vec4(color, 1.0);
}"""

    def _get_gradient_shader_example(self) -> str:
        """Get gradient shader example."""
        return """/*{
    "DESCRIPTION": "Gradient ISF Shader Example",
    "CREDIT": "Generated by ISF Shader Renderer",
    "CATEGORIES": ["Gradient"],
    "INPUTS": []
}*/

void main() {
    vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy;

    // Create radial gradient
    vec2 center = vec2(0.5, 0.5);
    float dist = distance(uv, center);

    vec3 color = vec3(1.0 - dist, dist, 0.5);
    gl_FragColor = vec4(color, 1.0);
}"""

    def _format_error_message_for_ai(
        self, error_message: str, error_info: Optional[Dict[str, Any]]
    ) -> str:
        """
        Format error messages to be more helpful for AI users.

        Args:
            error_message: The raw error message
            error_info: Detailed error information dictionary

        Returns:
            Formatted error message suitable for AI consumption
        """
        # Handle common ISF validation errors
        if "ISF metadata" in error_message:
            if "validation errors for ISFInput" in error_message:
                if "min" in error_message.lower() and "max" in error_message.lower():
                    return (
                        "ISF metadata validation error: MIN and MAX values for point2D inputs should be single numbers, not arrays. "
                        "For point2D inputs like 'uOffset', remove the MIN/MAX fields or use single numeric values. "
                        "Example: Remove 'MIN': [-1.0, -1.0] and 'MAX': [1.0, 1.0] from the uOffset input definition."
                    )

                return (
                    "ISF metadata validation error: One or more input parameters have invalid MIN/MAX values. "
                    "Check that MIN and MAX values match the input TYPE (float inputs need single numbers, not arrays)."
                )

            return (
                "ISF metadata validation error: The JSON header in the shader contains invalid input definitions. "
                "Check that all INPUTS have valid TYPE, DEFAULT, MIN, and MAX values according to ISF specification."
            )

        # Handle GLSL compilation errors
        if "GLSL" in error_message or "compilation" in error_message:
            return (
                "GLSL compilation error: The shader code contains syntax errors or invalid GLSL constructs. "
                "Check for missing semicolons, undefined variables, or invalid function calls in the shader code."
            )

        # Handle missing main function
        if "main function" in error_message.lower() or "main()" in error_message:
            return (
                "Shader structure error: The shader is missing a 'void main()' function. "
                "Every ISF shader must have a main function that sets gl_FragColor."
            )

        # Handle missing gl_FragColor
        if "gl_FragColor" in error_message.lower():
            return (
                "Shader output error: The shader does not assign a value to gl_FragColor. "
                "Every ISF shader must set gl_FragColor in the main function."
            )

        # Handle empty content
        if "empty" in error_message.lower():
            return (
                "Shader content error: The shader content is empty or contains only whitespace. "
                "Please provide valid ISF shader code with a JSON header and main function."
            )

        # Handle ISF header errors
        if "ISF header" in error_message.lower():
            return (
                "ISF header error: The shader does not have a valid ISF JSON header. "
                "ISF shaders should start with a JSON block like /*{ ... }*/ containing metadata."
            )

        # Generic error with suggestions
        return (
            f"Shader error: {error_message}. "
            "Common issues include: invalid ISF metadata, GLSL syntax errors, missing main function, "
            "or incorrect input parameter definitions. Check the shader code and ISF specification."
        )
