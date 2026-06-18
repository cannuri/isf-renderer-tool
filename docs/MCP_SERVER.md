# ISF Shader Renderer MCP Server

The ISF Shader Renderer includes a Model Context Protocol (MCP) server that allows AI assistants and other clients to programmatically render ISF shaders, validate shader content, and extract shader information.

## Overview

The MCP server provides a standardized interface for interacting with the ISF shader renderer. It supports:
- **Shader Rendering**: Render ISF shaders to JPEG images at specified time codes
- **Shader Validation**: Validate ISF shader syntax and extract metadata
- **Shader Information**: Extract detailed information from ISF shaders
- **Resource Access**: Access example shaders and documentation

## Installation

The MCP server is included with the ISF Shader Renderer package. Install with MCP dependencies:

```bash
pip install isf-shader-renderer
```

## Usage

### Starting the MCP Server

#### Command Line Interface

```bash
# Start MCP server in stdio mode (default)
isf-mcp-server --stdio

# Start HTTP server on specific port
isf-mcp-server --http --port 8000

# Enable debug/verbose output
isf-mcp-server --debug
```

#### Using the Main CLI

```bash
# Start MCP server via main CLI
isf-renderer mcp-server --stdio
# Or HTTP mode
isf-renderer mcp-server --port 8000
```

### Server Modes
- **Stdio mode** (default): Standard MCP protocol over stdio (recommended for AI assistants like Cursor)
- **HTTP mode**: RESTful API endpoints (for direct HTTP clients)

### Available Tools

#### 1. render_shader
Renders an ISF shader to JPEG images at specified time codes.

**Parameters:**
- `shader_content` (string, required): ISF shader source code
- `time_codes` (array of numbers, required): Time codes for rendering (seconds)
- `width` (integer, default: 1920): Output width in pixels
- `height` (integer, default: 1080): Output height in pixels
- `quality` (integer, default: 95): JPEG quality (1-100)
- `verbose` (boolean, default: false): Enable verbose output

**Response:**
- `success` (boolean): Whether the rendering was successful
- `message` (string): Human-readable message
- `rendered_frames` (array of strings): Base64 encoded JPEG images
- `metadata` (object): Rendering metadata
- `logs` (array of strings): All stdout/stderr output
- `shader_info` (object, optional): Extracted shader information

#### 2. validate_shader
Validates ISF shader syntax and extracts metadata.

**Parameters:**
- `shader_content` (string, required): ISF shader source code to validate

**Response:**
- `success` (boolean): Whether the shader is valid
- `message` (string): Human-readable message
- `shader_info` (object, optional): Extracted shader information
- `errors` (array of strings): Validation errors
- `warnings` (array of strings): Validation warnings

#### 3. get_shader_info
Extracts information from ISF shader.

**Parameters:**
- `shader_content` (string, required): ISF shader source code

**Response:**
- `success` (boolean): Whether the operation was successful
- `message` (string): Human-readable message
- `shader_info` (object, optional): Extracted shader information
- `errors` (array of strings): Any errors encountered

### Available Resources

The MCP server provides access to example shaders:
- `isf://examples/simple.fs`: Simple ISF shader example
- `isf://examples/gradient.fs`: Gradient ISF shader example

## Example Usage

### Python Client Example

```python
import asyncio
from isf_shader_renderer.mcp.handlers import ISFShaderHandlers

async def example():
    handlers = ISFShaderHandlers()
    shader_content = """/*{\n  \"DESCRIPTION\": \"Example Shader\"\n}*/\nvoid main() {\n  gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);\n}"""
    # Validate shader
    result = await handlers.call_tool("validate_shader", {"shader_content": shader_content})
    print(f"Validation: {result['success']}")
    # Render shader
    result = await handlers.call_tool("render_shader", {
        "shader_content": shader_content,
        "time_codes": [0.0, 1.0],
        "width": 640,
        "height": 480
    })
    print(f"Rendered {len(result['rendered_frames'])} frames")

asyncio.run(example())
```

### HTTP API Example

```bash
# Render shader
curl -X POST http://localhost:8000/render \
  -H "Content-Type: application/json" \
  -d '{
    "shader_content": "/* ISF shader */ void main() { gl_FragColor = vec4(1.0); }",
    "time_codes": [0.0, 1.0],
    "width": 640,
    "height": 480
  }'

# Validate shader
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "shader_content": "/* ISF shader */ void main() { gl_FragColor = vec4(1.0); }"
  }'
```

## Configuration

The MCP server can be configured via environment variables or a YAML config file.

### Environment Variables
- `MCP_SERVER_HOST`: Server host (default: localhost)
- `MCP_SERVER_PORT`: Server port (default: 8000)
- `MCP_SERVER_MAX_IMAGE_SIZE`: Maximum image size (default: 4096)
- `MCP_SERVER_MAX_FRAMES`: Maximum frames per request (default: 10)
- `MCP_SERVER_TEMP_DIR`: Temporary directory (default: /tmp/isf_renderer)

### Configuration File Example (`mcp_config.yaml`)
```yaml
server:
  host: localhost
  port: 8000
  enable_http: false
rendering:
  max_image_size: 4096
  max_frames_per_request: 10
  temp_dir: /tmp/isf_renderer
security:
  allowed_origins: []
  api_key: null
logging:
  level: INFO
  enable_debug: false
```

## Error Handling

The MCP server provides structured error responses:

```json
{
  "success": false,
  "message": "Error description",
  "errors": ["Detailed error 1", "Detailed error 2"],
  "metadata": {},
  "logs": ["Error log 1", "Error log 2"]
}
```

### Common Error Codes
- `INVALID_SHADER`: Shader content is invalid or malformed
- `RENDERING_FAILED`: Shader rendering failed
- `VALIDATION_FAILED`: Shader validation failed
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `INVALID_PARAMETERS`: Invalid request parameters

## Security Considerations
- The MCP server runs with the same permissions as the user
- Temporary files are automatically cleaned up
- Input validation is performed on all parameters
- File size limits are enforced to prevent resource exhaustion

## Performance
- Rendering is performed in memory with temporary files
- JPEG encoding adds overhead to image data
- Multiple frames are rendered sequentially
- Large images may take significant time to process

## Troubleshooting

### Common Issues
1. **MCP server won't start**
   - Check if all dependencies are installed
   - Verify port availability (if using HTTP mode)
   - Check file permissions for temp directory
2. **Rendering fails**
   - Validate shader content first
   - Check available disk space
   - Verify image dimensions are reasonable
3. **Performance issues**
   - Reduce image dimensions
   - Limit number of time codes
   - Use lower quality settings

### Debug Mode
Enable debug mode for detailed logging:
```bash
isf-mcp-server --debug
```

## Integration with AI Assistants

### Cursor Integration
Add to your Cursor configuration:
```json
{
  "mcpServers": {
    "isf-shader-renderer": {
      "command": "isf-mcp-server",
      "args": ["--stdio"]
    }
  }
}
```

### Other AI Assistants
The MCP server follows the Model Context Protocol specification and should work with any MCP-compatible client.

## Development

### Running Tests
```bash
pytest tests/test_mcp.py -v
```

### Example Script
Run the example script to test functionality:
```bash
python examples/mcp_example.py
```

### Building from Source
```bash
git clone <repository>
cd ai-shader-tool
pip install -e .
isf-mcp-server --help
```

## License
The MCP server is part of the ISF Shader Renderer and is licensed under the MIT License. 