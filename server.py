# My First MCP Server
# 🤖 Claude can now read, write, and execute commands autonomously!
# 🔒 Enhanced with security validations and error handling
# 🧹 System cleanup and secret detection

from mcp.server.fastmcp import FastMCP
import utils  # Import our utility functions
import os
import subprocess
import re
import json
from pathlib import Path

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
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
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
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        MAX_CONTENT_SIZE = 5 * 1024 * 1024  # 5MB limit
        if len(content) > MAX_CONTENT_SIZE:
            return f"Error: Content too large ({len(content)} bytes). Maximum size is {MAX_CONTENT_SIZE} bytes."
        
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


# System Cleanup Tools
@mcp.tool()
def system_cleanup(dry_run: bool = True) -> str:
    """
    Clean up Python cache files and __pycache__ directories.
    Args:
        dry_run: If True, only shows what would be deleted without actually deleting.
    Returns:
        JSON string with cleanup results
    """
    try:
        results = {
            "pyc_files": [],
            "pycache_dirs": [],
            "total_size": 0,
            "dry_run": dry_run
        }
        
        # Find .pyc files
        for root, dirs, files in os.walk(BASE_DIR):
            for file in files:
                if file.endswith('.pyc'):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    results["pyc_files"].append({
                        "path": file_path.replace(BASE_DIR, "."),
                        "size": file_size
                    })
                    results["total_size"] += file_size
                    
                    if not dry_run:
                        os.remove(file_path)
            
            # Find __pycache__ directories
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                
                # Calculate directory size
                dir_size = 0
                for dirpath, dirnames, filenames in os.walk(pycache_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        dir_size += os.path.getsize(fp)
                
                results["pycache_dirs"].append({
                    "path": pycache_path.replace(BASE_DIR, "."),
                    "size": dir_size
                })
                results["total_size"] += dir_size
                
                if not dry_run:
                    import shutil
                    shutil.rmtree(pycache_path)
        
        return json.dumps(results, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def scan_secrets(scan_all: bool = True) -> str:
    """
    Scan project files for hardcoded secrets and sensitive information.
    Args:
        scan_all: If True, scans all files. If False, only scans Python files.
    Returns:
        JSON string with detected secrets
    """
    try:
        results = {
            "files_scanned": 0,
            "secrets_found": [],
            "summary": {
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        # Secret patterns
        secret_patterns = [
            {
                "name": "OpenAI API Key",
                "pattern": r'sk-[a-zA-Z0-9]{48}',
                "severity": "high"
            },
            {
                "name": "Anthropic API Key",
                "pattern": r'AI[a-zA-Z0-9]{40,}',
                "severity": "high"
            },
            {
                "name": "Generic API Key",
                "pattern": r'api[_-]?key\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
                "severity": "high"
            },
            {
                "name": "Password",
                "pattern": r'password\s*=\s*["\']([^"\']{3,})["\']',
                "severity": "high"
            },
            {
                "name": "Secret Key",
                "pattern": r'secret[_-]?key\s*=\s*["\']([^"\']{10,})["\']',
                "severity": "high"
            },
            {
                "name": "AWS Access Key",
                "pattern": r'AKIA[0-9A-Z]{16}',
                "severity": "high"
            },
            {
                "name": "Private Key Header",
                "pattern": r'-----BEGIN\s+(RSA\s+)?PRIVATE KEY-----',
                "severity": "high"
            },
            {
                "name": "JWT Token",
                "pattern": r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
                "severity": "medium"
            },
            {
                "name": "Database Connection String",
                "pattern": r'(mysql|postgres|mongodb):\/\/[^\s]+',
                "severity": "medium"
            },
            {
                "name": "Generic Token",
                "pattern": r'token\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
                "severity": "medium"
            }
        ]
        
        # Files to scan
        files_to_scan = []
        for root, dirs, files in os.walk(BASE_DIR):
            # Skip __pycache__ and .git directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if scan_all:
                    # Scan text files only
                    if file.endswith(('.py', '.js', '.json', '.yaml', '.yml', '.env', '.txt', '.md', '.sh')):
                        files_to_scan.append(os.path.join(root, file))
                else:
                    # Only Python files
                    if file.endswith('.py'):
                        files_to_scan.append(os.path.join(root, file))
        
        # Scan each file
        for file_path in files_to_scan:
            results["files_scanned"] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Check each pattern
                for pattern_info in secret_patterns:
                    matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE)
                    
                    for match in matches:
                        # Find line number
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Get context (the line where secret was found)
                        context_line = lines[line_num - 1].strip()
                        
                        secret = {
                            "file": file_path.replace(BASE_DIR, "."),
                            "line": line_num,
                            "type": pattern_info["name"],
                            "severity": pattern_info["severity"],
                            "context": context_line[:100] + "..." if len(context_line) > 100 else context_line,
                            "matched": match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
                        }
                        
                        results["secrets_found"].append(secret)
                        results["summary"][pattern_info["severity"]] += 1
            
            except Exception as e:
                # Skip files that can't be read
                continue
        
        return json.dumps(results, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


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
    ALLOWED_COMMANDS = [
        'gt', 'git', 'ls', 'pwd', 'echo', 'cat', 'grep', 
        'find', 'wc', 'head', 'tail', 'python', 'pip'
    ]
    
    try:
        base_command = command.strip().split()[0] if command.strip() else ""
        
        if not any(base_command.startswith(allowed) for allowed in ALLOWED_COMMANDS):
            return f"Security Error: Command '{base_command}' is not allowed. Allowed commands: {', '.join(ALLOWED_COMMANDS)}"
        
        BLOCKED_PATTERNS = ['rm -rf', '> /dev/', 'sudo', 'chmod', 'chown', '&&', '||', ';', '|']
        if any(pattern in command.lower() for pattern in BLOCKED_PATTERNS):
            return f"Security Error: Command contains blocked pattern"
        
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=BASE_DIR,
            timeout=30
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
