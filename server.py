# My First MCP Server - Security Hardened Edition
# 🔒 Enhanced with comprehensive security controls
# 🛡️ Environment-based configuration
# 📊 Structured logging
# ⚡ Rate limiting

from mcp.server.fastmcp import FastMCP
import utils
import os
import subprocess
import json
import glob
import logging
from pathlib import Path

# Import security and configuration modules
from config import config, BASE_DIR, PROJECT_DIR
from security import (
    validate_commit_message,
    validate_command_strict,
    validate_filename,
    validate_git_command,
    RateLimiter,
    sanitize_error_message
)

# Setup logging
logger = logging.getLogger(__name__)

# Initialize rate limiters
from config import config as cfg

# Different rate limits for different operation types
file_read_limiter = RateLimiter(max_calls=cfg.rate_limit.calls_per_minute, time_window=60)
file_write_limiter = RateLimiter(max_calls=50, time_window=60)  # Stricter for writes
git_limiter = RateLimiter(max_calls=30, time_window=60)
command_limiter = RateLimiter(max_calls=20, time_window=60)  # Most restrictive

# Initialize MCP server
mcp = FastMCP("My Desktop Assistant - Security Hardened")


# ==================== Math Tools ====================

@mcp.tool()
def add_two_numbers(a: int, b: int) -> str:
    """
    Add two numbers together. Use this for basic math.
    
    Returns JSON with result or error.
    """
    try:
        result = utils.add_numbers(a, b)
        logger.info(f"Math operation: {a} + {b} = {result}")
        return json.dumps({"success": True, "result": result})
    except ValueError as e:
        logger.warning(f"Math operation failed: {e}")
        return json.dumps({"success": False, "error": "Invalid input range"})
    except Exception as e:
        error_msg = sanitize_error_message(e, "addition")
        return json.dumps({"success": False, "error": error_msg})


# ==================== File System Tools ====================

@mcp.tool()
@file_read_limiter
def list_files(directory: str = ".") -> str:
    """List all files in the given directory (within Desktop)."""
    try:
        safe_path = utils.validate_safe_path(directory, BASE_DIR)
        files = os.listdir(safe_path)
        logger.info(f"Listed directory: {directory}")
        return "\n".join(sorted(files))
    except ValueError as e:
        logger.warning(f"Path validation failed: {directory}")
        return "Error: Invalid directory path"
    except FileNotFoundError:
        logger.info(f"Directory not found: {directory}")
        return "Error: Directory not found"
    except PermissionError:
        logger.error(f"Permission denied: {directory}")
        return "Error: Permission denied"
    except Exception as e:
        return sanitize_error_message(e, "list directory")


@mcp.tool()
@file_read_limiter
def read_file(file_path: str) -> str:
    """Read and return the contents of a file (within Desktop)."""
    try:
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        file_size = os.path.getsize(safe_path)
        if file_size > config.files.max_file_size_bytes:
            logger.warning(f"File too large: {file_size} bytes")
            return f"Error: File exceeds {config.files.max_file_size_mb}MB limit"
        
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Read file: {file_path} ({file_size} bytes)")
        return content
        
    except ValueError as e:
        logger.warning(f"Path validation failed: {file_path}")
        return "Error: Invalid file path"
    except FileNotFoundError:
        logger.info(f"File not found: {file_path}")
        return "Error: File not found"
    except PermissionError:
        logger.error(f"Permission denied: {file_path}")
        return "Error: Access denied"
    except UnicodeDecodeError:
        logger.warning(f"Encoding error: {file_path}")
        return "Error: Cannot read file (encoding issue)"
    except Exception as e:
        return sanitize_error_message(e, "read file")


