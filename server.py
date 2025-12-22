# My First MCP Server
# 🤖 Claude can now read, write, and execute commands autonomously!

from mcp.server.fastmcp import FastMCP
import utils  # Import our utility functions

# 1. 서버 이름 설정 (AI가 식별할 이름)
mcp = FastMCP("My Desktop Assistant")

# 2. 기능 만들기: AI가 사용할 도구(Tool) 정의

# Math Tools
@mcp.tool()
def add_two_numbers(a: int, b: int) -> int:
    """Add two numbers together. Use this for basic math."""
    return utils.add_numbers(a, b)


# File System Tools
@mcp.tool()
def list_files(directory: str = ".") -> str:
    """List all files in the given directory."""
    import os
    try:
        files = os.listdir(directory)
        return "\n".join(sorted(files))
    except FileNotFoundError:
        return f"Error: Directory not found: {directory}"
    except PermissionError:
        return f"Error: Permission denied accessing: {directory}"
    except Exception as e:
        return f"Error reading directory: {str(e)}"


@mcp.tool()
def read_file(file_path: str) -> str:
    """Read and return the contents of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except PermissionError:
        return f"Error: Permission denied reading: {file_path}"
    except UnicodeDecodeError:
        return f"Error: Cannot read file (binary or encoding issue): {file_path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def write_file(file_path: str, content: str) -> str:
    """Write content to a file. Creates the file if it doesn't exist."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to: {file_path}"
    except PermissionError:
        return f"Error: Permission denied writing to: {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


# Time Tools
@mcp.tool()
def get_current_time() -> str:
    """Get the current date and time."""
    return utils.get_current_datetime()


@mcp.tool()
def get_time() -> str:
    """Get the current time in HH:MM:SS format."""
    return utils.get_current_time_only()


# User Interaction Tools
@mcp.tool()
def greet_user(name: str) -> str:
    """Greet a user with their name and the current time."""
    return utils.format_greeting(name)


# System Tools
@mcp.tool()
def run_command(command: str) -> str:
    """Execute a shell command and return the output."""
    import subprocess
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd="/Users/hyunhocho/Desktop/Stanford_CS/week2"
        )
        output = result.stdout if result.stdout else result.stderr
        return output if output else "Command executed successfully (no output)"
    except Exception as e:
        return f"Error executing command: {str(e)}"


@mcp.tool()
def check_status() -> str:
    """Check if the server is running."""
    return "Server is running perfectly!"


# 3. 서버 실행 (터미널에서 이 파일을 실행하면 작동 시작)
if __name__ == "__main__":
    mcp.run()
