"""Tests for Aurora Borealis shader through MCP framework."""

import base64
import tempfile
from pathlib import Path

import pytest

from isf_shader_renderer.mcp.handlers import ISFShaderHandlers
from isf_shader_renderer.mcp.utils import (
    extract_shader_metadata,
    validate_shader_content,
)

# Aurora Borealis shader content
AURORA_SHADER = """/*{
    "CATEGORIES": ["Nature", "Aurora", "Organic", "Flow"],
    "CREDIT": "Jim Cortez - Commune Project (Original: ISF Import by Old Salt)",
    "DESCRIPTION": "Creates a mesmerizing aurora borealis effect with flowing, ethereal light patterns that dance across the screen. Features multiple layers of sinuous light bands that move and morph organically, simulating the natural phenomenon of the northern lights with customizable colors and movement controls.",
    "INPUTS": [
        {
            "DEFAULT": [0.0, 1.0, 0.0, 1.0],
            "NAME": "uC1",
            "TYPE": "color"
        },
        {
            "DEFAULT": [0.0, 0.0, 1.0, 1.0],
            "NAME": "uC2",
            "TYPE": "color"
        },
        {
            "DEFAULT": [1.0, 0.0, 0.0, 1.0],
            "NAME": "uC3",
            "TYPE": "color"
        },
        {
            "DEFAULT": [0.0, 0.0],
            "LABEL": "Offset: ",
            "MAX": [1.0, 1.0],
            "MIN": [-1.0, -1.0],
            "NAME": "uOffset",
            "TYPE": "point2D"
        },
        {
            "DEFAULT": 1.0,
            "LABEL": "Zoom: ",
            "MAX": 10.0,
            "MIN": 1.0,
            "NAME": "uZoom",
            "TYPE": "float"
        },
        {
            "DEFAULT": 0.0,
            "LABEL": "Rotation(or R Speed):",
            "MAX": 180.0,
            "MIN": -180.0,
            "NAME": "uRotate",
            "TYPE": "float"
        },
        {
            "DEFAULT": 1,
            "LABEL": "Continuous Rotation? ",
            "NAME": "uContRot",
            "TYPE": "bool"
        },
        {
            "DEFAULT": 0,
            "LABEL": "Color Mode: ",
            "LABELS": [
                "Shader Defaults ",
                "Alternate Color Palette (3 used) "
            ],
            "NAME": "uColMode",
            "TYPE": "long",
            "VALUES": [0, 1]
        },
        {
            "DEFAULT": 1.0,
            "LABEL": "Intensity: ",
            "MAX": 4.0,
            "MIN": 0.0,
            "NAME": "uIntensity",
            "TYPE": "float"
        },
        {
            "DEFAULT": 18.0,
            "LABEL": "Iterations: ",
            "MAX": 32.0,
            "MIN": 8.0,
            "NAME": "uIterations",
            "TYPE": "float"
        },
        {
            "DEFAULT": 0.3,
            "LABEL": "Animation Speed: ",
            "MAX": 2.0,
            "MIN": 0.0,
            "NAME": "uAnimSpeed",
            "TYPE": "float"
        },
        {
            "DEFAULT": 0.99,
            "LABEL": "Scale Factor: ",
            "MAX": 1.0,
            "MIN": 0.8,
            "NAME": "uScaleFactor",
            "TYPE": "float"
        }
    ],
    "ISFVSN": "2"
}*/

/*
ORIGINAL SHADER INFORMATION:
- Original Author: ISF Import by Old Salt
- Original Shader: http://www.glslsandbox.com/e#58544.0
- Source: Originally sourced from editor.isf.video - Aurora by ISF Import by Old Salt
- Description: Aurora borealis effect with flowing, ethereal light patterns
- License: GLSL Sandbox license
- Features: Color customization, rotation controls, zoom and offset functions
*/

#define PI 3.141592653589
#define rotate2D(a) mat2(cos(a),-sin(a),sin(a),cos(a))

void main()
{
    vec2 uv = gl_FragCoord.xy/RENDERSIZE - 0.5; // normalize coordinates
    uv.x *= RENDERSIZE.x/RENDERSIZE.y;          // correct aspect ratio
    uv = (uv-uOffset) * 3.0/uZoom;              // offset and zoom functions

    // Fixed rotation calculation - now consistent between continuous and static modes
    float rotationAngle = uRotate * PI / 180.0;
    if (uContRot) {
        rotationAngle += TIME * uAnimSpeed;
    }
    uv = uv * rotate2D(rotationAngle);

    vec2 p = uv;
    float d = 2.0 * length(p);
    vec3 col = vec3(0.0);

    // Use configurable iterations with proper casting and GLSL-compatible loop
    int iterations = int(clamp(uIterations, 8.0, 32.0));

    // GLSL-compatible loop with fixed bounds and blend factor for fractional iterations
    for (int i = 0; i < 32; i++)
    {
        float blendFactor = 1.0;
        if (float(i) >= float(iterations)) {
            blendFactor = 0.0;
        }

        float dist = abs(p.y + sin(float(i) + TIME * uAnimSpeed + 3.0 * p.x)) - 0.2;
        if (dist < 1.0) {
            col += blendFactor * (1.0 - pow(abs(dist), 0.28)) * vec3(0.8 + 0.2 * sin(TIME), 0.9 + 0.1 * sin(TIME * 1.1), 1.2);
        }

        // Improved precision with safer division
        float scaleDivisor = max(d, 1e-6);
        p *= uScaleFactor / scaleDivisor;
        p *= rotate2D(PI / 60.0);
    }
    col *= 0.49;

    vec4 cShad = vec4(col - d - 0.4, 1.0);
    vec3 cOut = cShad.rgb;

    // Optimized color mode switching
    if (uColMode == 1) {
        cOut = uC1.rgb * cShad.r + uC2.rgb * cShad.g + uC3.rgb * cShad.b;
    }

    cOut = cOut * uIntensity;
    cOut = clamp(cOut, vec3(0.0), vec3(1.0));
    gl_FragColor = vec4(cOut.rgb, cShad.a);
}"""


