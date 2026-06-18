# AI Guide: ISF Shader Renderer

This guide provides comprehensive information for AI systems to effectively use the ISF Shader Renderer command-line tool for shader validation, compilation testing, and visual effect generation.

## Command Overview

**Tool Name**: `isf-renderer`
**Purpose**: Render ISF (Interactive Shader Format) shaders to PNG images
**AI-Friendly Flag**: `--ai-info` (provides natural language output without colors/formatting)

## Essential Command Structure

```bash
isf-renderer <shader_file> --output <output_path> [options]
```

## Core Parameters

### Required Parameters
- `shader_file`: Path to ISF shader file (`.fs` extension) or `-` for stdin
- `--output` / `-o`: Output image path (PNG format)

### Key Optional Parameters
- `--ai-info`: **CRITICAL** - Use this flag for AI processing (natural language output)
- `--time` / `-t`: Time code for animation (can specify multiple times)
- `--width` / `-w`: Output width (default: 1920)
- `--height` / `-h`: Output height (default: 1080)
- `--inputs`: Shader input values as `key=value` pairs
- `--config` / `-c`: YAML configuration file for batch rendering

## AI-Optimized Usage Patterns

### 1. Basic Shader Validation
```bash
isf-renderer shader.fs --output test.png --ai-info
```
**Purpose**: Test if a shader compiles and renders successfully
**Expected Output**:
- Success: `Successfully rendered 1 frame`
- Failure: Natural language error description

### 2. Shader Compilation Testing
```bash
isf-renderer shader.fs --output test.png --ai-info --time 0
```
**Purpose**: Validate shader at specific time point
**Use Case**: Testing shader compilation and basic functionality

### 3. Animation Frame Generation
```bash
isf-renderer shader.fs --output frame_%04d.png --ai-info --time 0 --time 1 --time 2
```
**Purpose**: Generate multiple frames for animation
**Output**: `frame_0000.png`, `frame_0001.png`, `frame_0002.png`

### 4. Input Parameter Testing
```bash
isf-renderer shader.fs --output test.png --ai-info --inputs "color=1.0 0.0 0.0 1.0,intensity=0.8"
```
**Purpose**: Test shader with specific input parameters
**Use Case**: Validating shader behavior with different inputs

## Error Handling and Interpretation

### Common Error Patterns

#### 1. Missing Main Function
**Error**: `The shader is missing a main function. ISF shaders require a 'void main()' function to define the fragment shader entry point.`
**Action**: Add `void main()` function to shader

#### 2. Syntax Errors
**Error**: `The shader contains syntax errors: [details]. Please check the GLSL syntax and ensure all brackets, semicolons, and function calls are properly formatted.`
**Action**: Fix GLSL syntax issues (missing semicolons, brackets, etc.)

#### 3. Compilation Errors
**Error**: `The shader failed to compile: [details]. This usually indicates syntax errors, undefined variables, or unsupported GLSL features.`
**Action**: Check for undefined variables, unsupported functions, or GLSL version issues

#### 4. File Not Found
**Error**: `File not found: [filename]. Please check that the file path is correct and the file exists.`
**Action**: Verify file path and ensure file exists

### Success Patterns

#### Single Frame Success
```
Successfully rendered 1 frame
```

#### Multiple Frames Success
```
Successfully rendered 5 frames
```

#### Partial Success (Some Frames Failed)
```
Completed rendering with 3 successful frames and 2 failed frames
```

## Input Parameter Format

### Supported Input Types
- `bool`: `true` or `false`
- `int`: Integer values
- `float`: Decimal numbers
- `point2D`: Two float values (e.g., `0.5 0.3`)
- `color`: Four float values RGBA (e.g., `1.0 0.0 0.0 1.0`)
- `image`: File path to image file

### Input Syntax Examples
```bash
# Single input
--inputs "color=1.0 0.0 0.0 1.0"

# Multiple inputs
--inputs "intensity=0.8,position=0.5 0.3,enabled=true"

# Complex inputs
--inputs "color=0.2 0.4 0.6 1.0,scale=2.5,offset=0.1 0.2,useTexture=true"
```

## Batch Rendering with Configuration Files

### Configuration File Format (YAML)
```yaml
defaults:
  width: 1920
  height: 1080
  quality: 95

shaders:
  - input: "shader1.fs"
    output: "output1_%04d.png"
    times: [0.0, 1.0, 2.0]
    inputs:
      color: [1.0, 0.0, 0.0, 1.0]
```

### Batch Rendering Command
```bash
isf-renderer --config config.yaml --ai-info
```

## Sample AI Prompts and Responses

### Prompt 1: Validate Shader Compilation
**User**: "Test if this shader compiles and renders correctly"
**AI Action**:
```bash
isf-renderer user_shader.fs --output test.png --ai-info
```
**Response**: "Successfully rendered 1 frame" or specific error description

