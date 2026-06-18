"""MCP server for ISF Shader Renderer using standard MCP Server."""

import asyncio
import base64
import logging
import sys
from typing import List

from mcp import Resource as MCPResource
from mcp import Tool
from mcp.server import Server
from mcp.server.fastmcp import Image as FastMCPImage
from mcp.server.stdio import stdio_server

from .handlers import ISFShaderHandlers


def main():
    """Main function to create and run the MCP server."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ISF Shader Renderer MCP Server")
    parser.add_argument(
        "--stdio", action="store_true", help="Run in stdio mode (default)"
    )
    parser.add_argument("--http", action="store_true", help="Run in HTTP mode")
    parser.add_argument(
        "--port", type=int, default=8000, help="HTTP server port (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="HTTP server host (default: localhost)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Set up logging to stderr
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger("isf-mcp-server")

    # Determine mode
    if args.http:
        # Run HTTP server using official MCP transport
        run_http_server(logger, args.host, args.port)
    else:
        # Run stdio server (default)
        run_stdio_server(logger)


def run_http_server(logger, host: str, port: int):
    """Run the HTTP MCP server using FastMCP with streamable-http transport."""
    print("Creating ISF Shader Renderer MCP HTTP server...", file=sys.stderr)

    # Create FastMCP server
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("isf-shader-renderer")
    handlers = ISFShaderHandlers()

    # Register tools using FastMCP decorators
    @server.tool()
    async def render_shader(
        shader_content: str,
        time_codes: list[float],
        width: int = 1920,
        height: int = 1080,
        quality: int = 95,
        verbose: bool = False,
    ) -> dict:
        """Render an ISF shader to PNG images at specified time codes."""
        logger.info(f"render_shader called with {len(time_codes)} time codes")
        result = await handlers.call_tool(
            "render_shader",
            {
                "shader_content": shader_content,
                "time_codes": time_codes,
                "width": width,
                "height": height,
                "quality": quality,
                "verbose": verbose,
            },
        )
        return result

    @server.tool()
    async def validate_shader(shader_content: str) -> dict:
        """Validate ISF shader syntax and extract metadata."""
        logger.info("validate_shader called")
        result = await handlers.call_tool(
            "validate_shader", {"shader_content": shader_content}
        )
        return result

    @server.tool()
    async def get_shader_info(shader_content: str) -> dict:
        """Extract information from ISF shader."""
        logger.info("get_shader_info called")
        result = await handlers.call_tool(
            "get_shader_info", {"shader_content": shader_content}
        )
        return result

    # Register resources
    @server.resource("isf://examples/simple.fs")
    async def simple_shader() -> str:
        """Simple test shader."""
        return """/*{
    "DESCRIPTION": "Simple test shader",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() {
    gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
}"""

    @server.resource("isf://examples/gradient.fs")
    async def gradient_shader() -> str:
        """Gradient test shader."""
        return """/*{
    "DESCRIPTION": "Gradient test shader",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    gl_FragColor = vec4(uv.x, uv.y, 0.5, 1.0);
}"""

    print("All handlers registered", file=sys.stderr)
    print(f"Starting MCP HTTP server on {host}:{port}...", file=sys.stderr)

    # Run HTTP server using FastMCP streamable-http transport
    try:
        # Set environment variables for FastMCP HTTP server
        import os

        os.environ["MCP_SERVER_PORT"] = str(port)
        os.environ["MCP_SERVER_HOST"] = host

        # Run the server with streamable-http transport
        server.run(transport="streamable-http")
    except Exception as e:
        logger.error(f"Error in HTTP server: {e}", exc_info=True)
        raise


def run_stdio_server(logger):
    """Run the stdio MCP server."""
    print("Creating ISF Shader Renderer MCP server...", file=sys.stderr)

    # Create standard MCP server
    server = Server("isf-shader-renderer")
    handlers = ISFShaderHandlers()

    # Define tools
    render_shader_tool = Tool(
        name="render_shader",
        description="Render an ISF shader to JPEG images at specified time codes",
        inputSchema={
            "type": "object",
            "properties": {
                "shader_content": {
                    "type": "string",
                    "description": "ISF shader source code",
                },
                "time_codes": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Time codes for rendering (seconds)",
                },
                "width": {
                    "type": "integer",
                    "default": 1920,
                    "description": "Output width in pixels",
                },
                "height": {
                    "type": "integer",
                    "default": 1080,
                    "description": "Output height in pixels",
                },
                "quality": {
                    "type": "integer",
                    "default": 95,
                    "minimum": 1,
                    "maximum": 100,
                    "description": "JPEG quality (1-100)",
                },
                "verbose": {
                    "type": "boolean",
                    "default": False,
                    "description": "Enable verbose output",
                },
            },
            "required": ["shader_content", "time_codes"],
        },
    )

    validate_shader_tool = Tool(
        name="validate_shader",
        description="Validate ISF shader syntax and extract metadata",
        inputSchema={
            "type": "object",
            "properties": {
                "shader_content": {
                    "type": "string",
                    "description": "ISF shader source code to validate",
                }
            },
            "required": ["shader_content"],
        },
    )

    get_shader_info_tool = Tool(
        name="get_shader_info",
        description="Extract information from ISF shader",
        inputSchema={
            "type": "object",
            "properties": {
                "shader_content": {
                    "type": "string",
                    "description": "ISF shader source code",
                }
            },
            "required": ["shader_content"],
        },
    )

    # Register handlers
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        logger.info("list_tools called")
        return [render_shader_tool, validate_shader_tool, get_shader_info_tool]

    @server.list_resources()
    async def list_resources() -> List[MCPResource]:
        logger.info("list_resources called")
        resources = await handlers.list_resources()
        # Convert our Resource models into MCP Resource objects.
        return [MCPResource(**r.model_dump()) for r in resources]

    @server.read_resource()
    async def read_resource(uri) -> bytes:
        logger.info(f"read_resource called with uri: {uri}")
        return await handlers.read_resource(str(uri))

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> dict:
        logger.info(f"call_tool called with name: {name}")
        result = await handlers.call_tool(name, arguments)

        # For render_shader, return the rendered frames as fastmcp.Image content
        # blocks, decoded from the base64 payload (the handler does not persist
        # files to disk).
        if name == "render_shader" and result.get("rendered_frames"):
            content_blocks = []
            for frame_b64 in result["rendered_frames"]:
                image_bytes = base64.b64decode(frame_b64)
                img_content = (
                    FastMCPImage(data=image_bytes, format="png")
                    .to_image_content()
                    .model_dump()
                )
                content_blocks.append(img_content)
            return {
                "content": content_blocks,
                "isError": not result.get("success", True),
            }
        # For other tools or if no images, return as text
        import json

        return {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            "isError": not result.get("success", True),
        }

    print("All handlers registered", file=sys.stderr)
    print("Starting MCP server...", file=sys.stderr)

    # Run server
    async def run_server():
        try:
            initialization_options = server.create_initialization_options()
            async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, initialization_options)
        except Exception as e:
            logger.error(f"Error in server: {e}", exc_info=True)
            raise

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
