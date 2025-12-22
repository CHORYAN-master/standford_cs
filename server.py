# My First MCP Server
# 🤖 Claude can now read, write, and execute commands autonomously!
# 🔒 Enhanced with security validations and error handling

from mcp.server.fastmcp import FastMCP
import utils  # Import our utility functions
import os

# Security: Define base directory for file operations
BASE_DIR = "/Users/hyunhocho/Desktop/Stanford_CS/week2"

# 1. 서버 이름 설정 (AI가 식별할 이름)
mcp = FastMCP("My Desktop Assistant")

# 2. 기능 만들기: AI가 사용할 도구(Tool) 정의

# Math Tools
@mcp.tool()
def add_two_numbers(a: int, b: int) -> int:
    """Add two numbers together. Use this for basic math."""
    try:
        return utils.add_numbers(a, b)
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


# File System Tools
@mcp.tool()
def list_files(directory: str = ".") -> str:
    """List all files in the given directory (within project directory only)."""
    try:
        # Validate path security
        safe_path = utils.validate_safe_path(directory, BASE_DIR)
        files = os.listdir(safe_path)
        return "\n".join(sorted(files))
    except ValueError as e:
        return f"Security Error: {str(e)}"
    except FileNotFoundError:
        return f"Error: Directory not found: {directory}"
    except PermissionError:
        return f"Error: Permission denied accessing: {directory}"
    except Exception as e:
        return f"Error reading directory: {str(e)}"


@mcp.tool()
def read_file(file_path: str) -> str:
    """Read and return the contents of a file (within project directory only)."""
    try:
        # Validate path security
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        # Check file size before reading (prevent memory issues)
        file_size = os.path.getsize(safe_path)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
        if file_size > MAX_FILE_SIZE:
            return f"Error: File too large ({file_size} bytes). Maximum size is {MAX_FILE_SIZE} bytes."
        
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except ValueError as e:
        return f"Security Error: {str(e)}"
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
    """Write content to a file (within project directory only). Creates the file if it doesn't exist."""
    try:
        # Validate path security
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        # Validate content size
        MAX_CONTENT_SIZE = 5 * 1024 * 1024  # 5MB limit
        if len(content) > MAX_CONTENT_SIZE:
            return f"Error: Content too large ({len(content)} bytes). Maximum size is {MAX_CONTENT_SIZE} bytes."
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to: {file_path}"
    except ValueError as e:
        return f"Security Error: {str(e)}"
    except PermissionError:
        return f"Error: Permission denied writing to: {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


# Time Tools
@mcp.tool()
def get_current_time() -> str:
    """Get the current date and time."""
    try:
        return utils.get_current_datetime()
    except Exception as e:
        return f"Error getting time: {str(e)}"


@mcp.tool()
def get_time() -> str:
    """Get the current time in HH:MM:SS format."""
    try:
        return utils.get_current_time_only()
    except Exception as e:
        return f"Error getting time: {str(e)}"


# User Interaction Tools
@mcp.tool()
def greet_user(name: str) -> str:
    """Greet a user with their name and the current time."""
    try:
        return utils.format_greeting(name)
    except ValueError as e:
        return f"Input Error: {str(e)}"
    except Exception as e:
        return f"Error creating greeting: {str(e)}"


# System Tools
@mcp.tool()
def run_command(command: str) -> str:
    """
    Execute a shell command and return the output.
    WARNING: Only safe, whitelisted commands are allowed.
    """
    import subprocess
    
    # Security: Whitelist of allowed commands
    ALLOWED_COMMANDS = [
        'gt', 'git', 'ls', 'pwd', 'echo', 'cat', 'grep', 
        'find', 'wc', 'head', 'tail', 'python', 'pip'
    ]
    
    try:
        # Extract base command
        base_command = command.strip().split()[0] if command.strip() else ""
        
        # Check if command is whitelisted
        if not any(base_command.startswith(allowed) for allowed in ALLOWED_COMMANDS):
            return f"Security Error: Command '{base_command}' is not allowed. Allowed commands: {', '.join(ALLOWED_COMMANDS)}"
        
        # Additional security: Block dangerous patterns
        BLOCKED_PATTERNS = ['rm -rf', '> /dev/', 'sudo', 'chmod', 'chown', '&&', '||', ';', '|']
        if any(pattern in command.lower() for pattern in BLOCKED_PATTERNS):
            return f"Security Error: Command contains blocked pattern"
        
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=BASE_DIR,
            timeout=30  # Prevent hanging commands
        )
        output = result.stdout if result.stdout else result.stderr
        return output if output else "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


@mcp.tool()
def check_status() -> str:
    """Check if the server is running."""
    return "Server is running perfectly! 🚀"


# 3. 서버 실행 (터미널에서 이 파일을 실행하면 작동 시작)
if __name__ == "__main__":
    mcp.run()
