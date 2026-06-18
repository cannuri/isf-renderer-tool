"""Contract tests for the MCP render path (the AI render->evaluate->refine loop).

These assert the guarantees an LLM-in-the-loop depends on: rendered frames come
back as usable base64 PNGs, the requested dimensions are honoured and reported,
failures return a consistent shape with a typed error code, and the server does
not leak temporary files to disk.
"""

import base64
import glob
import os
import tempfile

import pytest

from isf_shader_renderer.mcp.handlers import ISFShaderHandlers

VALID_SHADER = """/*{
    "DESCRIPTION": "Contract test shader",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() {
    vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy;
    gl_FragColor = vec4(uv, 0.5, 1.0);
}"""

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def handlers():
    return ISFShaderHandlers()


async def test_render_returns_png_frames_and_honours_dimensions(handlers):
    result = await handlers.call_tool(
        "render_shader",
        {
            "shader_content": VALID_SHADER,
            "time_codes": [0.0, 1.0],
            "width": 320,
            "height": 240,
        },
    )
    assert result["success"] is True
    assert len(result["rendered_frames"]) == 2

    # Frames are real, decodable PNGs the model can actually view.
    for frame in result["rendered_frames"]:
        assert base64.b64decode(frame)[:8] == PNG_MAGIC

    # Requested dimensions are honoured and reported back in the metadata.
    md = result["metadata"]
    assert md["width"] == 320
    assert md["height"] == 240
    assert md["frame_count"] == 2
    assert md["time_range"] == [0.0, 1.0]


async def test_render_does_not_leak_temp_dirs(handlers):
    pattern = os.path.join(tempfile.gettempdir(), "isf_render_*")
    before = set(glob.glob(pattern))
    await handlers.call_tool(
        "render_shader",
        {
            "shader_content": VALID_SHADER,
            "time_codes": [0.0],
            "width": 32,
            "height": 32,
        },
    )
    after = set(glob.glob(pattern))
    assert after == before  # the render directory was cleaned up


async def test_render_failure_has_consistent_shape(handlers):
    result = await handlers.call_tool(
        "render_shader", {"shader_content": "", "time_codes": [0.0]}
    )
    assert result["success"] is False
    assert result["rendered_frames"] == []
    assert result["shader_info"] is None
    assert result["error_details"]["error_code"] == "SHADER_VALIDATION_ERROR"
    assert "Invalid shader content" in result["message"]