@mcp.tool()
@file_write_limiter
def write_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """
    Write content to a file (within Desktop).
    
    Args:
        file_path: Path to file
        content: Content to write
        overwrite: If True, overwrites existing file
    """
    try:
        # Validate filename
        is_valid, error = validate_filename(file_path)
        if not is_valid:
            logger.warning(f"Invalid filename: {file_path} - {error}")
            return f"Error: {error}"
        
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        # Size check
        if len(content) > config.files.max_content_size_bytes:
            logger.warning(f"Content too large: {len(content)} bytes")
            return f"Error: Content exceeds {config.files.max_content_size_mb}MB limit"
        
        # Check if file exists
        if os.path.exists(safe_path) and not overwrite:
            logger.info(f"File exists, overwrite=False: {file_path}")
            return "Error: File exists. Set overwrite=True to replace"
        
        # Create directory if needed
        parent_dir = os.path.dirname(safe_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, mode=0o755, exist_ok=True)
        
        # Write file
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Set permissions
        os.chmod(safe_path, 0o644)
        
        logger.info(f"Wrote file: {file_path} ({len(content)} bytes)")
        return f"Successfully wrote to: {file_path}"
        
    except ValueError as e:
        logger.warning(f"Path validation failed: {file_path}")
        return "Error: Invalid file path"
    except PermissionError:
        logger.error(f"Permission denied: {file_path}")
        return "Error: Permission denied"
    except Exception as e:
        return sanitize_error_message(e, "write file")


@mcp.tool()
@file_write_limiter
def create_directory(dir_path: str) -> str:
    """Create a new directory within Desktop."""
    try:
        safe_path = utils.validate_safe_path(dir_path, BASE_DIR)
        os.makedirs(safe_path, mode=0o755, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
        return f"Created directory: {dir_path}"
    except ValueError as e:
        logger.warning(f"Path validation failed: {dir_path}")
        return "Error: Invalid directory path"
    except Exception as e:
        return sanitize_error_message(e, "create directory")


@mcp.tool()
@file_write_limiter
def delete_file(file_path: str) -> str:
    """Delete a file (within Desktop)."""
    try:
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        if not os.path.exists(safe_path):
            logger.info(f"Delete attempt on non-existent file: {file_path}")
            return "Error: File not found"
        
        # Log before deletion
        file_size = os.path.getsize(safe_path)
        logger.warning(f"Deleting file: {file_path} ({file_size} bytes)")
        
        os.remove(safe_path)
        logger.info(f"File deleted: {file_path}")
        return f"Deleted: {file_path}"
        
    except ValueError as e:
        logger.warning(f"Path validation failed: {file_path}")
        return "Error: Invalid file path"
    except PermissionError:
        logger.error(f"Permission denied: {file_path}")
        return "Error: Permission denied"
    except Exception as e:
        return sanitize_error_message(e, "delete file")


@mcp.tool()
@file_write_limiter
def move_file(src: str, dst: str) -> str:
    """Move or rename a file within Desktop."""
    try:
        safe_src = utils.validate_safe_path(src, BASE_DIR)
        safe_dst = utils.validate_safe_path(dst, BASE_DIR)
        
        # Validate destination filename
        is_valid, error = validate_filename(dst)
        if not is_valid:
            logger.warning(f"Invalid destination filename: {dst}")
            return f"Error: {error}"
        
        # Create destination directory if needed
        dst_dir = os.path.dirname(safe_dst)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir, mode=0o755, exist_ok=True)
        
        os.rename(safe_src, safe_dst)
        logger.info(f"Moved file: {src} -> {dst}")
        return f"Moved {src} to {dst}"
        
    except ValueError as e:
        logger.warning(f"Path validation failed: {src} or {dst}")
        return "Error: Invalid file path"
    except Exception as e:
        return sanitize_error_message(e, "move file")


