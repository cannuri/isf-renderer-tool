"""Typed exceptions for ISF shader operations.

These carry a stable ``error_code`` and structured ``details`` so callers
(the CLI and the MCP server) can present machine-actionable diagnostics
instead of parsing free-form strings. They subclass ``RuntimeError`` so that
existing ``except RuntimeError`` / ``pytest.raises(RuntimeError)`` call sites
keep working.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, Optional


class ISFShaderError(RuntimeError):
    """Base exception for ISF shader errors."""

    default_code = "ISF_ERROR"

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.error_code = error_code or self.default_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation of the error."""
        return {
            "type": type(self).__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }

    @classmethod
    def from_exception(
        cls, exc: BaseException, message: Optional[str] = None
    ) -> "ISFShaderError":
        """Wrap an arbitrary exception, preserving its message and traceback."""
        if isinstance(exc, ISFShaderError):
            return exc
        details: Dict[str, Any] = {
            "original_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        }
        for attr in ("error_code", "details"):
            if hasattr(exc, attr):
                details[attr] = getattr(exc, attr)
        return cls(message or str(exc), details=details)


class ShaderValidationError(ISFShaderError):
    """The shader is structurally invalid (bad ISF metadata, missing main, etc.)."""

    default_code = "SHADER_VALIDATION_ERROR"


class RenderingError(ISFShaderError):
    """The shader failed to render (GLSL compile error, backend failure, etc.)."""

    default_code = "RENDERING_ERROR"
