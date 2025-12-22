# My First MCP Server - Production-Ready Secure Edition
# 🔒 Enhanced Security: Environment-based configuration, strict validation
# 🛡️ Defense in Depth: Multiple layers of security checks
# 📝 Comprehensive Logging: Detailed audit trail for all operations
# 🚀 Git/Graphite automation with input validation

from mcp.server.fastmcp import FastMCP
import utils
import os
import subprocess
import json
import glob
import logging
from pathlib import Path

# Import configuration and security modules
from config import (
    config, file_constraints, ValidationLimits, 
    TimeoutSettings, SecuritySettings
)
from security import (
    validate_commit_message, validate_command_strict,
    validate_filename, sanitize_error_message
)

# Setup logging
logger = logging.getLogger(__name__)

# Get configuration from environment
BASE_DIR = config.BASE_DIR
PROJECT_DIR = config.PROJECT_DIR

logger.info("=" * 60)
logger.info("MCP Server Starting - Secure Edition")
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"PROJECT_DIR: {PROJECT_DIR}")
logger.info("=" * 60)

# Initialize MCP Server
mcp = FastMCP("My Desktop Assistant - Secure Production Edition")


# ==================== Math Tools ====================

@mcp.tool()
def add_two_numbers(a: int, b: int) -> str:
    """
    Add two numbers together with overflow protection.
    Returns JSON result for consistency.
    """
    try:
        result = utils.add_numbers(a, b)
        logger.info(f"Addition successful: {a} + {b} = {result}")
        return json.dumps({"success": True, "result": result})
    except ValueError as e:
        logger.warning(f"Addition failed - validation error: a={a}, b={b}, error={e}")
        return json.dumps({"success": False, "error": "Invalid input: numbers out of range"})
    except Exception as e:
        logger.error(f"Addition failed - unexpected error: {e}", exc_info=True)
        return json.dumps({"success": False, "error": "Unable to perform calculation"})


# ==================== File System Tools ====================

@mcp.tool()
def list_files(directory: str = ".") -> str:
    """List all files in the given directory (within BASE_DIR)."""
    try:
        safe_path = utils.validate_safe_path(directory, BASE_DIR)
        files = os.listdir(safe_path)
        logger.info(f"Listed directory: {directory} ({len(files)} items)")
        return "\n".join(sorted(files))
    except ValueError as e:
        logger.warning(f"list_files - invalid path: {directory}")
        return "Error: Invalid directory path"
    except FileNotFoundError:
        logger.info(f"list_files - directory not found: {directory}")
        return "Error: Directory not found"
    except PermissionError:
        logger.error(f"list_files - permission denied: {directory}")
        return "Error: Access denied"
    except Exception as e:
        logger.error(f"list_files failed: {e}", exc_info=True)
        return "Error: Unable to list directory"


@mcp.tool()
def read_file(file_path: str) -> str:
    """Read and return the contents of a file (within BASE_DIR)."""
    try:
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        file_size = os.path.getsize(safe_path)
        if file_size > file_constraints.MAX_FILE_SIZE:
            logger.warning(f"read_file - file too large: {file_path} ({file_size} bytes)")
            return f"Error: File size exceeds limit ({file_constraints.MAX_FILE_SIZE / (1024*1024):.0f}MB)"
        
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"File read successfully: {file_path} ({file_size} bytes)")
        return content
        
    except ValueError as e:
        logger.warning(f"read_file - invalid path: {file_path}")
        return "Error: Invalid file path"
    except FileNotFoundError:
        logger.info(f"read_file - file not found: {file_path}")
        return "Error: File not found"
    except PermissionError:
        logger.error(f"read_file - permission denied: {file_path}")
        return "Error: Access denied"
    except UnicodeDecodeError:
        logger.warning(f"read_file - encoding error: {file_path}")
        return "Error: Cannot read file (encoding issue)"
    except Exception as e:
        logger.error(f"read_file failed: {e}", exc_info=True)
        return "Error: Unable to read file"


