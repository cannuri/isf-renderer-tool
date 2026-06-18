#!/usr/bin/env python3
"""Simple MCP client for testing the ISF Shader Renderer MCP server."""

import asyncio
import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path


class SimpleMCPClient:
    """Simple MCP client for testing."""

    def __init__(self, server_process):
        """Initialize the client with a server process."""
        self.server_process = server_process
        self.request_id = 1

    def _next_id(self) -> int:
        """Get next request ID."""
        current = self.request_id
        self.request_id += 1
        return current

    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a request to the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {}
        }

        # Send request
        request_json = json.dumps(request) + "\n"
        self.server_process.stdin.write(request_json.encode())
        await self.server_process.stdin.drain()

        # Read response
        response_line = await self.server_process.stdout.readline()
        response = json.loads(response_line.decode().strip())

        if "error" in response:
            raise Exception(f"MCP Error: {response['error']}")

        return response.get("result", {})

    async def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Send a notification to the MCP server (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }

        # Send notification (no ID, no response expected)
        notification_json = json.dumps(notification) + "\n"
        self.server_process.stdin.write(notification_json.encode())
        await self.server_process.stdin.drain()

    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection."""
        return await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "clientInfo": {
                "name": "simple-mcp-client",
                "version": "1.0.0"
            }
        })

    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return await self.send_request("tools/list", {})

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool."""
        return await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

    async def list_resources(self) -> Dict[str, Any]:
        """List available resources."""
        return await self.send_request("resources/list", {})

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource."""
        return await self.send_request("resources/read", {
            "uri": uri
        })


async def test_mcp_client():
    """Test the MCP client with the server."""
    import subprocess

    print("Starting MCP server...")

    # Start the MCP server as a subprocess
    server_process = await asyncio.create_subprocess_exec(
        "isf-mcp-server", "--stdio",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        # Create client
        client = SimpleMCPClient(server_process)

        print("Initializing MCP connection...")
        init_result = await client.initialize()
        print(f"Initialization result: {init_result}")

        # Send initialized notification (this is a notification, not a request)
        try:
            await client.send_notification("notifications/initialized", {})
            print("Initialized notification sent successfully")
        except Exception as e:
            print(f"Initialized notification failed (this may be normal): {e}")

        print("\nListing tools...")
        tools_result = await client.list_tools()
        print(f"Available tools: {len(tools_result.get('tools', []))}")
        for tool in tools_result.get('tools', []):
            print(f"  - {tool['name']}: {tool['description']}")

        print("\nListing resources...")
        resources_result = await client.list_resources()
        print(f"Available resources: {len(resources_result.get('resources', []))}")
        for resource in resources_result.get('resources', []):
            print(f"  - {resource['name']}: {resource['description']}")

        # Test shader validation
        print("\nTesting shader validation...")
        test_shader = """/*{
    "DESCRIPTION": "Test Shader"
}*/
void main() {
    vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy;
    gl_FragColor = vec4(uv.x, uv.y, 0.5, 1.0);
}"""

        validate_result = await client.call_tool("validate_shader", {
            "shader_content": test_shader
        })
        print(f"Validation result: {validate_result}")

        # Test shader rendering
        print("\nTesting shader rendering...")
        render_result = await client.call_tool("render_shader", {
            "shader_content": test_shader,
            "time_codes": [0.0, 1.0],  # Two time codes
            "width": 320,  # Larger size
            "height": 240  # Larger size
        })
        print(f"Render result: {render_result}")

        # Test resource reading
        if resources_result.get('resources'):
            print("\nTesting resource reading...")
            first_resource = resources_result['resources'][0]
            read_result = await client.read_resource(first_resource['uri'])
            print(f"Resource content length: {len(read_result.get('contents', []))}")
            if read_result.get('contents'):
                content = read_result['contents'][0]
                print(f"First 100 chars: {content['text'][:100]}")

        print("\nMCP client test completed successfully!")

    except Exception as e:
        print(f"Error during MCP client test: {e}")
        # Get stderr output for debugging
        if server_process.stderr:
            stderr_output = await server_process.stderr.read()
            if stderr_output:
                print(f"Server stderr: {stderr_output.decode()}")
        raise
    finally:
        # Terminate the server
        server_process.terminate()
        await server_process.wait()


def main():
    """Main function."""
    print("Simple MCP Client Test")
    print("This will test the MCP server via stdio protocol.")
    print()

    try:
        asyncio.run(test_mcp_client())
        return 0
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())