class TestAuroraShaderValidation:
    """Test Aurora shader validation through MCP framework."""

    def test_aurora_shader_content_validation(self):
        """Test that the Aurora shader content is valid."""
        errors = validate_shader_content(AURORA_SHADER)
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_aurora_shader_has_main_function(self):
        """Test that the Aurora shader has a main function."""
        assert "void main()" in AURORA_SHADER
        assert "gl_FragColor" in AURORA_SHADER

    def test_aurora_shader_has_isf_header(self):
        """Test that the Aurora shader has proper ISF header."""
        assert "CATEGORIES" in AURORA_SHADER
        assert "DESCRIPTION" in AURORA_SHADER
        assert "CREDIT" in AURORA_SHADER
        assert "INPUTS" in AURORA_SHADER

    def test_aurora_shader_has_time_uniform(self):
        """Test that the Aurora shader uses TIME uniform."""
        assert "TIME" in AURORA_SHADER

    def test_aurora_shader_has_resolution_uniform(self):
        """Test that the Aurora shader uses RENDERSIZE uniform."""
        assert "RENDERSIZE" in AURORA_SHADER


class TestAuroraShaderMetadata:
    """Test Aurora shader metadata extraction through MCP framework."""

    def test_aurora_shader_metadata_extraction(self):
        """Test extraction of Aurora shader metadata."""
        metadata = extract_shader_metadata(AURORA_SHADER)

        # Basic metadata
        assert metadata["type"] == "ISF"
        assert metadata["size"] == len(AURORA_SHADER)
        assert metadata["lines"] == len(AURORA_SHADER.splitlines())

        # ISF-specific metadata
        assert metadata["has_time_uniform"] is True
        assert metadata["has_resolution_uniform"] is True
        assert "isf_header" in metadata

        # Aurora-specific metadata
        assert (
            metadata["description"]
            == "Creates a mesmerizing aurora borealis effect with flowing, ethereal light patterns that dance across the screen. Features multiple layers of sinuous light bands that move and morph organically, simulating the natural phenomenon of the northern lights with customizable colors and movement controls."
        )
        assert (
            metadata["credit"]
            == "Jim Cortez - Commune Project (Original: ISF Import by Old Salt)"
        )
        assert "Nature" in metadata["categories"]
        assert "Aurora" in metadata["categories"]
        assert "Organic" in metadata["categories"]
        assert "Flow" in metadata["categories"]

        # Input metadata
        assert metadata["input_count"] == 12  # All the uC1, uC2, uC3, uOffset, etc.
        # Note: pass_count is only present if PASSES field exists in ISF header
        # Aurora shader is single-pass, so this field may not be present


