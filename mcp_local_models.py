"""
MCP Server: Local Model Inference
Provides local model execution without API keys or external dependencies.
Supports: Ollama, GGUF files, Hugging Face transformers
"""

import json
import subprocess
import os
import sys
from typing import Any

# MCP Tool Registry
TOOLS = {
    "ollama_run": {
        "description": "Run Ollama model locally",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "Model name (e.g., mistral, llama2)"},
                "prompt": {"type": "string", "description": "Input prompt"},
                "temperature": {"type": "number", "description": "Temperature (0.0-1.0)", "default": 0.7},
                "max_tokens": {"type": "integer", "description": "Max output tokens", "default": 512}
            },
            "required": ["model", "prompt"]
        }
    },
    "gguf_run": {
        "description": "Run GGUF model locally via llama-cpp-python",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_path": {"type": "string", "description": "Path to .gguf file"},
                "prompt": {"type": "string", "description": "Input prompt"},
                "temperature": {"type": "number", "description": "Temperature (0.0-1.0)", "default": 0.7},
                "max_tokens": {"type": "integer", "description": "Max output tokens", "default": 512}
            },
            "required": ["model_path", "prompt"]
        }
    },
    "list_ollama_models": {
        "description": "List all available Ollama models",
        "inputSchema": {"type": "object", "properties": {}}
    }
}


def run_ollama(model: str, prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
    """Run inference via Ollama (local, no API key)"""
    try:
        # Check if Ollama is running
        subprocess.run(["ollama", "list"], capture_output=True, timeout=2, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "ERROR: Ollama not running. Install from https://ollama.ai and run: ollama serve"

    try:
        result = subprocess.run(
            ["ollama", "run", model, "--format", "json"],
            input=prompt.encode(),
            capture_output=True,
            timeout=120,
            text=True
        )

        if result.returncode == 0:
            # Parse JSON response
            try:
                data = json.loads(result.stdout)
                return data.get("response", result.stdout)
            except:
                return result.stdout
        else:
            return f"ERROR: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "ERROR: Model inference timed out (>120s)"
    except Exception as e:
        return f"ERROR: {str(e)}"


def run_gguf(model_path: str, prompt: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
    """Run GGUF model via llama-cpp-python (local, no API key)"""
    try:
        from llama_cpp import Llama
    except ImportError:
        return "ERROR: llama-cpp-python not installed. Run: pip install llama-cpp-python"

    if not os.path.exists(model_path):
        return f"ERROR: Model file not found: {model_path}"

    try:
        # Load model (GPU if available, otherwise CPU)
        llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,  # Use GPU if available
            n_ctx=2048,  # Context window
            verbose=False
        )

        # Run inference
        response = llm(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
            stop=["\n"]
        )

        return response["choices"][0]["text"].strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


def list_ollama_models() -> str:
    """List all available Ollama models"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return "No Ollama models found. Run: ollama pull mistral"
    except FileNotFoundError:
        return "ERROR: Ollama not installed. Download from https://ollama.ai"
    except Exception as e:
        return f"ERROR: {str(e)}"


def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """Process MCP tool calls"""

    if tool_name == "ollama_run":
        return run_ollama(
            model=tool_input["model"],
            prompt=tool_input["prompt"],
            temperature=tool_input.get("temperature", 0.7),
            max_tokens=tool_input.get("max_tokens", 512)
        )

    elif tool_name == "gguf_run":
        return run_gguf(
            model_path=tool_input["model_path"],
            prompt=tool_input["prompt"],
            temperature=tool_input.get("temperature", 0.7),
            max_tokens=tool_input.get("max_tokens", 512)
        )

    elif tool_name == "list_ollama_models":
        return list_ollama_models()

    else:
        return f"ERROR: Unknown tool: {tool_name}"


# ============================================================================
# MCP Integration (if used as subprocess)
# ============================================================================

if __name__ == "__main__":
    # For testing
    print("=== Local Model MCP Server ===")
    print(f"Available tools: {list(TOOLS.keys())}")
    print()

    # List Ollama models
    print("Ollama models:")
    print(list_ollama_models())
    print()

    # Test Ollama if available
    test_model = "mistral"
    print(f"Testing {test_model}...")
    result = run_ollama(test_model, "What is AI in one sentence?")
    print(f"Response: {result}")
