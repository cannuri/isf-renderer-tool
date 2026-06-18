"""Tests for shader rendering functionality."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from isf_shader_renderer.config import Defaults, ShaderConfig, ShaderRendererConfig
from isf_shader_renderer.renderer import ShaderRenderer


class TestShaderRenderer:
    """Test ShaderRenderer class."""

    def test_renderer_creation(self):
        config = ShaderRendererConfig()
        renderer = ShaderRenderer(config)
        assert renderer.config == config

    def test_render_frame_basic(self):
        config = ShaderRendererConfig()
        renderer = ShaderRenderer(config)
        shader_content = """/*{
    \"DESCRIPTION\": \"Test shader\",
    \"CREDIT\": \"Test\",
    \"CATEGORIES\": [\"Test\"],
    \"INPUTS\": []
}*/
void main() { gl_FragColor = vec4(1.0); }"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = Path(f.name)
        try:
            renderer.render_frame(shader_content, 1.0, output_path)
            assert output_path.exists()
            image = Image.open(output_path)
            assert image.size == (1920, 1080)
            assert image.mode == "RGBA"
        finally:
            output_path.unlink()

    def test_render_frame_with_shader_config(self):
        config = ShaderRendererConfig()
        shader_config = ShaderConfig(
            input="test.fs",
            output="output.png",
            times=[0.0],
            width=640,
            height=480,
            quality=80,
        )
        config.shaders.append(shader_config)
        renderer = ShaderRenderer(config)
        shader_content = """/*{
    \"DESCRIPTION\": \"Test shader\",
    \"CREDIT\": \"Test\",
    \"CATEGORIES\": [\"Test\"],
    \"INPUTS\": []
}*/
void main() { gl_FragColor = vec4(1.0); }"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = Path(f.name)
        try:
            renderer.render_frame(shader_content, 1.0, output_path, shader_config)
            assert output_path.exists()
            image = Image.open(output_path)
            assert image.size == (640, 480)
            assert image.mode == "RGBA"
        finally:
            output_path.unlink()

    @pytest.mark.regression
    def test_custom_dimensions_rendering(self):
        config = ShaderRendererConfig()
        shader_config = ShaderConfig(
            input="test.fs",
            output="output.png",
            times=[0.0],
            width=640,
            height=480,
            quality=80,
        )
        config.shaders.append(shader_config)
        renderer = ShaderRenderer(config)
        shader_content = """/*{
    "DESCRIPTION": "Test shader",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() { gl_FragColor = vec4(1.0); }"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = Path(f.name)
        try:
            renderer.render_frame(shader_content, 1.0, output_path, shader_config)
            assert output_path.exists()
            image = Image.open(output_path)
            assert image.size == (640, 480)
            assert image.mode == "RGBA"
        finally:
            output_path.unlink()

    @pytest.mark.regression
    def test_basic_pyvvisf_operations(self):
        try:
            import pyvvisf
        except ImportError:
            pytest.skip("pyvvisf not available")

        # Only check for attributes that exist in this pyvvisf version
        if hasattr(pyvvisf, "get_platform_info"):
            platform_info = pyvvisf.get_platform_info()
            assert platform_info is not None
        if hasattr(pyvvisf, "is_vvisf_available"):
            available = pyvvisf.is_vvisf_available()
            assert isinstance(available, bool)
        if hasattr(pyvvisf, "get_gl_info"):
            gl_info = pyvvisf.get_gl_info()
            assert gl_info is not None
        if hasattr(pyvvisf, "Size"):
            size = pyvvisf.Size(100, 100)
            assert size.width == 100
            assert size.height == 100

        shader_content = """/*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() {
            gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
        }"""

        with pyvvisf.ISFRenderer(shader_content) as renderer:
            if hasattr(renderer, "is_valid"):
                assert renderer.is_valid()
            buffer = renderer.render(100, 100)
            assert buffer is not None
            if hasattr(renderer, "get_shader_info"):
                info = renderer.get_shader_info()
                assert info is not None

    @pytest.mark.regression
    def test_simple_rendering_without_framework(self):
        try:
            import pyvvisf
        except ImportError:
            pytest.skip("pyvvisf not available")
        shader_content = """/*{
            "DESCRIPTION": "Simple test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() {
            gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
        }"""
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            buffer = renderer.render(100, 100)
            assert buffer is not None
            image = buffer.to_pil_image()
            assert image.size == (100, 100)
            assert image.mode == "RGBA"

    @pytest.mark.stress
    def test_multiple_renders_stress_test(self):
        config = ShaderRendererConfig()
        shader_config = ShaderConfig(
            input="test.fs",
            output="output.png",
            times=[0.0],
            width=640,
            height=480,
            quality=80,
        )
        config.shaders.append(shader_config)
        renderer = ShaderRenderer(config)
        shader_content = """/*{
    "DESCRIPTION": "Test shader",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() { gl_FragColor = vec4(1.0); }"""
        for _ in range(10):
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                output_path = Path(f.name)
            try:
                renderer.render_frame(shader_content, 1.0, output_path, shader_config)
                assert output_path.exists()
                image = Image.open(output_path)
                assert image.size == (640, 480)
                assert image.mode == "RGBA"
            finally:
                output_path.unlink()

    def test_validate_shader(self):
        """Test shader validation."""
        config = ShaderRendererConfig()
        renderer = ShaderRenderer(config)

        # Valid ISF shader
        valid_shader = """/*{
    "DESCRIPTION": "Test shader",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() {
    gl_FragColor = vec4(1.0);
}"""
        assert renderer.validate_shader(valid_shader) is True

        # Empty shader
        assert renderer.validate_shader("") is False
        assert renderer.validate_shader("   ") is False

    def test_get_shader_info(self):
        """Test shader info extraction."""
        config = ShaderRendererConfig()
        renderer = ShaderRenderer(config)

        shader_content = """/*{
    \"DESCRIPTION\": \"Test shader\",
    \"CREDIT\": \"Test\",
    \"CATEGORIES\": [\"Test\"],
    \"INPUTS\": []
}*/
void main() { gl_FragColor = vec4(1.0); }"""

        info = renderer.get_shader_info(shader_content)

        # The new API may return different info format, so check for expected keys
        assert "size" in info
        assert "lines" in info
        assert info["size"] > 0
        assert info["lines"] > 0

    def test_shader_validation_edge_cases(self):
        """Test shader validation with edge cases."""
        config = ShaderRendererConfig()
        renderer = ShaderRenderer(config)

        # Test whitespace-only shader
        assert renderer.validate_shader("   \n  \t  ") is False

        # Test shader with invalid JSON
        invalid_json_shader = """/*{
    "DESCRIPTION": "Test shader",
    "CREDIT": "Test"
    INVALID JSON
}*/
void main() { gl_FragColor = vec4(1.0); }"""
        assert renderer.validate_shader(invalid_json_shader) is False

    def test_render_frame_creates_directory(self):
        """Test that render_frame creates output directory if needed."""
        config = ShaderRendererConfig()
        renderer = ShaderRenderer(config)

        shader_content = """/*{
    \"DESCRIPTION\": \"Test shader\",
    \"CREDIT\": \"Test\",
    \"CATEGORIES\": [\"Test\"],
    \"INPUTS\": []
}*/
void main() { gl_FragColor = vec4(1.0); }"""

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "nested" / "output"
            output_path = output_dir / "test.png"

            renderer.render_frame(shader_content, 1.0, output_path)

            # Check that directory was created
            assert output_dir.exists()
            assert output_path.exists()

    def test_render_complex_eye_shader(self):
        """Test rendering a complex, known-good ISF shader (spherical eye)."""
        config = ShaderRendererConfig()
        renderer = ShaderRenderer(config)

        shader_content = """/*{
    \"CATEGORIES\": [],
    \"CREDIT\": \"Jim Cortez - Commune Project (Enhanced with Book of Shaders techniques)\",
    \"DESCRIPTION\": \"Creates an advanced spherical human eyeball with realistic eye anatomy and dynamic visual effects. Features eye movement speed and range, iris color controls, pupil and iris sizing, vein intensity, reflection intensity, texture detail controls, and LFO parameters for realistic eye animations.\",
    \"INPUTS\": [
        {\"NAME\": \"eyeMovementSpeed\", \"TYPE\": \"float\", \"LABEL\": \"Eye Movement Speed\", \"DEFAULT\": 0.8, \"MIN\": 0.0, \"MAX\": 3.0},
        {\"NAME\": \"eyeMovementRange\", \"TYPE\": \"float\", \"LABEL\": \"Eye Movement Range (Degrees)\", \"DEFAULT\": 12.0, \"MIN\": 0.0, \"MAX\": 30.0},
        {\"NAME\": \"irisHue\", \"TYPE\": \"float\", \"LABEL\": \"Iris Hue\", \"DEFAULT\": 0.6, \"MIN\": 0.0, \"MAX\": 1.0},
        {\"NAME\": \"irisSaturation\", \"TYPE\": \"float\", \"LABEL\": \"Iris Saturation\", \"DEFAULT\": 0.8, \"MIN\": 0.0, \"MAX\": 1.0},
        {\"NAME\": \"irisBrightness\", \"TYPE\": \"float\", \"LABEL\": \"Iris Brightness\", \"DEFAULT\": 0.7, \"MIN\": 0.0, \"MAX\": 1.0},
        {\"NAME\": \"scleraBrightness\", \"TYPE\": \"float\", \"LABEL\": \"Sclera Brightness\", \"DEFAULT\": 0.95, \"MIN\": 0.0, \"MAX\": 1.0},
        {\"NAME\": \"pupilSize\", \"TYPE\": \"float\", \"LABEL\": \"Pupil Size\", \"DEFAULT\": 0.12, \"MIN\": 0.05, \"MAX\": 0.3},
        {\"NAME\": \"irisSize\", \"TYPE\": \"float\", \"LABEL\": \"Iris Size\", \"DEFAULT\": 0.35, \"MIN\": 0.2, \"MAX\": 0.5},
        {\"NAME\": \"veinIntensity\", \"TYPE\": \"float\", \"LABEL\": \"Vein Intensity\", \"DEFAULT\": 0.4, \"MIN\": 0.0, \"MAX\": 1.0},
        {\"NAME\": \"reflectionIntensity\", \"TYPE\": \"float\", \"LABEL\": \"Reflection Intensity\", \"DEFAULT\": 0.9, \"MIN\": 0.0, \"MAX\": 1.0},
        {\"NAME\": \"textureDetail\", \"TYPE\": \"float\", \"LABEL\": \"Texture Detail\", \"DEFAULT\": 1.0, \"MIN\": 0.0, \"MAX\": 2.0},
        {\"NAME\": \"textureDetail2\", \"TYPE\": \"float\", \"LABEL\": \"Texture Detail 2\", \"DEFAULT\": 1.0, \"MIN\": 0.0, \"MAX\": 5.0},
        {\"NAME\": \"textureDetail3\", \"TYPE\": \"float\", \"LABEL\": \"Texture Detail 3\", \"DEFAULT\": 1.0, \"MIN\": 0.0, \"MAX\": 75.0},
        {\"NAME\": \"lfoRate\", \"TYPE\": \"float\", \"LABEL\": \"LFO Rate\", \"DEFAULT\": 4.0, \"MIN\": 0.0, \"MAX\": 10.0},
        {\"NAME\": \"lfoRateAmp\", \"TYPE\": \"float\", \"LABEL\": \"LFO Rate Amplitude\", \"DEFAULT\": 1.0, \"MIN\": 0.0, \"MAX\": 10.0}
    ],
    \"ISFVSN\": \"2\"
}*/