class TestAuroraShaderMCPHandlers:
    """Test Aurora shader through MCP handlers."""

    @pytest.fixture
    def handlers(self):
        """Create handlers instance for testing."""
        return ISFShaderHandlers()

    @pytest.mark.asyncio
    async def test_aurora_shader_validation_through_mcp(self, handlers):
        """Test Aurora shader validation through MCP handlers."""
        result = await handlers.call_tool(
            "validate_shader", {"shader_content": AURORA_SHADER}
        )

        assert result["success"] is True
        assert "valid" in result["message"].lower()
        assert "errors" not in result or len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_aurora_shader_info_through_mcp(self, handlers):
        """Test Aurora shader info extraction through MCP handlers."""
        result = await handlers.call_tool(
            "get_shader_info", {"shader_content": AURORA_SHADER}
        )

        assert result["success"] is True
        assert "shader_info" in result

        info = result["shader_info"]
        assert info["type"] == "ISF"
        assert (
            info["description"]
            == "Creates a mesmerizing aurora borealis effect with flowing, ethereal light patterns that dance across the screen. Features multiple layers of sinuous light bands that move and morph organically, simulating the natural phenomenon of the northern lights with customizable colors and movement controls."
        )
        assert (
            info["credit"]
            == "Jim Cortez - Commune Project (Original: ISF Import by Old Salt)"
        )
        assert info["has_time_uniform"] is True
        assert info["has_resolution_uniform"] is True

    @pytest.mark.asyncio
    async def test_aurora_shader_rendering_through_mcp(self, handlers):
        """Test Aurora shader rendering through MCP handlers."""
        result = await handlers.call_tool(
            "render_shader",
            {
                "shader_content": AURORA_SHADER,
                "time_codes": [0.0, 1.0, 2.0],
                "width": 320,
                "height": 240,
                "quality": 95,
                "verbose": True,
            },
        )

        assert result["success"] is True
        assert "rendered_frames" in result
        assert len(result["rendered_frames"]) == 3  # Three time codes

        # Check that frames are base64-encoded images
        for frame_b64 in result["rendered_frames"]:
            assert isinstance(frame_b64, str)
            assert len(frame_b64) > 0
            # Verify it's valid base64
            try:
                decoded = base64.b64decode(frame_b64)
                assert len(decoded) > 0
            except Exception:
                pytest.fail("Invalid base64 encoding in rendered frame")

    @pytest.mark.asyncio
    async def test_aurora_shader_rendering_with_custom_parameters(self, handlers):
        """Test Aurora shader rendering with custom input parameters."""
        # Test with different color mode and intensity
        result = await handlers.call_tool(
            "render_shader",
            {
                "shader_content": AURORA_SHADER,
                "time_codes": [0.5],
                "width": 640,
                "height": 480,
                "quality": 90,
                "verbose": False,
                "shader_inputs": {
                    "uColMode": 1,  # Use alternate color palette
                    "uIntensity": 2.0,  # Higher intensity
                    "uZoom": 2.0,  # Zoom in
                    "uAnimSpeed": 0.5,  # Faster animation
                    "uC1": [1.0, 0.0, 0.0, 1.0],  # Red
                    "uC2": [0.0, 1.0, 0.0, 1.0],  # Green
                    "uC3": [0.0, 0.0, 1.0, 1.0],  # Blue
                },
            },
        )

        assert result["success"] is True
        assert len(result["rendered_frames"]) == 1

    @pytest.mark.asyncio
    async def test_aurora_shader_rendering_animation_sequence(self, handlers):
        """Test Aurora shader rendering with animation sequence."""
        # Test with more time codes to create animation
        time_codes = [i * 0.2 for i in range(10)]  # 0.0, 0.2, 0.4, ..., 1.8

        result = await handlers.call_tool(
            "render_shader",
            {
                "shader_content": AURORA_SHADER,
                "time_codes": time_codes,
                "width": 480,
                "height": 360,
                "quality": 85,
                "verbose": True,
                "shader_inputs": {
                    "uContRot": True,  # Enable continuous rotation
                    "uAnimSpeed": 0.8,  # Medium animation speed
                    "uIterations": 24.0,  # More iterations for detail
                },
            },
        )

        assert result["success"] is True
        assert len(result["rendered_frames"]) == 10

        # Verify metadata
        assert "metadata" in result
        metadata = result["metadata"]
        assert metadata["width"] == 480
        assert metadata["height"] == 360
        assert metadata["frame_count"] == 10
        assert metadata["time_range"] == [0.0, 1.8]