@mcp.tool()
def organize_screenshots(max_files: int = 1000) -> str:
    """
    Find all screenshot files on Desktop and move them to Screenshots folder.
    
    Args:
        max_files: Maximum number of files to process (default: 1000)
    """
    try:
        # Validate BASE_DIR exists
        if not os.path.isdir(BASE_DIR):
            logger.error(f"BASE_DIR does not exist: {BASE_DIR}")
            return json.dumps({"error": "Base directory not found"})
        
        results = {
            "found": [],
            "moved": [],
            "skipped": [],
            "errors": []
        }
        
        screenshots_dir = os.path.join(BASE_DIR, "Screenshots")
        os.makedirs(screenshots_dir, mode=0o755, exist_ok=True)
        
        # Find screenshot files
        patterns = [
            os.path.join(BASE_DIR, "screenshot*"),
            os.path.join(BASE_DIR, "Screenshot*")
        ]
        
        screenshot_files = []
        for pattern in patterns:
            screenshot_files.extend(glob.glob(pattern))
        
        screenshot_files = list(set(screenshot_files))
        
        # Apply limit
        if len(screenshot_files) > max_files:
            logger.warning(f"Too many screenshot files: {len(screenshot_files)}")
            results["skipped"] = [os.path.basename(f) for f in screenshot_files[max_files:]]
            screenshot_files = screenshot_files[:max_files]
        
        results["found"] = [os.path.basename(f) for f in screenshot_files]
        
        # Move each file
        for file_path in screenshot_files:
            try:
                # Skip if already in Screenshots
                if os.path.dirname(file_path) == screenshots_dir:
                    results["skipped"].append(os.path.basename(file_path))
                    continue
                
                filename = os.path.basename(file_path)
                dest_path = os.path.join(screenshots_dir, filename)
                
                # Handle duplicates
                counter = 1
                base_name, ext = os.path.splitext(filename)
                while os.path.exists(dest_path):
                    filename = f"{base_name}_{counter}{ext}"
                    dest_path = os.path.join(screenshots_dir, filename)
                    counter += 1
                
                os.rename(file_path, dest_path)
                results["moved"].append(filename)
                logger.info(f"Moved screenshot: {filename}")
                
            except Exception as e:
                error_msg = f"{os.path.basename(file_path)}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(f"Failed to move {file_path}: {e}")
        
        logger.info(f"Screenshot organization complete: {len(results['moved'])} moved")
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error(f"organize_screenshots failed: {e}", exc_info=True)
        return json.dumps({"error": "Operation failed"})


# ==================== Git/Graphite Tools ====================

@mcp.tool()
@git_limiter
def git_status() -> str:
    """Get current git status."""
    try:
        result = subprocess.run(
            ['git', '-C', PROJECT_DIR, 'status'],
            capture_output=True,
            text=True,
            timeout=config.timeouts.git_operation,
            check=False
        )
        logger.info("Git status executed")
        return result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
        logger.error("Git status timeout")
        return "Error: Operation timed out"
    except Exception as e:
        return sanitize_error_message(e, "git status")


@mcp.tool()
@git_limiter
def git_commit(message: str, add_all: bool = True) -> str:
    """
    Commit changes with a validated message.
    
    Args:
        message: Commit message (alphanumeric and safe punctuation only)
        add_all: If True, adds all changes before committing
    """
    # Validate commit message
    is_valid, error = validate_commit_message(message)
    if not is_valid:
        logger.warning(f"Invalid commit message rejected: {error}")
        return f"Error: {error}"
    
    try:
        if add_all:
            subprocess.run(
                ['git', '-C', PROJECT_DIR, 'add', '.'],
                check=True,
                timeout=config.timeouts.git_operation,
                capture_output=True
            )
        
        result = subprocess.run(
            ['git', '-C', PROJECT_DIR, 'commit', '-m', message],
            capture_output=True,
            text=True,
            timeout=config.timeouts.git_operation,
            check=False
        )
        
        if result.returncode == 0:
            logger.info(f"Git commit successful: {message[:50]}")
            return result.stdout
        else:
            logger.warning(f"Git commit failed: {result.stderr}")
            return f"Commit failed: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        logger.error("Git commit timeout")
        return "Error: Operation timed out"
    except Exception as e:
        return sanitize_error_message(e, "git commit")