@mcp.tool()
def write_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """
    Write content to a file (within BASE_DIR).
    Creates the file if it doesn't exist.
    Set overwrite=True to replace existing files.
    """
    try:
        # Validate filename
        is_valid, error = validate_filename(file_path)
        if not is_valid:
            logger.warning(f"write_file - invalid filename: {file_path} - {error}")
            return f"Error: {error}"
        
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        # Content size check
        if len(content) > file_constraints.MAX_CONTENT_SIZE:
            logger.warning(f"write_file - content too large: {len(content)} bytes")
            return f"Error: Content exceeds limit ({file_constraints.MAX_CONTENT_SIZE / (1024*1024):.0f}MB)"
        
        # Check if file exists
        if os.path.exists(safe_path) and not overwrite:
            logger.info(f"write_file - file exists, overwrite=False: {file_path}")
            return "Error: File exists. Set overwrite=True to replace"
        
        # Backup existing file
        if os.path.exists(safe_path):
            import shutil
            backup_path = f"{safe_path}.backup"
            shutil.copy2(safe_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Create directory
        parent_dir = os.path.dirname(safe_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, mode=0o755, exist_ok=True)
            logger.info(f"Created directory: {parent_dir}")
        
        # Write file
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Set permissions (read/write for owner, read for group/others)
        os.chmod(safe_path, 0o644)
        
        logger.info(f"File written successfully: {file_path} ({len(content)} bytes)")
        return f"Successfully wrote to: {file_path}"
        
    except ValueError as e:
        logger.warning(f"write_file - path validation failed: {file_path}")
        return "Error: Invalid file path"
    except PermissionError:
        logger.error(f"write_file - permission denied: {file_path}")
        return "Error: Permission denied"
    except Exception as e:
        logger.error(f"write_file failed: {e}", exc_info=True)
        return "Error: Unable to write file"


@mcp.tool()
def create_directory(dir_path: str) -> str:
    """Create a new directory within BASE_DIR."""
    try:
        safe_path = utils.validate_safe_path(dir_path, BASE_DIR)
        os.makedirs(safe_path, mode=0o755, exist_ok=True)
        logger.info(f"Directory created: {dir_path}")
        return f"Created directory: {dir_path}"
    except ValueError as e:
        logger.warning(f"create_directory - invalid path: {dir_path}")
        return "Error: Invalid directory path"
    except PermissionError:
        logger.error(f"create_directory - permission denied: {dir_path}")
        return "Error: Permission denied"
    except Exception as e:
        logger.error(f"create_directory failed: {e}", exc_info=True)
        return "Error: Unable to create directory"


@mcp.tool()
def delete_file(file_path: str) -> str:
    """Delete a file (within BASE_DIR). Use with caution."""
    try:
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        if not os.path.exists(safe_path):
            logger.info(f"delete_file - file not found: {file_path}")
            return "Error: File not found"
        
        # Log before deletion (audit trail)
        file_size = os.path.getsize(safe_path)
        logger.warning(
            f"FILE DELETION - Path: {file_path}, Size: {file_size} bytes"
        )
        
        os.remove(safe_path)
        logger.info(f"File deleted successfully: {file_path}")
        return f"Deleted: {file_path}"
        
    except ValueError as e:
        logger.warning(f"delete_file - invalid path: {file_path}")
        return "Error: Invalid file path"
    except PermissionError:
        logger.error(f"delete_file - permission denied: {file_path}")
        return "Error: Permission denied"
    except Exception as e:
        logger.error(f"delete_file failed: {e}", exc_info=True)
        return "Error: Unable to delete file"


@mcp.tool()
def move_file(src: str, dst: str) -> str:
    """Move or rename a file within BASE_DIR."""
    try:
        safe_src = utils.validate_safe_path(src, BASE_DIR)
        safe_dst = utils.validate_safe_path(dst, BASE_DIR)
        
        if not os.path.exists(safe_src):
            logger.info(f"move_file - source not found: {src}")
            return "Error: Source file not found"
        
        # Create destination directory if needed
        dst_dir = os.path.dirname(safe_dst)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir, mode=0o755, exist_ok=True)
        
        os.rename(safe_src, safe_dst)
        logger.info(f"File moved: {src} -> {dst}")
        return f"Moved {src} to {dst}"
        
    except ValueError as e:
        logger.warning(f"move_file - invalid path: {src} or {dst}")
        return "Error: Invalid file path"
    except PermissionError:
        logger.error(f"move_file - permission denied")
        return "Error: Permission denied"
    except Exception as e:
        logger.error(f"move_file failed: {e}", exc_info=True)
        return "Error: Unable to move file"


@mcp.tool()
def organize_screenshots(max_files: int = 1000) -> str:
    """
    Find and organize screenshot files on Desktop.
    Moves them to a Screenshots folder with safety limits.
    """
    try:
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
            logger.warning(f"Too many screenshots: {len(screenshot_files)}, limiting to {max_files}")
            results["skipped"] = [os.path.basename(f) for f in screenshot_files[max_files:]]
            screenshot_files = screenshot_files[:max_files]
        
        results["found"] = [os.path.basename(f) for f in screenshot_files]
        
        # Move each file
        for file_path in screenshot_files:
            try:
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
                logger.info(f"Screenshot moved: {filename}")
                
            except Exception as e:
                error_msg = f"{os.path.basename(file_path)}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(f"Failed to move screenshot: {e}")
        
        logger.info(f"Screenshot organization complete: {len(results['moved'])} moved")
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error(f"organize_screenshots failed: {e}", exc_info=True)
        return json.dumps({"error": "Unable to organize screenshots"})