class TestAuroraShaderFileOperations:
    """Test Aurora shader file operations through MCP framework."""

    @pytest.fixture
    def handlers(self):
        """Create handlers instance for testing."""
        return ISFShaderHandlers()

    @pytest.mark.asyncio
    async def test_aurora_shader_from_file(self, handlers):
        """Test Aurora shader loaded from file."""
        # Create temporary shader file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fs", delete=False
        ) as temp_file:
            temp_file.write(AURORA_SHADER)
            temp_path = Path(temp_file.name)

        try:
            # Read the shader file
            shader_content = temp_path.read_text()

            # Test rendering from file content
            result = await handlers.call_tool(
                "render_shader",
                {
                    "shader_content": shader_content,
                    "time_codes": [0.0],
                    "width": 320,
                    "height": 240,
                    "quality": 95,
                    "verbose": False,
                },
            )

            assert result["success"] is True
            assert len(result["rendered_frames"]) == 1

        finally:
            # Clean up
            temp_path.unlink()

    @pytest.mark.asyncio
    async def test_aurora_shader_save_rendered_frames(self, handlers):
        """Test saving rendered Aurora shader frames to files."""
        result = await handlers.call_tool(
            "render_shader",
            {
                "shader_content": AURORA_SHADER,
                "time_codes": [0.0, 1.0],
                "width": 320,
                "height": 240,
                "quality": 95,
                "verbose": False,
            },
        )

        assert result["success"] is True
        assert len(result["rendered_frames"]) == 2

        # Save frames to files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for i, frame_b64 in enumerate(result["rendered_frames"]):
                # Decode base64 to image
                image_data = base64.b64decode(frame_b64)

                # Save to file
                output_file = temp_path / f"aurora_frame_{i:02d}.jpg"
                output_file.write_bytes(image_data)

                # Verify file was created and has content
                assert output_file.exists()
                assert output_file.stat().st_size > 0

                # Verify it's a valid image by checking file size
                assert output_file.stat().st_size > 1000  # Should be at least 1KB


class TestAuroraShaderErrorHandling:
    """Test Aurora shader error handling through MCP framework."""

    @pytest.fixture
    def handlers(self):
        """Create handlers instance for testing."""
        return ISFShaderHandlers()

    @pytest.mark.asyncio
    async def test_aurora_shader_tolerates_out_of_range_inputs(self, handlers):
        """Out-of-range input values should be tolerated, not crash the render.

        The Aurora shader is valid (see test_aurora_shader_validation_through_mcp),
        and the backend clamps/ignores out-of-range input values rather than
        failing, so the render still succeeds.
        """
        result = await handlers.call_tool(
            "render_shader",
            {
                "shader_content": AURORA_SHADER,
                "time_codes": [0.0],
                "width": 320,
                "height": 240,
                "quality": 95,
                "verbose": False,
                "shader_inputs": {
                    "uIntensity": 10.0,  # Above the input's nominal max
                    "uZoom": 0.5,  # Below the input's nominal min
                    "uIterations": 50.0,  # Above the input's nominal max
                },
            },
        )

        assert result["success"] is True
        assert len(result["rendered_frames"]) == 1

    @pytest.mark.asyncio
    async def test_aurora_shader_missing_content(self, handlers):
        """Test Aurora shader with missing content."""
        result = await handlers.call_tool(
            "render_shader",
            {
                "shader_content": "",
                "time_codes": [0.0],
                "width": 320,
                "height": 240,
                "quality": 95,
                "verbose": False,
            },
        )

        assert result["success"] is False
        assert (
            "invalid" in result["message"].lower()
            or "error" in result["message"].lower()
        )


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