### Prompt 2: Generate Animation Frames
**User**: "Create 10 frames of animation from this shader"
**AI Action**:
```bash
isf-renderer animation_shader.fs --output frame_%04d.png --ai-info --time 0 --time 0.1 --time 0.2 --time 0.3 --time 0.4 --time 0.5 --time 0.6 --time 0.7 --time 0.8 --time 0.9
```
**Response**: "Successfully rendered 10 frames"

### Prompt 3: Test Shader with Different Parameters
**User**: "Test this shader with red, green, and blue colors"
**AI Action**:
```bash
# Red
isf-renderer color_shader.fs --output red.png --ai-info --inputs "color=1.0 0.0 0.0 1.0"
# Green
isf-renderer color_shader.fs --output green.png --ai-info --inputs "color=0.0 1.0 0.0 1.0"
# Blue
isf-renderer color_shader.fs --output blue.png --ai-info --inputs "color=0.0 0.0 1.0 1.0"
```

### Prompt 4: Debug Shader Errors
**User**: "Why isn't this shader working?"
**AI Action**:
```bash
isf-renderer broken_shader.fs --output debug.png --ai-info
```
**Response**: Natural language error description with actionable advice

### Prompt 5: Batch Process Multiple Shaders
**User**: "Render all shaders in the shaders/ directory"
**AI Action**:
```bash
# Create config.yaml with all shaders
isf-renderer --config batch_config.yaml --ai-info
```

## Advanced Usage Patterns

### 1. Stdin Input (for dynamic shader generation)
```bash
echo "void main() { gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); }" | isf-renderer - --output dynamic.png --ai-info
```

### 2. High-Quality Rendering
```bash
isf-renderer shader.fs --output hq.png --ai-info --width 3840 --height 2160 --quality 100
```

### 3. Small Test Renders
```bash
isf-renderer shader.fs --output test.png --ai-info --width 256 --height 256
```

### 4. Time-Based Animation Testing
```bash
isf-renderer animated_shader.fs --output anim_%04d.png --ai-info --time 0:2:0.1
```

## Error Recovery Strategies

### 1. Syntax Error Recovery
- Parse error message for specific line/character
- Check for missing semicolons, brackets, or parentheses
- Verify GLSL syntax compliance

### 2. Missing Function Recovery
- Ensure `void main()` function exists
- Check function signatures and return types
- Verify ISF metadata format

### 3. Input Parameter Recovery
- Validate input parameter names match shader definition
- Check parameter types and value ranges
- Ensure required inputs are provided

### 4. Performance Issues
- Reduce render dimensions if memory errors occur
- Use smaller `width`/`height` in configuration
- Test with lower quality settings first

## Best Practices for AI Usage

### 1. Always Use `--ai-info` Flag
- Provides consistent, parseable output
- No terminal colors or formatting to parse
- Natural language error descriptions

### 2. Test Incrementally
- Start with basic compilation test
- Add parameters one at a time
- Test with small dimensions first

### 3. Handle Errors Gracefully
- Parse error messages for actionable information
- Provide specific feedback to users
- Suggest fixes based on error patterns

### 4. Validate Output
- Check that output files were created
- Verify file sizes are reasonable
- Confirm image format is correct

### 5. Use Appropriate Dimensions
- Start with small test renders (256x256)
- Scale up for final output
- Consider memory constraints

## Integration Patterns

### 1. CI/CD Pipeline Integration
```bash
# Test shader compilation in pipeline
isf-renderer shader.fs --output test.png --ai-info
if [ $? -eq 0 ]; then
    echo "Shader compilation successful"
else
    echo "Shader compilation failed"
    exit 1
fi
```

### 2. Automated Testing
```bash
# Test multiple shaders
for shader in shaders/*.fs; do
    isf-renderer "$shader" --output "test_$(basename "$shader" .fs).png" --ai-info
done
```

### 3. Dynamic Shader Generation
```bash
# Generate shader content dynamically
shader_content="void main() { gl_FragColor = vec4($r, $g, $b, 1.0); }"
echo "$shader_content" | isf-renderer - --output dynamic.png --ai-info
```

## Troubleshooting Guide

### Debugging Commands

```bash
# Test with verbose output
isf-renderer shader.fs --output test.png --ai-info --verbose

# Test with profiling
isf-renderer shader.fs --output test.png --ai-info --profile

# Test with minimal settings
isf-renderer shader.fs --output test.png --ai-info --width 64 --height 64
```

## Output Interpretation

### Success Indicators
- Command returns exit code 0
- Output contains "Successfully rendered"
- Output file exists and has reasonable size

### Failure Indicators
- Command returns non-zero exit code
- Output contains error description
- No output file created or file is empty

### Partial Success
- Some frames rendered successfully
- Some frames failed
- Mixed success/failure message

This guide provides all the essential information for AI systems to effectively use the ISF Shader Renderer for shader validation, testing, and generation tasks.
