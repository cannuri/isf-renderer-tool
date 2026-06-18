"""ISF shader rendering functionality using pyvvisf."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pyvvisf

from .config import ShaderConfig, ShaderRendererConfig
from .errors import ISFShaderError, RenderingError, ShaderValidationError

logger = logging.getLogger(__name__)

# Map ISF JSON metadata keys (which are upper-case by spec) to friendly lower-case keys.
_ISF_KEY_MAP = {
    "DESCRIPTION": "description",
    "CREDIT": "credit",
    "CATEGORIES": "categories",
    "INPUTS": "inputs",
    "PASSES": "passes",
}


def parse_isf_header(shader_content: str) -> Dict[str, Any]:
    """Extract the ISF JSON metadata block (``/*{ ... }*/``).

    Returns the parsed dict, or an empty dict if no valid block is present.
    Never raises.
    """
    match = re.search(r"/\*\{([\s\S]*?)\}\*/", shader_content)
    if not match:
        return {}
    try:
        parsed = json.loads("{" + match.group(1) + "}")
    except (json.JSONDecodeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def normalize_isf_metadata_keys(data: Any) -> Dict[str, Any]:
    """Lower-case ISF metadata keys (e.g. ``DESCRIPTION`` -> ``description``)."""
    if not isinstance(data, dict):
        return {}
    return {_ISF_KEY_MAP.get(k, k.lower()): v for k, v in data.items()}


class ShaderRenderer:
    """Main renderer class for ISF shaders using VVISF.

    Note: rendering uses a process-global OpenGL context (via pyvvisf/GLFW) and
    is therefore not safe to call concurrently from multiple threads. Serialize
    access if you need parallelism.
    """

    def __init__(self, config: ShaderRendererConfig):
        """Initialize the renderer with configuration."""
        self.config = config

    def render_frame(
        self,
        shader_content: str,
        time_code: float,
        output_path: Path,
        shader_config: Optional[ShaderConfig] = None,
    ) -> None:
        """
        Render a single frame of an ISF shader.

        Args:
            shader_content: The ISF shader source code
            time_code: Time offset for the shader (for animated shaders)
            output_path: Path to save the rendered image
            shader_config: Optional shader-specific configuration

        Raises:
            RenderingError: if the shader fails to compile or render. No output
                file is created in that case.
        """
        width, height = self._get_dimensions(shader_config)

        try:
            with pyvvisf.ISFRenderer(shader_content) as renderer:
                # Set shader inputs if provided
                self._set_shader_inputs(renderer, shader_config)

                # Render the frame (TIME and RENDERSIZE are set automatically).
                buffer = renderer.render(width, height, time_offset=time_code)

                image = buffer.to_pil_image()
                if image is None:
                    raise RenderingError(
                        "Failed to render: image is None (buffer conversion failed)"
                    )

                # Only touch the filesystem once we have a valid image, so a
                # failed render never leaves a partial/empty file behind.
                output_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(output_path)

                logger.info("Successfully rendered frame to %s", output_path)

        except Exception as e:
            logger.error("Failed to render frame: %s", e)
            raise RenderingError.from_exception(e) from e

    def _set_shader_inputs(
        self,
        renderer: Any,
        shader_config: Optional[ShaderConfig],
    ) -> None:
        """Set shader input values on the active ISFRenderer instance."""
        if not (shader_config and shader_config.inputs):
            return

        for input_name, input_value in shader_config.inputs.items():
            try:
                renderer.set_input(input_name, self._coerce_input_value(input_value))
            except Exception as e:
                logger.warning("Failed to set input '%s': %s", input_name, e)

    @staticmethod
    def _coerce_input_value(input_value: Any) -> Any:
        """Coerce a string input value to the type ISF expects.

        Non-string values are passed through unchanged (the ISFRenderer
        auto-coerces Python primitives).
        """
        if not isinstance(input_value, str):
            return input_value

        lowered = input_value.lower()
        if lowered in ("true", "1", "yes", "on"):
            return True
        if lowered in ("false", "0", "no", "off"):
            return False

        if "," in input_value or " " in input_value:
            try:
                parts = [
                    float(x.strip())
                    for x in input_value.replace(" ", ",").split(",")
                    if x.strip()
                ]
                if len(parts) in (2, 3, 4):
                    return tuple(parts)
                return float(input_value)
            except ValueError:
                return float(input_value)

        try:
            return float(input_value) if "." in input_value else int(input_value)
        except ValueError:
            return input_value

    def _get_dimensions(self, shader_config: Optional[ShaderConfig]) -> Tuple[int, int]:
        """Get render dimensions from config."""
        if shader_config:
            return (
                shader_config.get_width(self.config.defaults),
                shader_config.get_height(self.config.defaults),
            )
        return self.config.defaults.width, self.config.defaults.height

    def validate_shader_detailed(self, shader_content: str) -> Optional[ISFShaderError]:
        """Validate a shader and return the error, or ``None`` if it is valid.

        This is the single source of truth for validation. It compiles the
        shader exactly once, so callers never need to re-render to obtain the
        error details.
        """
        if not shader_content or not shader_content.strip():
            return ShaderValidationError(
                "Shader content is empty or contains only whitespace."
            )

        if "void main(" not in shader_content and "void main (" not in shader_content:
            return ShaderValidationError("Shader is missing a 'void main()' function.")

        try:
            with pyvvisf.ISFRenderer(shader_content) as renderer:
                # Render a minimal frame to trigger GLSL compilation.
                renderer.render(8, 8, time_offset=0.0)
        except Exception as e:
            logger.warning("Shader validation failed: %s", e)
            return ShaderValidationError.from_exception(e)
        return None

    def validate_shader(self, shader_content: str) -> bool:
        """Return True if the shader is valid, False otherwise."""
        return self.validate_shader_detailed(shader_content) is None

    def get_shader_info(self, shader_content: str) -> Dict[str, Any]:
        """
        Extract metadata from ISF shader content.

        Returns a dict with a stable shape (always includes ``type``, ``size``,
        ``lines``, ``has_*_uniform``, ``description`` and ``credit``), merged
        with any fields parsed from the ISF JSON header. Never raises and never
        requires an OpenGL context.
        """
        upper = shader_content.upper()
        info: Dict[str, Any] = {
            "type": "ISF",
            "size": len(shader_content),
            "lines": len(shader_content.splitlines()),
            "has_time_uniform": "TIME" in upper,
            "has_resolution_uniform": "RENDERSIZE" in upper,
            "has_mouse_uniform": "MOUSE" in upper,
            "has_date_uniform": "DATE" in upper,
            "description": None,
            "credit": None,
            "categories": None,
        }

        header = parse_isf_header(shader_content)
        if header:
            info["isf_header"] = header
            normalized = normalize_isf_metadata_keys(header)
            for key in ("description", "credit", "categories"):
                if normalized.get(key) is not None:
                    info[key] = normalized[key]
            inputs = normalized.get("inputs")
            if isinstance(inputs, list):
                info["inputs"] = inputs
                info["input_count"] = len(inputs)
            passes = normalized.get("passes")
            if isinstance(passes, list):
                info["pass_count"] = len(passes)

        return info

    def cleanup(self) -> None:
        """Clean up resources (ISFRenderer manages its own GL context teardown)."""
        logger.debug("Cleanup completed.")