@mcp.tool()
@git_limiter
def graphite_create_stack(message: str) -> str:
    """
    Create a new Graphite stack with validated message.
    
    Args:
        message: Stack message (same validation as commit message)
    """
    # Use same validation as commit message
    is_valid, error = validate_commit_message(message)
    if not is_valid:
        logger.warning(f"Invalid stack message rejected: {error}")
        return f"Error: {error}"
    
    try:
        result = subprocess.run(
            ['gt', '-C', PROJECT_DIR, 'create', '-m', message],
            capture_output=True,
            text=True,
            timeout=15,
            check=False
        )
        
        if result.returncode == 0:
            logger.info(f"Graphite stack created: {message[:50]}")
            return result.stdout
        else:
            logger.warning(f"Graphite stack creation failed: {result.stderr}")
            return result.stderr
            
    except subprocess.TimeoutExpired:
        logger.error("Graphite operation timeout")
        return "Error: Operation timed out"
    except Exception as e:
        return sanitize_error_message(e, "graphite stack")


@mcp.tool()
@git_limiter
def graphite_log() -> str:
    """Get Graphite stack log."""
    try:
        result = subprocess.run(
            ['gt', '-C', PROJECT_DIR, 'log'],
            capture_output=True,
            text=True,
            timeout=config.timeouts.git_operation,
            check=False
        )
        logger.info("Graphite log executed")
        return result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
        logger.error("Graphite log timeout")
        return "Error: Operation timed out"
    except Exception as e:
        return sanitize_error_message(e, "graphite log")


@mcp.tool()
@git_limiter
def auto_commit_and_stack(message: str) -> str:
    """
    One-step automation: add, commit, and create Graphite stack.
    
    Args:
        message: Commit and stack message (validated)
    """
    # Validate message
    is_valid, error = validate_commit_message(message)
    if not is_valid:
        logger.warning(f"Invalid message rejected: {error}")
        return f"Error: {error}"
    
    try:
        # Add all changes
        subprocess.run(
            ['git', '-C', PROJECT_DIR, 'add', '.'],
            check=True,
            timeout=config.timeouts.git_operation,
            capture_output=True
        )
        
        # Commit
        commit_result = subprocess.run(
            ['git', '-C', PROJECT_DIR, 'commit', '-m', message],
            capture_output=True,
            text=True,
            timeout=config.timeouts.git_operation,
            check=True
        )
        
        # Create Graphite stack
        stack_result = subprocess.run(
            ['gt', '-C', PROJECT_DIR, 'create', '-m', message],
            capture_output=True,
            text=True,
            timeout=15,
            check=False
        )
        
        logger.info(f"Auto commit and stack successful: {message[:50]}")
        return f"✅ Success!\n\nCommit:\n{commit_result.stdout}\n\nStack:\n{stack_result.stdout}"
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Auto commit failed: {e}")
        return f"Error: {e.stderr if e.stderr else 'Operation failed'}"
    except subprocess.TimeoutExpired:
        logger.error("Auto commit timeout")
        return "Error: Operation timed out"
    except Exception as e:
        return sanitize_error_message(e, "auto commit and stack")


# ==================== System Maintenance Tools ====================

@mcp.tool()
def system_cleanup(dry_run: bool = True) -> str:
    """
    Clean up Python cache files and __pycache__ directories.
    
    Args:
        dry_run: If True, only shows what would be deleted
    """
    try:
        results = {
            "pyc_files": [],
            "pycache_dirs": [],
            "total_size": 0,
            "dry_run": dry_run
        }
        
        for root, dirs, files in os.walk(PROJECT_DIR):
            # Skip .git and other special directories
            dirs[:] = [d for d in dirs if d not in ['.git', '.venv', 'venv', 'node_modules']]
            
            for file in files:
                if file.endswith('.pyc'):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    results["pyc_files"].append({
                        "path": file_path.replace(PROJECT_DIR, "."),
                        "size": file_size
                    })
                    results["total_size"] += file_size
                    
                    if not dry_run:
                        os.remove(file_path)
                        logger.info(f"Removed .pyc file: {file_path}")
            
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                dir_size = sum(
                    os.path.getsize(os.path.join(dirpath, f))
                    for dirpath, _, filenames in os.walk(pycache_path)
                    for f in filenames
                )
                
                results["pycache_dirs"].append({
                    "path": pycache_path.replace(PROJECT_DIR, "."),
                    "size": dir_size
                })
                results["total_size"] += dir_size
                
                if not dry_run:
                    import shutil
                    shutil.rmtree(pycache_path)
                    logger.info(f"Removed __pycache__: {pycache_path}")
        
        logger.info(f"System cleanup complete: {len(results['pyc_files'])} files, {results['total_size']} bytes")
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error(f"System cleanup failed: {e}", exc_info=True)
        return json.dumps({"error": "Operation failed"})


