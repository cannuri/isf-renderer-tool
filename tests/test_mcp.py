"""Tests for MCP server functionality."""

import tempfile
from pathlib import Path

import pytest

from isf_shader_renderer.mcp.handlers import ISFShaderHandlers
from isf_shader_renderer.mcp.models import (
    GetShaderInfoRequest,
    RenderRequest,
    ValidateRequest,
)
from isf_shader_renderer.mcp.utils import (
    create_temp_file,
    decode_base64_to_image,
    encode_image_to_base64,
    extract_shader_metadata,
    sanitize_filename,
    validate_shader_content,
)


class TestMCPModels:
    """Test MCP request/response models."""

    def test_render_request_valid(self):
        """Test valid render request."""
        request = RenderRequest(
            shader_content="/* ISF shader */ void main() { gl_FragColor = vec4(1.0); }",
            time_codes=[0.0, 1.0, 2.0],
            width=640,
            height=480,
            quality=95,
            verbose=True,
        )

        assert (
            request.shader_content
            == "/* ISF shader */ void main() { gl_FragColor = vec4(1.0); }"
        )
        assert request.time_codes == [0.0, 1.0, 2.0]
        assert request.width == 640
        assert request.height == 480
        assert request.quality == 95
        assert request.verbose is True

    def test_render_request_defaults(self):
        """Test render request with defaults."""
        request = RenderRequest(
            shader_content="/* ISF shader */ void main() { gl_FragColor = vec4(1.0); }",
            time_codes=[0.0],
        )

        assert request.width == 1920
        assert request.height == 1080
        assert request.quality == 95
        assert request.verbose is False

    def test_validate_request(self):
        """Test validate request."""
        request = ValidateRequest(
            shader_content="/* ISF shader */ void main() { gl_FragColor = vec4(1.0); }"
        )

        assert (
            request.shader_content
            == "/* ISF shader */ void main() { gl_FragColor = vec4(1.0); }"
        )

    def test_get_shader_info_request(self):
        """Test get shader info request."""
        request = GetShaderInfoRequest(
            shader_content="/* ISF shader */ void main() { gl_FragColor = vec4(1.0); }"
        )

        assert (
            request.shader_content
            == "/* ISF shader */ void main() { gl_FragColor = vec4(1.0); }"
        )


