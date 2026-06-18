"""Configuration management for ISF Shader Renderer (ShaderRendererConfig)."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from jsonschema import validate


@dataclass
class Defaults:
    """Default configuration settings."""

    width: int = 1920
    height: int = 1080
    quality: int = 95
    output_format: str = "png"


@dataclass
class ShaderConfig:
    """Configuration for a single shader."""

    input: str
    output: str
    times: List[float]
    width: Optional[int] = None
    height: Optional[int] = None
    quality: Optional[int] = None
    inputs: Optional[Dict[str, Any]] = None

    def get_width(self, defaults: Defaults) -> int:
        return self.width if self.width is not None else defaults.width

    def get_height(self, defaults: Defaults) -> int:
        return self.height if self.height is not None else defaults.height

    def get_quality(self, defaults: Defaults) -> int:
        return self.quality if self.quality is not None else defaults.quality


@dataclass
class ShaderRendererConfig:
    """Main configuration class for the ISF Shader Renderer."""

    defaults: Defaults = field(default_factory=Defaults)
    shaders: List[ShaderConfig] = field(default_factory=list)


CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "defaults": {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "minimum": 1},
                "height": {"type": "integer", "minimum": 1},
                "quality": {"type": "integer", "minimum": 1, "maximum": 100},
                "output_format": {"type": "string", "enum": ["png", "jpg", "jpeg"]},
            },
            "additionalProperties": False,
        },
        "shaders": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["input", "output", "times"],
                "properties": {
                    "input": {"type": "string"},
                    "output": {"type": "string"},
                    "times": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 1,
                    },
                    "width": {"type": "integer", "minimum": 1},
                    "height": {"type": "integer", "minimum": 1},
                    "quality": {"type": "integer", "minimum": 1, "maximum": 100},
                    "inputs": {"type": "object"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


def load_config(config_path: Path) -> ShaderRendererConfig:
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    # yaml.safe_load returns None for an empty file; treat that as an empty config.
    if data is None:
        data = {}
    try:
        validate(instance=data, schema=CONFIG_SCHEMA)
    except Exception as e:
        raise ValueError(f"Invalid configuration format: {e}")
    config = ShaderRendererConfig()
    if "defaults" in data:
        defaults_data = data["defaults"]
        config.defaults = Defaults(
            width=defaults_data.get("width", 1920),
            height=defaults_data.get("height", 1080),
            quality=defaults_data.get("quality", 95),
            output_format=defaults_data.get("output_format", "png"),
        )
    if "shaders" in data:
        for shader_data in data["shaders"]:
            shader_config = ShaderConfig(
                input=shader_data["input"],
                output=shader_data["output"],
                times=shader_data["times"],
                width=shader_data.get("width"),
                height=shader_data.get("height"),
                quality=shader_data.get("quality"),
                inputs=shader_data.get("inputs"),
            )
            config.shaders.append(shader_config)
    return config


def save_config(config: ShaderRendererConfig, config_path: Path) -> None:
    data = {
        "defaults": {
            "width": config.defaults.width,
            "height": config.defaults.height,
            "quality": config.defaults.quality,
            "output_format": config.defaults.output_format,
        },
        "shaders": [
            {
                "input": shader.input,
                "output": shader.output,
                "times": shader.times,
                **({"width": shader.width} if shader.width is not None else {}),
                **({"height": shader.height} if shader.height is not None else {}),
                **({"quality": shader.quality} if shader.quality is not None else {}),
                **({"inputs": shader.inputs} if shader.inputs is not None else {}),
            }
            for shader in config.shaders
        ],
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, indent=2)


def create_default_config(config_path: Path) -> None:
    config = ShaderRendererConfig()
    example_shader = ShaderConfig(
        input="shaders/example.fs",
        output="output/example_%04d.png",
        times=[0.0, 0.5, 1.0, 1.5, 2.0],
        width=1280,
        height=720,
    )
    config.shaders.append(example_shader)
    save_config(config, config_path)
