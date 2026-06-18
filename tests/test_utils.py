"""Tests for utility functions."""

import pytest

from isf_shader_renderer.utils import (
    calculate_frame_count,
    extract_shader_metadata,
    format_output_path,
    generate_time_codes,
    get_file_extension,
    parse_time_range,
    sanitize_filename,
    validate_output_path,
)


class TestParseTimeRange:
    """Test time range parsing."""

    def test_parse_comma_separated(self):
        """Test parsing comma-separated time values."""
        result = parse_time_range("0,1,2,3")
        assert result == [0.0, 1.0, 2.0, 3.0]

    def test_parse_range_with_step(self):
        """Test parsing range with step."""
        result = parse_time_range("0:3:0.5")
        assert result == [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    def test_parse_range_with_dash(self):
        """Test parsing range with dash separator."""
        result = parse_time_range("0-3:0.5")
        assert result == [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    def test_parse_single_value(self):
        """Test parsing single time value."""
        result = parse_time_range("1.5")
        assert result == [1.5]

    def test_parse_invalid_format(self):
        """Test parsing invalid time range format."""
        with pytest.raises(ValueError, match="Invalid time range format"):
            parse_time_range("invalid")


class TestFormatOutputPath:
    """Test output path formatting."""

    def test_format_with_frame_number(self):
        """Test formatting with frame number."""
        result = format_output_path("output_%04d.png", 5, 1.5)
        assert result == "output_0005.png"

    def test_format_with_time_code(self):
        """Test formatting with time code."""
        result = format_output_path("output_%f.png", 0, 1.5)
        assert result == "output_1.500.png"

    def test_format_with_precision(self):
        """Test formatting with precision specifier."""
        result = format_output_path("output_%.3f.png", 0, 1.56789)
        assert result == "output_1.568.png"


class TestValidateOutputPath:
    """Test output path validation."""

    def test_validate_existing_directory(self, tmp_path):
        """Test validation with existing directory."""
        output_path = tmp_path / "test.png"
        assert validate_output_path(output_path) is True

    def test_validate_nonexistent_directory(self, tmp_path):
        """Test validation with non-existent directory."""
        output_path = tmp_path / "nested" / "test.png"
        assert validate_output_path(output_path) is True  # Should create directory


class TestExtractShaderMetadata:
    """Test shader metadata extraction."""

    def test_extract_basic_metadata(self):
        """Test extracting basic metadata."""
        shader_content = """
        /* name: Test Shader */
        /* description: A test shader */
        /* author: Test Author */
        /* version: 1.0 */
        void main() { gl_FragColor = vec4(1.0); }
        """

        metadata = extract_shader_metadata(shader_content)

        assert metadata["name"] == "Test Shader"
        assert metadata["description"] == "A test shader"
        assert metadata["author"] == "Test Author"
        assert metadata["version"] == "1.0"

    def test_extract_no_metadata(self):
        """Test extracting metadata from shader without metadata."""
        shader_content = "void main() { gl_FragColor = vec4(1.0); }"

        metadata = extract_shader_metadata(shader_content)

        assert metadata["name"] is None
        assert metadata["description"] is None
        assert metadata["author"] is None
        assert metadata["version"] is None


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_sanitize_valid_filename(self):
        """Test sanitizing valid filename."""
        result = sanitize_filename("test.png")
        assert result == "test.png"

    def test_sanitize_invalid_chars(self):
        """Test sanitizing filename with invalid characters."""
        result = sanitize_filename('test<>:"/\\|?*.png')
        assert result == "test_________.png"

    def test_sanitize_leading_trailing_spaces(self):
        """Test sanitizing filename with leading/trailing spaces."""
        result = sanitize_filename("  test.png  ")
        assert result == "test.png"

    def test_sanitize_empty_filename(self):
        """Test sanitizing empty filename."""
        result = sanitize_filename("")
        assert result == "unnamed"


class TestGetFileExtension:
    """Test file extension mapping."""

    def test_get_png_extension(self):
        """Test getting PNG extension."""
        assert get_file_extension("png") == ".png"

    def test_get_jpg_extension(self):
        """Test getting JPG extension."""
        assert get_file_extension("jpg") == ".jpg"
        assert get_file_extension("jpeg") == ".jpg"

    def test_get_unknown_extension(self):
        """Test getting unknown format extension."""
        assert get_file_extension("unknown") == ".png"  # Default


class TestFrameCalculations:
    """Test frame calculation functions."""

    def test_calculate_frame_count(self):
        """Test frame count calculation."""
        count = calculate_frame_count(0.0, 2.0, 30.0)
        assert count == 61  # 0.0 to 2.0 at 30fps = 61 frames

    def test_generate_time_codes(self):
        """Test time code generation."""
        time_codes = generate_time_codes(0.0, 1.0, 4.0)  # 4fps
        expected = [0.0, 0.25, 0.5, 0.75, 1.0]
        assert time_codes == expected