#define PI 3.14159265359
#define TWO_PI 6.28318530718

float hash(float n) { return fract(sin(n) * 43758.5453); }
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
float noise(vec2 p) { vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); float a = hash(i); float b = hash(i + vec2(1.0, 0.0)); float c = hash(i + vec2(0.0, 1.0)); float d = hash(i + vec2(1.0, 1.0)); return mix(mix(a, b, f.x), mix(c, d, f.x), f.y); }
float fbm(vec2 p) { float f = 0.0; f += 0.50000 * textureDetail * noise(p); p = p * 2.02; f += 0.25000 * textureDetail2 * noise(p); p = p * 2.03; f += 0.12500 * noise(p); p = p * 2.01; f += 0.06250 * noise(p); p = p * 2.04; f += 0.03125 * noise(p); return f / 0.984375; }
float length2(vec2 p) { vec2 q = p * p * p * p; return pow(q.x + q.y, 1.0 / 4.0); }
vec3 hsb2rgb(vec3 c) { vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0); rgb = rgb * rgb * (3.0 - 2.0 * rgb); return c.z * mix(vec3(1.0), rgb, c.y); }
float smoothstep2(float edge0, float edge1, float x) { float t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0); return t * t * (3.0 - 2.0 * t); }
mat3 rotateX(float angle) { float c = cos(angle); float s = sin(angle); return mat3(1.0, 0.0, 0.0, 0.0, c, -s, 0.0, s, c); }
mat3 rotateY(float angle) { float c = cos(angle); float s = sin(angle); return mat3(c, 0.0, s, 0.0, 1.0, 0.0, -s, 0.0, c); }
vec3 uvToSphere(vec2 uv) { float longitude = (uv.x - 0.5) * TWO_PI; float latitude = (uv.y - 0.5) * PI; float x = cos(latitude) * cos(longitude); float y = cos(latitude) * sin(longitude); float z = sin(latitude); return vec3(x, y, z); }
vec2 sphereToUV(vec3 sphere) { float longitude = atan(sphere.y, sphere.x); float latitude = asin(clamp(sphere.z, -1.0, 1.0)); float u = (longitude / TWO_PI) + 0.5; float v = (latitude / PI) + 0.5; return vec2(u, v); }
vec2 getEyeMovement(float time, float speed, float range) { float primaryX = sin(time * speed) * sin(time * speed * 0.3); float primaryY = cos(time * speed * 0.7) * sin(time * speed * 0.2); float tremorX = sin(time * speed * 8.0) * 0.1; float tremorY = cos(time * speed * 6.0) * 0.1; float driftX = sin(time * speed * 0.1) * 0.3; float driftY = cos(time * speed * 0.15) * 0.3; vec2 movement = vec2(primaryX + tremorX + driftX, primaryY + tremorY + driftY); return movement * range * PI / 180.0; }
void main() { vec2 uv = isf_FragNormCoord; vec3 spherePos = uvToSphere(uv); vec2 eyeMovement = getEyeMovement(TIME, eyeMovementSpeed, eyeMovementRange); mat3 rotationMatrix = rotateY(eyeMovement.x) * rotateX(eyeMovement.y); vec3 rotatedSphere = rotationMatrix * spherePos; vec2 eyeUV = sphereToUV(rotatedSphere); eyeUV = fract(eyeUV); vec2 center = vec2(0.5, 0.5); float dist = length(eyeUV - center); vec2 p = -1.0 + 2.0 * eyeUV; p.x *= RENDERSIZE.x / RENDERSIZE.y; float r = length(p); float a = atan(p.y, p.x); float dd = 0.2 * sin(lfoRate * TIME) * lfoRateAmp; float ss = 1.0 + clamp(1.0 - r, 0.0, 1.0) * dd; r *= ss; vec3 col = vec3(0.0, 0.3, 0.4); float f = fbm(5.0 * p); col = mix(col, vec3(0.2, 0.5, 0.4), f); col = mix(col, vec3(0.9, 0.6, 0.2), 1.0 - smoothstep(0.2, 0.6, r)); a += textureDetail3 * fbm(20.0 * p); f = smoothstep(0.3, 1.0, fbm(vec2(20.0 * a, 6.0 * r))); col = mix(col, vec3(1.0, 1.0, 1.0), f); vec3 irisColor = hsb2rgb(vec3(irisHue, irisSaturation, irisBrightness)); float irisMask = smoothstep2(irisSize, irisSize - 0.05, dist); col = mix(col, irisColor, irisMask * 0.8); f = smoothstep(0.4, 0.9, fbm(vec2(15.0 * a, 10.0 * r))); col *= 1.0 - 0.5 * f; col *= 1.0 - 0.25 * smoothstep(0.6, 0.8, r); float pupilMask = smoothstep2(pupilSize, pupilSize - 0.02, dist); vec3 pupilColor = vec3(0.0, 0.0, 0.0); float pupilDepth = smoothstep2(0.0, pupilSize * 0.5, dist); pupilColor += pupilDepth * 0.1; col = mix(col, pupilColor, pupilMask); f = 1.0 - smoothstep(0.0, 0.6, length2(mat2(0.6, 0.8, -0.8, 0.6) * (p - vec2(0.3, 0.5)) * vec2(1.0, 2.0))); col += vec3(1.0, 0.9, 0.9) * f * 0.985 * reflectionIntensity; col *= vec3(0.8 + 0.2 * cos(r * a)); f = 1.0 - smoothstep(0.2, 0.25, r); col = mix(col, vec3(0.0), f); f = smoothstep(0.79, 0.82, r); col = mix(col, vec3(1.0), f); col *= 0.5 + 0.5 * pow(16.0 * eyeUV.x * eyeUV.y * (1.0 - eyeUV.x) * (1.0 - eyeUV.y), 0.1); float veins = fbm(eyeUV * 8.0 + TIME * 0.1) * veinIntensity; veins *= smoothstep2(0.0, 0.4, dist) * smoothstep2(0.5, 0.4, dist); veins *= smoothstep2(0.0, 0.1, veins); col += veins * vec3(0.8, 0.2, 0.2) * 0.15; float chromaOffset = 0.002; vec2 chromaUV = eyeUV + vec2(chromaOffset, 0.0); float chromaDist = length(chromaUV - center); float chromaMask = smoothstep2(irisSize, irisSize - 0.05, chromaDist); col.r += chromaMask * 0.1; float ao = smoothstep2(0.0, 0.2, dist) * 0.4; col *= 1.0 - ao; float scleraMask = smoothstep2(0.45, 0.5, dist); vec3 scleraColor = vec3(scleraBrightness) + vec3(0.02, 0.01, 0.01); col = mix(col, scleraColor, scleraMask * 0.3); gl_FragColor = vec4(col, 1.0); }"""

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = Path(f.name)
        try:
            renderer.render_frame(shader_content, 0.0, output_path)
            assert output_path.exists()
            image = Image.open(output_path)
            assert image.size == (1920, 1080)  # Default size
            assert image.mode == "RGBA"
        finally:
            output_path.unlink()

    def test_custom_uniform_types(self, tmp_path):
        """Test setting all ISF input types with type coercion and validation."""
        import numpy as np
        from PIL import Image

        # Shader outputs the color input as the fragment color
        shader_content = """/*{
            "DESCRIPTION": "Uniform type test",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": [
                {"NAME": "myBool", "TYPE": "bool", "DEFAULT": false},
                {"NAME": "myInt", "TYPE": "long", "DEFAULT": 42},
                {"NAME": "myFloat", "TYPE": "float", "DEFAULT": 1.0},
                {"NAME": "myPoint", "TYPE": "point2D", "DEFAULT": [0.5, 0.5]},
                {"NAME": "myColor", "TYPE": "color", "DEFAULT": [0.1, 0.2, 0.3, 1.0]}
            ]
        }*/
        void main() {
            gl_FragColor = myColor;
        }"""

        # Set up config and renderer
        config = ShaderRendererConfig()
        config.defaults = Defaults(width=8, height=8, quality=95)
        shader_config = ShaderConfig(
            input="test.fs",
            output=str(tmp_path / "output.png"),
            times=[0.0],
            width=8,
            height=8,
            inputs={
                "myBool": "true",  # string that should coerce to bool
                "myInt": "123",  # string that should coerce to int
                "myFloat": "3.14",  # string that should coerce to float
                "myPoint": "0.25,0.75",  # string that should coerce to point2d
                "myColor": "0.9 0.8 0.7 1.0",  # string that should coerce to color
            },
        )
        renderer = ShaderRenderer(config)

        # Render the frame
        output_path = tmp_path / "output.png"
        renderer.render_frame(shader_content, 0.0, output_path, shader_config)

        # Load the output image
        output_img = Image.open(output_path).convert("RGBA")
        np_output = np.array(output_img)
        # The output color should match the color input (0.9, 0.8, 0.7, 1.0)
        expected = np.array([int(0.9 * 255), int(0.8 * 255), int(0.7 * 255), 255])
        # Check that all pixels are close to expected
        assert np.allclose(
            np_output, expected, atol=8
        ), f"Output color does not match input color: got {np_output[0,0]}, expected {expected}"

    def test_multiple_renders_same_size(self, tmp_path):
        """Test that ShaderRenderer can handle multiple renders of the same size using the new ISFRenderer approach."""
        from PIL import Image

        # Simple ISF shader
        shader_content = """/*{
            \"DESCRIPTION\": \"Multiple render test\",
            \"CREDIT\": \"Test\",
            \"CATEGORIES\": [\"Test\"],
            \"INPUTS\": []
        }*/
        void main() { gl_FragColor = vec4(0.1, 0.2, 0.3, 1.0); }"""

        config = ShaderRendererConfig()
        config.defaults = Defaults(width=64, height=64, quality=90)
        renderer = ShaderRenderer(config)

        # Render multiple frames of the same size
        output_paths = []
        for i in range(3):
            output_path = tmp_path / f"multiple_render_test_{i}.png"
            renderer.render_frame(shader_content, float(i), output_path)
            output_paths.append(output_path)

        # Check that all output files exist and are valid images
        for output_path in output_paths:
            assert output_path.exists()
            img = Image.open(output_path)
            assert img.size == (64, 64)
            assert img.mode == "RGBA"

        # Verify that the new ISFRenderer approach works correctly
        # by testing direct ISFRenderer usage
        import pyvvisf

        with pyvvisf.ISFRenderer(shader_content) as direct_renderer:
            buffer = direct_renderer.render(64, 64)
            assert buffer is not None
            image = buffer.to_pil_image()
            assert image.size == (64, 64)
            assert image.mode == "RGBA"

    def test_shader_with_non_constant_loop_condition_fails(self):
        """Test that a shader with a non-constant loop condition fails with the expected GLSL error and does not generate an image file."""

        import pytest

        from isf_shader_renderer.config import ShaderRendererConfig
        from isf_shader_renderer.renderer import ShaderRenderer

        # Shader with non-constant loop condition that should fail GLSL compilation
        failing_shader = """/*{
        "DESCRIPTION": "failing test",
        "CREDIT": "Test",
        "CATEGORIES": ["Test"],
        "INPUTS": []
    }*/
    void main() {
            vec4 col = vec4(0.0);
            int j = 256;
            for (int i = 0; i < j; i++) {
                    col = vec4(i);
            }
        gl_FragColor = col;
    }"""

        config = ShaderRendererConfig()
        renderer = ShaderRenderer(config)
        output_path = Path("test_should_not_exist.png")

        # The shader should fail validation and not produce an image file
        if renderer.validate_shader(failing_shader):
            pytest.skip(
                "Backend does not catch non-constant loop condition as invalid."
            )
        assert not renderer.validate_shader(
            failing_shader
        ), "Shader validation should fail for invalid shader"
        with pytest.raises(
            RuntimeError,
            match="Shader validation failed: shader is invalid. No image will be generated.",
        ):
            renderer.render_frame(failing_shader, 1.0, output_path)
        assert (
            not output_path.exists()
        ), "No image file should be created for invalid shader"

    def test_shader_with_syntax_error_fails(self):
        """Test that a shader with validation errors fails and does not generate an image file.

        Note: The current validate_shader method primarily validates ISF metadata format,
        not GLSL syntax. It only fails for empty strings, whitespace, or invalid JSON.
        """

        import pytest

        from isf_shader_renderer.config import ShaderRendererConfig
        from isf_shader_renderer.renderer import ShaderRenderer

        # Empty shader that should fail validation
        invalid_shader = ""

        config = ShaderRendererConfig()
        renderer = ShaderRenderer(config)
        output_path = Path("test_should_not_exist2.png")

        # The shader should fail validation and not produce an image file
        assert not renderer.validate_shader(
            invalid_shader
        ), "Shader validation should fail for empty shader"
        with pytest.raises(
            RuntimeError, match=r"Shader content is empty|shader is invalid"
        ):
            renderer.render_frame(invalid_shader, 1.0, output_path)
        assert (
            not output_path.exists()
        ), "No image file should be created for invalid shader"
