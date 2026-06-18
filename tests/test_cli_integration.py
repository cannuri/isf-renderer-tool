import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import numpy as np
from PIL import Image


def test_cli_render_minimal_shader():
    # Write a minimal valid ISF shader to a temp file
    shader_code = """/*{
    "DESCRIPTION": "Minimal test shader",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() { gl_FragColor = vec4(0.2, 0.4, 0.6, 1.0); }"""
    with tempfile.NamedTemporaryFile(
        suffix=".fs", delete=False, mode="w"
    ) as shader_file:
        shader_file.write(shader_code)
        shader_path = Path(shader_file.name)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as output_file:
        output_path = Path(output_file.name)

    try:
        # Run the CLI as a subprocess
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "isf_shader_renderer.cli",
                    str(shader_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            raise

        # Check that the output file was created
        assert output_path.exists(), f"Output file {output_path} was not created"

        # Check that it's a valid image
        image = Image.open(output_path)
        assert image.size[0] > 0 and image.size[1] > 0
        assert image.mode in ("RGBA", "RGB")

        # Optionally, check CLI output for success
        assert "Successfully rendered" in result.stdout or result.returncode == 0
    finally:
        shader_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)


def test_cli_render_all_input_types():
    """Test rendering a shader with all ISF input types via CLI, including image input."""
    # Write a shader with all input types
    shader_code = """/*{
    "DESCRIPTION": "All input types test shader",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": [
        {"NAME": "myBool", "TYPE": "bool", "DEFAULT": false},
        {"NAME": "myInt", "TYPE": "long", "DEFAULT": 42},
        {"NAME": "myFloat", "TYPE": "float", "DEFAULT": 1.0},
        {"NAME": "myPoint", "TYPE": "point2D", "DEFAULT": [0.5, 0.5]},
        {"NAME": "myColor", "TYPE": "color", "DEFAULT": [0.1, 0.2, 0.3, 1.0]},
        {"NAME": "inputImage", "TYPE": "image"}
    ]
}*/
void main() { gl_FragColor = myColor; }"""
    with tempfile.NamedTemporaryFile(
        suffix=".fs", delete=False, mode="w"
    ) as shader_file:
        shader_file.write(shader_code)
        shader_path = Path(shader_file.name)

    # Create a test input image (blue square)
    input_img = Image.new("RGBA", (16, 16), (0, 0, 255, 255))
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
        input_img.save(img_file.name)
        input_img_path = Path(img_file.name)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as output_file:
        output_path = Path(output_file.name)

    try:
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "isf_shader_renderer.cli",
                    str(shader_path),
                    "--output",
                    str(output_path),
                    "--inputs",
                    f"myBool=true,myInt=123,myFloat=3.14,myPoint=0.25 0.75,myColor=0.9 0.8 0.7 1.0,inputImage={input_img_path}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            raise
        assert output_path.exists(), f"Output file {output_path} was not created"
        image = Image.open(output_path)
        assert image.size[0] > 0 and image.size[1] > 0
        assert image.mode in ("RGBA", "RGB")
        np_output = np.array(image)
        expected = np.array([int(0.9 * 255), int(0.8 * 255), int(0.7 * 255), 255])
        assert np.allclose(
            np_output[0, 0], expected, atol=8
        ), f"Output color does not match input color: got {np_output[0,0]}, expected {expected}"
    finally:
        shader_path.unlink(missing_ok=True)
        input_img_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)


def test_cli_batch_rendering():
    """Test batch rendering with multiple time codes via CLI."""
    shader_code = """/*{
    "DESCRIPTION": "Batch test shader",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() { gl_FragColor = vec4(TIME/2.0, 0.5, 0.5, 1.0); }"""
    with tempfile.NamedTemporaryFile(
        suffix=".fs", delete=False, mode="w"
    ) as shader_file:
        shader_file.write(shader_code)
        shader_path = Path(shader_file.name)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_pattern = Path(tmpdir) / "batch_%04d.png"
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "isf_shader_renderer.cli",
                    str(shader_path),
                    "--output",
                    str(output_pattern),
                    "--time",
                    "0",
                    "--time",
                    "1",
                    "--time",
                    "2",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            raise
        # Check that all output files were created
        for i in range(3):
            out_path = Path(tmpdir) / f"batch_{i:04d}.png"
            assert out_path.exists(), f"Batch output {out_path} not created"
            image = Image.open(out_path)
            assert image.size[0] > 0 and image.size[1] > 0
            assert image.mode in ("RGBA", "RGB")


def test_cli_error_handling_invalid_shader():
    """Test CLI error handling for invalid shader."""
    # Write an invalid shader (missing main)
    shader_code = '/*{ "DESCRIPTION": "Invalid shader" }*/'
    with tempfile.NamedTemporaryFile(
        suffix=".fs", delete=False, mode="w"
    ) as shader_file:
        shader_file.write(shader_code)
        shader_path = Path(shader_file.name)
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / f"invalid_output_{uuid.uuid4().hex}.png"
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "isf_shader_renderer.cli",
                    str(shader_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            raise
        # Should not create output file, should print error
        if output_path.exists():
            print(
                f"Output file exists: {output_path}, size: {output_path.stat().st_size}"
            )
            print(f"Modification time: {output_path.stat().st_mtime}")
            with open(output_path, "rb") as f:
                print(f"First 64 bytes: {f.read(64)}")
            assert (
                output_path.stat().st_size == 0
            ), "Output file should be empty for invalid shader"
    shader_path.unlink(missing_ok=True)