class TestMCPUtils:
    """Test MCP utility functions."""

    def test_validate_shader_content_valid(self):
        """Test validation of valid shader content."""
        shader_content = """/*{
    "DESCRIPTION": "Test shader",
    "CREDIT": "Test"
}*/
void main() {
    gl_FragColor = vec4(1.0);
}"""

        errors = validate_shader_content(shader_content)
        assert len(errors) == 0

    def test_validate_shader_content_empty(self):
        """Test validation of empty shader content."""
        errors = validate_shader_content("")
        assert len(errors) == 1
        assert "empty" in errors[0]

    def test_validate_shader_content_no_main(self):
        """Test validation of shader without main function."""
        shader_content = "/* ISF shader */ vec4 color = vec4(1.0);"

        errors = validate_shader_content(shader_content)
        assert len(errors) > 0
        assert any("main function" in error for error in errors)

    def test_extract_shader_metadata(self):
        """Test shader metadata extraction."""
        shader_content = """/*{
    "DESCRIPTION": "Test shader",
    "CREDIT": "Test Author",
    "CATEGORIES": ["Test"],
    "INPUTS": [],
    "PASSES": []
}*/
void main() {
    gl_FragColor = vec4(1.0);
}"""

        metadata = extract_shader_metadata(shader_content)

        assert metadata["type"] == "ISF"
        assert metadata["size"] == len(shader_content)
        assert metadata["lines"] == len(shader_content.splitlines())
        assert metadata["has_time_uniform"] is False
        assert metadata["has_resolution_uniform"] is False
        assert "isf_header" in metadata
        assert metadata["description"] == "Test shader"
        assert metadata["credit"] == "Test Author"
        assert metadata["categories"] == ["Test"]
        assert metadata["input_count"] == 0
        assert metadata["pass_count"] == 0

    def test_extract_shader_metadata_with_uniforms(self):
        """Test shader metadata extraction with uniforms."""
        shader_content = """/*{
    "DESCRIPTION": "Test shader with uniforms"
}*/
void main() {
    vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy;
    float time = TIME;
    gl_FragColor = vec4(uv.x, uv.y, time, 1.0);
}"""

        metadata = extract_shader_metadata(shader_content)

        assert metadata["has_time_uniform"] is True
        assert metadata["has_resolution_uniform"] is True

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test unsafe characters
        unsafe_name = 'file<>:"/\\|?*.txt'
        sanitized = sanitize_filename(unsafe_name)
        assert sanitized == "file_________.txt"

        # Test long filename
        long_name = "a" * 300
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) == 255

    def test_create_temp_file(self):
        """Test temporary file creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = create_temp_file(suffix=".png", directory=Path(temp_dir))
            assert temp_path.suffix == ".png"
            assert temp_path.parent == Path(temp_dir)
            assert not temp_path.exists()  # File is created but empty

    def test_encode_decode_image(self):
        """Test image encoding and decoding."""
        # Create a simple test image
        import numpy as np
        from PIL import Image

        # Create a small test image
        test_image = Image.fromarray(
            np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            test_image.save(temp_file.name)
            temp_path = Path(temp_file.name)

        try:
            # Encode to base64
            base64_data = encode_image_to_base64(temp_path)
            assert isinstance(base64_data, str)
            assert len(base64_data) > 0

            # Decode back to file
            output_path = temp_path.with_name("decoded.png")
            decode_base64_to_image(base64_data, output_path)

            # Verify files are the same
            assert output_path.exists()
            assert output_path.stat().st_size == temp_path.stat().st_size

            # Clean up
            output_path.unlink()
        finally:
            temp_path.unlink()


class TestMCPHandlers:
    """Test MCP handlers."""

    @pytest.fixture
    def handlers(self):
        """Create handlers instance for testing."""
        return ISFShaderHandlers()

    @pytest.mark.asyncio
    async def test_render_shader_success(self, handlers):
        """Test successful shader rendering."""
        shader_content = """/*{
    "DESCRIPTION": "Test shader"
}*/
void main() {
    gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
}"""

        result = await handlers.call_tool(
            "render_shader",
            {
                "shader_content": shader_content,
                "time_codes": [0.0, 1.0],
                "width": 64,
                "height": 64,
            },
        )

        assert result["success"] is True
        assert len(result["rendered_frames"]) == 2
        assert "metadata" in result
        assert "shader_info" in result
        assert result["metadata"]["frame_count"] == 2

    @pytest.mark.asyncio
    async def test_render_shader_invalid(self, handlers):
        """Test shader rendering with invalid shader."""
        result = await handlers.call_tool(
            "render_shader", {"shader_content": "", "time_codes": [0.0]}
        )

        assert result["success"] is False
        assert "Invalid shader content" in result["message"]

    @pytest.mark.asyncio
    async def test_validate_shader_success(self, handlers):
        """Test successful shader validation."""
        shader_content = """/*{
    "DESCRIPTION": "Test shader"
}*/
void main() {
    gl_FragColor = vec4(1.0);
}"""

        result = await handlers.call_tool(
            "validate_shader", {"shader_content": shader_content}
        )

        assert result["success"] is True
        assert "shader_info" in result
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_shader_with_warnings(self, handlers):
        """Test shader validation with warnings."""
        shader_content = """/*{
    "DESCRIPTION": "Test shader"
}*/
void main() {
    gl_FragColor = vec4(1.0);
}"""

        result = await handlers.call_tool(
            "validate_shader", {"shader_content": shader_content}
        )

        assert result["success"] is True
        assert len(result["warnings"]) > 0
        assert any("TIME uniform" in warning for warning in result["warnings"])

    @pytest.mark.asyncio
    async def test_get_shader_info(self, handlers):
        """Test shader info extraction."""
        shader_content = """/*{
    "DESCRIPTION": "Test shader",
    "CREDIT": "Test Author"
}*/
void main() {
    gl_FragColor = vec4(1.0);
}"""

        result = await handlers.call_tool(
            "get_shader_info", {"shader_content": shader_content}
        )

        assert result["success"] is True
        assert "shader_info" in result
        assert result["shader_info"]["description"] == "Test shader"
        assert result["shader_info"]["credit"] == "Test Author"

    @pytest.mark.asyncio
    async def test_unknown_tool(self, handlers):
        """Test handling of unknown tool."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await handlers.call_tool("unknown_tool", {})

    @pytest.mark.asyncio
    async def test_list_resources(self, handlers):
        """Test resource listing."""
        resources = await handlers.list_resources()

        assert len(resources) == 3
        resource_uris = [r.uri for r in resources]
        assert "isf://examples/basic" in resource_uris
        assert "isf://examples/animated" in resource_uris
        assert "isf://examples/gradient" in resource_uris

    @pytest.mark.asyncio
    async def test_read_resource(self, handlers):
        """Test resource reading."""
        content = await handlers.read_resource("isf://examples/basic")

        assert isinstance(content, bytes)
        decoded = content.decode()
        assert "Basic ISF Shader Example" in decoded
        assert "void main()" in decoded

    @pytest.mark.asyncio
    async def test_read_unknown_resource(self, handlers):
        """Test reading unknown resource."""
        with pytest.raises(ValueError, match="Unknown resource"):
            await handlers.read_resource("isf://unknown/resource")