@mcp.tool()
def scan_secrets(scan_all: bool = True) -> str:
    """
    Scan project files for hardcoded secrets.
    
    Args:
        scan_all: If True, scans all text files; if False, only Python files
    """
    try:
        results = utils.perform_secret_scan(PROJECT_DIR, scan_all)
        logger.info(f"Secret scan complete: {results.get('files_scanned', 0)} files scanned")
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Secret scan failed: {e}", exc_info=True)
        return json.dumps({"error": "Operation failed"})


# ==================== Time Tools ====================

@mcp.tool()
def get_current_time() -> str:
    """Get the current date and time."""
    try:
        time_str = utils.get_current_datetime()
        logger.debug(f"Time requested: {time_str}")
        return time_str
    except Exception as e:
        return sanitize_error_message(e, "get time")


@mcp.tool()
def get_time() -> str:
    """Get the current time in HH:MM:SS format."""
    try:
        time_str = utils.get_current_time_only()
        logger.debug(f"Time requested: {time_str}")
        return time_str
    except Exception as e:
        return sanitize_error_message(e, "get time")


@mcp.tool()
def greet_user(name: str) -> str:
    """Greet a user with their name and the current time."""
    try:
        greeting = utils.format_greeting(name)
        logger.info(f"Greeted user: {name}")
        return greeting
    except ValueError as e:
        logger.warning(f"Invalid name: {e}")
        return "Error: Invalid name format"
    except Exception as e:
        return sanitize_error_message(e, "greet user")


# ==================== Safe Command Execution ====================

@mcp.tool()
@command_limiter
def run_command(command: str) -> str:
    """
    Execute SAFE, READ-ONLY commands with strict validation.
    
    Only allows: ls, pwd, cat, grep, find, wc, head, tail, echo
    NO shell execution, NO piping, NO command chaining.
    
    Args:
        command: Command to execute (must be in whitelist)
    """
    # Validate command
    is_valid, error, parsed_args = validate_command_strict(command)
    
    if not is_valid:
        logger.warning(f"Command rejected: {command} - {error}")
        return f"Error: {error}"
    
    try:
        # Execute with shell=False for security
        result = subprocess.run(
            parsed_args,
            shell=False,  # CRITICAL: Prevents command injection
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
            timeout=config.timeouts.command_execution
        )
        
        output = result.stdout if result.stdout else result.stderr
        logger.info(f"Command executed: {parsed_args[0]}")
        return output if output else "Command executed (no output)"
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timeout: {command}")
        return "Error: Command timed out"
    except Exception as e:
        return sanitize_error_message(e, "command execution")


@mcp.tool()
def check_status() -> str:
    """Check if the server is running."""
    status_info = {
        "status": "running",
        "version": "2.0-security-hardened",
        "base_dir": BASE_DIR,
        "project_dir": PROJECT_DIR,
        "logging": config.logging.level,
        "rate_limiting": "enabled"
    }
    logger.debug("Status check requested")
    return json.dumps(status_info, indent=2)


# ==================== Run Server ====================

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("MCP Server Starting - Security Hardened Edition")
    logger.info(f"BASE_DIR: {BASE_DIR}")
    logger.info(f"PROJECT_DIR: {PROJECT_DIR}")
    logger.info(f"Log Level: {config.logging.level}")
    logger.info(f"Rate Limiting: {config.rate_limit.calls_per_minute} calls/min")
    logger.info("="*60)
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.critical(f"Server error: {e}", exc_info=True)
        raise