# ==================== Git/Graphite Tools ====================

@mcp.tool()
def git_status() -> str:
    """Get current git status."""
    try:
        result = subprocess.run(
            ['git', '-C', PROJECT_DIR, 'status'],
            capture_output=True,
            text=True,
            timeout=TimeoutSettings.GIT_OPERATION,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("Git status retrieved successfully")
            return result.stdout
        else:
            logger.warning(f"Git status failed: {result.stderr}")
            return result.stderr
            
    except subprocess.TimeoutExpired:
        logger.error("Git status timeout")
        return "Error: Operation timed out"
    except Exception as e:
        logger.error(f"git_status failed: {e}", exc_info=True)
        return "Error: Unable to get git status"


@mcp.tool()
def git_commit(message: str, add_all: bool = True) -> str:
    """
    Commit changes with strict validation.
    
    Args:
        message: Commit message (validated for security)
        add_all: If True, adds all changes before committing
    """
    # Validate commit message
    is_valid, error = validate_commit_message(message)
    if not is_valid:
        logger.warning(f"Invalid commit message rejected: {error}")
        return f"Error: {error}"
    
    try:
        if add_all:
            add_result = subprocess.run(
                ['git', '-C', PROJECT_DIR, 'add', '.'],
                capture_output=True,
                text=True,
                timeout=TimeoutSettings.GIT_OPERATION,
                check=False
            )
            
            if add_result.returncode != 0:
                logger.warning(f"Git add failed: {add_result.stderr}")
                return f"Error: Unable to stage changes - {add_result.stderr}"
        
        # Commit with validated message
        result = subprocess.run(
            ['git', '-C', PROJECT_DIR, 'commit', '-m', message],
            capture_output=True,
            text=True,
            timeout=TimeoutSettings.GIT_OPERATION,
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
        logger.error(f"git_commit failed: {e}", exc_info=True)
        return "Error: Unable to commit changes"


@mcp.tool()
def graphite_create_stack(message: str) -> str:
    """Create a new Graphite stack with validated message."""
    # Use same validation as git_commit
    is_valid, error = validate_commit_message(message)
    if not is_valid:
        logger.warning(f"Invalid stack message rejected: {error}")
        return f"Error: {error}"
    
    try:
        result = subprocess.run(
            ['gt', '-C', PROJECT_DIR, 'create', '-m', message],
            capture_output=True,
            text=True,
            timeout=TimeoutSettings.GRAPHITE_OPERATION,
            check=False
        )
        
        if result.returncode == 0:
            logger.info(f"Graphite stack created: {message[:50]}")
            return result.stdout
        else:
            logger.warning(f"Graphite create failed: {result.stderr}")
            return result.stderr
            
    except subprocess.TimeoutExpired:
        logger.error("Graphite create timeout")
        return "Error: Operation timed out"
    except Exception as e:
        logger.error(f"graphite_create_stack failed: {e}", exc_info=True)
        return "Error: Unable to create stack"


@mcp.tool()
def graphite_log() -> str:
    """Get Graphite stack log."""
    try:
        result = subprocess.run(
            ['gt', '-C', PROJECT_DIR, 'log'],
            capture_output=True,
            text=True,
            timeout=TimeoutSettings.GIT_OPERATION,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("Graphite log retrieved")
            return result.stdout
        else:
            return result.stderr
            
    except subprocess.TimeoutExpired:
        return "Error: Operation timed out"
    except Exception as e:
        logger.error(f"graphite_log failed: {e}", exc_info=True)
        return "Error: Unable to get log"


@mcp.tool()
def auto_commit_and_stack(message: str) -> str:
    """
    One-step automation: add all changes, commit, and create Graphite stack.
    Message is validated before execution.
    """
    # Validate message once for both operations
    is_valid, error = validate_commit_message(message)
    if not is_valid:
        logger.warning(f"Invalid message rejected for auto workflow: {error}")
        return f"Error: {error}"
    
    try:
        # Add all changes
        subprocess.run(
            ['git', '-C', PROJECT_DIR, 'add', '.'],
            capture_output=True,
            timeout=TimeoutSettings.GIT_OPERATION,
            check=True
        )
        
        # Commit
        commit_result = subprocess.run(
            ['git', '-C', PROJECT_DIR, 'commit', '-m', message],
            capture_output=True,
            text=True,
            timeout=TimeoutSettings.GIT_OPERATION,
            check=True
        )
        
        # Create Graphite stack
        stack_result = subprocess.run(
            ['gt', '-C', PROJECT_DIR, 'create', '-m', message],
            capture_output=True,
            text=True,
            timeout=TimeoutSettings.GRAPHITE_OPERATION,
            check=False
        )
        
        logger.info(f"Auto commit and stack successful: {message[:50]}")
        return f"✅ Success!\n\nCommit:\n{commit_result.stdout}\n\nStack:\n{stack_result.stdout}"
        
    except subprocess.TimeoutExpired:
        logger.error("Auto workflow timeout")
        return "Error: Operation timed out"
    except subprocess.CalledProcessError as e:
        logger.error(f"Auto workflow failed: {e}")
        return f"Error during workflow: {e.stderr if e.stderr else str(e)}"
    except Exception as e:
        logger.error(f"auto_commit_and_stack failed: {e}", exc_info=True)
        return "Error: Unable to complete workflow"


# ==================== System Cleanup Tools ====================

@mcp.tool()
def system_cleanup(dry_run: bool = True) -> str:
    """
    Clean up Python cache files and __pycache__ directories.
    Set dry_run=False to actually delete files.
    """
    try:
        results = {
            "pyc_files": [],
            "pycache_dirs": [],
            "total_size": 0,
            "dry_run": dry_run
        }
        
        for root, dirs, files in os.walk(PROJECT_DIR):
            # .pyc files
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
                        logger.info(f"Deleted .pyc file: {file_path}")
            
            # __pycache__ directories
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                dir_size = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, dn, filenames in os.walk(pycache_path)
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
                    logger.info(f"Deleted __pycache__: {pycache_path}")
        
        mode = "dry run" if dry_run else "actual cleanup"
        logger.info(f"System cleanup complete ({mode}): {results['total_size']} bytes")
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error(f"system_cleanup failed: {e}", exc_info=True)
        return json.dumps({"error": "Unable to perform cleanup"})


@mcp.tool()
def scan_secrets(scan_all: bool = True) -> str:
    """
    Scan project files for hardcoded secrets.
    Returns JSON with detected secrets.
    """
    try:
        results = utils.perform_secret_scan(PROJECT_DIR, scan_all)
        
        logger.info(
            f"Secret scan complete: {results.get('files_scanned', 0)} files, "
            f"{len(results.get('secrets_found', []))} secrets found"
        )
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error(f"scan_secrets failed: {e}", exc_info=True)
        return json.dumps({"error": "Unable to scan for secrets"})


# ==================== Time Tools ====================

@mcp.tool()
def get_current_time() -> str:
    """Get the current date and time."""
    try:
        return utils.get_current_datetime()
    except Exception as e:
        logger.error(f"get_current_time failed: {e}")
        return "Error: Unable to get time"


@mcp.tool()
def get_time() -> str:
    """Get the current time in HH:MM:SS format."""
    try:
        return utils.get_current_time_only()
    except Exception as e:
        logger.error(f"get_time failed: {e}")
        return "Error: Unable to get time"


@mcp.tool()
def greet_user(name: str) -> str:
    """Greet a user with their name and the current time."""
    try:
        return utils.format_greeting(name)
    except ValueError as e:
        logger.warning(f"Invalid username: {e}")
        return "Error: Invalid name"
    except Exception as e:
        logger.error(f"greet_user failed: {e}", exc_info=True)
        return "Error: Unable to create greeting"


# ==================== Command Execution (RESTRICTED) ====================

@mcp.tool()
def run_command(command: str) -> str:
    """
    Execute SAFE READ-ONLY commands with strict validation.
    
    Security: Only whitelisted commands allowed, shell=False, input validation.
    Allowed commands: ls, pwd, cat, grep, find, wc, head, tail, echo, git (read-only)
    """
    # Strict validation
    is_valid, error, parsed_args = validate_command_strict(command)
    
    if not is_valid:
        logger.warning(f"Command rejected: {command} - {error}")
        return f"Error: {error}"
    
    try:
        # Execute with shell=False (SECURE)
        result = subprocess.run(
            parsed_args,
            shell=False,  # CRITICAL: Prevents command injection
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
            timeout=TimeoutSettings.COMMAND_EXECUTION
        )
        
        output = result.stdout if result.stdout else result.stderr
        logger.info(f"Command executed: {parsed_args[0]}")
        return output if output else "Command executed successfully (no output)"
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timeout: {command}")
        return "Error: Command timed out"
    except Exception as e:
        logger.error(f"Command execution failed: {e}", exc_info=True)
        return "Error: Unable to execute command"


@mcp.tool()
def check_status() -> str:
    """Check if the server is running."""
    logger.info("Status check performed")
    return "Server is running! 🚀 Secure Production Edition - All security measures active!"


# ==================== Run Server ====================

if __name__ == "__main__":
    logger.info("Starting MCP Server...")
    mcp.run()
