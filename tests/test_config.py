"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest
import yaml

from isf_shader_renderer.config import (
    Defaults,
    ShaderConfig,
    ShaderRendererConfig,
    create_default_config,
    load_config,
    save_config,
)


class TestDefaults:
    """Test Defaults dataclass."""

    def test_defaults_creation(self):
        """Test creating Defaults with default values."""
        defaults = Defaults()
        assert defaults.width == 1920
        assert defaults.height == 1080
        assert defaults.quality == 95
        assert defaults.output_format == "png"

    def test_defaults_custom_values(self):
        """Test creating Defaults with custom values."""
        defaults = Defaults(width=1280, height=720, quality=90)
        assert defaults.width == 1280
        assert defaults.height == 720
        assert defaults.quality == 90
        assert defaults.output_format == "png"


class TestShaderConfig:
    """Test ShaderConfig dataclass."""

    def test_shader_config_creation(self):
        """Test creating ShaderConfig."""
        config = ShaderConfig(
            input="test.fs",
            output="output.png",
            times=[0.0, 1.0, 2.0],
        )
        assert config.input == "test.fs"
        assert config.output == "output.png"
        assert config.times == [0.0, 1.0, 2.0]
        assert config.width is None
        assert config.height is None
        assert config.quality is None

    def test_shader_config_get_methods(self):
        """Test ShaderConfig get methods with defaults."""
        config = ShaderConfig(
            input="test.fs",
            output="output.png",
            times=[0.0],
            width=1280,
            height=720,
            quality=90,
        )
        defaults = Defaults()

        assert config.get_width(defaults) == 1280
        assert config.get_height(defaults) == 720
        assert config.get_quality(defaults) == 90

    def test_shader_config_get_methods_with_none(self):
        """Test ShaderConfig get methods when values are None."""
        config = ShaderConfig(
            input="test.fs",
            output="output.png",
            times=[0.0],
        )
        defaults = Defaults()

        assert config.get_width(defaults) == 1920
        assert config.get_height(defaults) == 1080
        assert config.get_quality(defaults) == 95


class TestShaderRendererConfig:
    """Test ShaderRendererConfig dataclass."""

    def test_config_creation(self):
        """Test creating ShaderRendererConfig with defaults."""
        config = ShaderRendererConfig()
        assert config.defaults.width == 1920
        assert config.defaults.height == 1080
        assert config.defaults.quality == 95
        assert config.shaders == []

    def test_config_with_shaders(self):
        """Test creating ShaderRendererConfig with shaders."""
        shader_config = ShaderConfig(
            input="test.fs",
            output="output.png",
            times=[0.0, 1.0, 2.0],
        )
        config = ShaderRendererConfig(shaders=[shader_config])
        assert len(config.shaders) == 1
        assert config.shaders[0].input == "test.fs"


class TestConfigFileOperations:
    """Test configuration file operations."""

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        config = ShaderRendererConfig()
        shader_config = ShaderConfig(
            input="test.fs",
            output="output.png",
            times=[0.0, 1.0, 2.0],
            width=1280,
            height=720,
        )
        config.shaders.append(shader_config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_path = Path(f.name)

        try:
            save_config(config, config_path)
            loaded_config = load_config(config_path)

            assert loaded_config.defaults.width == config.defaults.width
            assert loaded_config.defaults.height == config.defaults.height
            assert len(loaded_config.shaders) == 1
            assert loaded_config.shaders[0].input == "test.fs"
            assert loaded_config.shaders[0].times == [0.0, 1.0, 2.0]
        finally:
            config_path.unlink()

    def test_load_config_file_not_found(self):
        """Test loading non-existent configuration file."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("nonexistent.yaml"))

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)

        try:
            with pytest.raises(Exception):
                load_config(config_path)
        finally:
            config_path.unlink()

    def test_load_invalid_config_schema(self):
        """Test loading configuration with invalid schema."""
        invalid_config = {
            "defaults": {
                "width": "invalid",  # Should be integer
            },
            "shaders": [
                {
                    "input": "test.fs",
                    "output": "output.png",
                    "times": [0.0, 1.0],
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(invalid_config, f)
            config_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid configuration format"):
                load_config(config_path)
        finally:
            config_path.unlink()

    def test_create_default_config(self):
        """Test creating default configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_path = Path(f.name)

        try:
            create_default_config(config_path)
            loaded_config = load_config(config_path)

            assert len(loaded_config.shaders) == 1
            assert loaded_config.shaders[0].input == "shaders/example.fs"
            assert loaded_config.shaders[0].output == "output/example_%04d.png"
            assert loaded_config.shaders[0].times == [0.0, 0.5, 1.0, 1.5, 2.0]
        finally:
            config_path.unlink()
