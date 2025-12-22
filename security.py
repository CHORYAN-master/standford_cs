"""
Security utilities for input validation and sanitization.
Implements strict validation for commands, commit messages, and filenames.
"""

import re
import shlex
import logging
from typing import Tuple, List, Optional
from pathlib import Path
from config import ValidationLimits, SecuritySettings

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def validate_commit_message(message: str) -> Tuple[bool, str]:
    """
    Validate git commit message with strict security checks.
    
    Security measures:
    - Length limits
    - Character whitelist (alphanumeric + safe punctuation)
    - Command injection pattern blocking
    
    Args:
        message: Commit message to validate
    
    Returns:
        (is_valid, error_message)
        - is_valid: True if message is safe
        - error_message: Description of validation failure (empty if valid)
    
    Examples:
        >>> validate_commit_message("feat: add new feature")
        (True, "")
        
        >>> validate_commit_message("test; rm -rf /")
        (False, "Commit message contains forbidden characters")
    """
    # Type check
    if not message or not isinstance(message, str):
        return False, "Commit message must be a non-empty string"
    
    # Length validation
    if len(message) > ValidationLimits.MAX_COMMIT_MSG_LENGTH:
        return False, f"Commit message too long (max {ValidationLimits.MAX_COMMIT_MSG_LENGTH} characters)"
    
    # Character whitelist - only allow safe characters
    # Alphanumeric, spaces, and common punctuation: -_.,!?:()[]
    if not re.match(r'^[a-zA-Z0-9\s\-_.,!?:()\[\]]+$', message):
        return False, "Commit message contains invalid characters"
    
    # Block command injection patterns
    for pattern in SecuritySettings.BLOCKED_COMMAND_PATTERNS:
        if pattern in message:
            return False, f"Commit message contains forbidden pattern: '{pattern}'"
    
    return True, ""


def validate_command_strict(command: str) -> Tuple[bool, str, List[str]]:
    """
    Strictly validate shell command for security.
    
    Security measures:
    - Command whitelist (only safe read-only commands)
    - Shell operator blocking (;, &&, ||, |, etc.)
    - Path traversal prevention
    - Proper shell parsing (shlex)
    
    Args:
        command: Shell command string to validate
    
    Returns:
        (is_valid, error_message, parsed_args)
        - is_valid: True if command is safe
        - error_message: Description of validation failure
        - parsed_args: Safely parsed command arguments
    
    Examples:
        >>> validate_command_strict("ls -la")
        (True, "", ["ls", "-la"])
        
        >>> validate_command_strict("ls && rm file")
        (False, "Forbidden character: &&", [])
    """
    # Type and length check
    if not command or not isinstance(command, str):
        return False, "Command must be a non-empty string", []
    
    if len(command) > ValidationLimits.MAX_COMMAND_LENGTH:
        return False, f"Command too long (max {ValidationLimits.MAX_COMMAND_LENGTH} characters)", []
    
    # Block dangerous operators BEFORE parsing
    for char in SecuritySettings.BLOCKED_COMMAND_PATTERNS:
        if char in command:
            logger.warning(f"Blocked command with forbidden pattern: {char}")
            return False, f"Forbidden character: {char}", []
    
    # Parse command safely using shlex
    try:
        parsed_args = shlex.split(command)
    except ValueError as e:
        logger.warning(f"Command parsing failed: {e}")
        return False, f"Invalid command syntax: {e}", []
    
    if not parsed_args:
        return False, "Empty command after parsing", []
    
    # Extract base command
    base_cmd = parsed_args[0]
    
    # Whitelist check - only allow safe read-only commands
    if base_cmd not in SecuritySettings.SAFE_READ_ONLY_COMMANDS:
        logger.warning(f"Blocked non-whitelisted command: {base_cmd}")
        return False, f"Command '{base_cmd}' is not allowed", []
    
    # Check arguments for path traversal
    for arg in parsed_args[1:]:
        if '..' in arg:
            logger.warning(f"Blocked path traversal attempt: {arg}")
            return False, "Path traversal not allowed in arguments", []
        
        # Block absolute paths in arguments (except for git -C)
        if arg.startswith('/') and base_cmd not in ['git']:
            logger.warning(f"Blocked absolute path in argument: {arg}")
            return False, "Absolute paths not allowed in arguments", []
    
    logger.info(f"Command validated: {base_cmd}")
    return True, "", parsed_args


def validate_filename(file_path: str) -> Tuple[bool, str]:
    """
    Validate filename for security and compatibility.
    
    Security measures:
    - Extension whitelist
    - Reserved name blocking (Windows)
    - Dangerous character blocking
    - Hidden file prevention
    
    Args:
        file_path: File path to validate (can be relative)
    
    Returns:
        (is_valid, error_message)
    
    Examples:
        >>> validate_filename("data.json")
        (True, "")
        
        >>> validate_filename("malware.exe")
        (False, "File extension .exe not allowed")
    """
    try:
        path = Path(file_path)
        filename = path.name.lower()
        
        # Check extension whitelist
        if path.suffix not in SecuritySettings.ALLOWED_WRITE_EXTENSIONS:
            return False, f"File extension {path.suffix} not allowed"
        
        # Check for reserved filenames (Windows)
        stem = path.stem.lower()
        if stem in SecuritySettings.FORBIDDEN_FILENAMES:
            return False, f"Filename '{stem}' is reserved"
        
        # Block dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
        for char in dangerous_chars:
            if char in filename:
                return False, f"Filename contains invalid character: '{char}'"
        
        # Block hidden files (starting with .)
        if filename.startswith('.'):
            return False, "Hidden files not allowed"
        
        # Block files with multiple extensions (e.g., file.txt.exe)
        if filename.count('.') > 1:
            return False, "Multiple file extensions not allowed"
        
        return True, ""
        
    except Exception as e:
        logger.error(f"Filename validation error: {e}")
        return False, f"Invalid filename: {e}"


def sanitize_error_message(error: Exception, context: str = "") -> str:
    """
    Sanitize error messages for client display.
    
    Removes sensitive information like:
    - File system paths
    - User names
    - System information
    
    Args:
        error: Exception object
        context: Optional context (e.g., "file operation", "git command")
    
    Returns:
        Sanitized generic error message
    
    Examples:
        >>> sanitize_error_message(FileNotFoundError("/Users/john/file.txt"))
        "File not found"
    """
    error_type = type(error).__name__
    
    # Map specific errors to generic messages
    error_map = {
        'FileNotFoundError': 'File not found',
        'PermissionError': 'Access denied',
        'IsADirectoryError': 'Invalid file path',
        'NotADirectoryError': 'Invalid directory path',
        'UnicodeDecodeError': 'File encoding error',
        'TimeoutExpired': 'Operation timed out',
        'ValueError': 'Invalid input',
        'TypeError': 'Invalid input type',
    }
    
    generic_message = error_map.get(error_type, 'Operation failed')
    
    if context:
        return f"Error: {generic_message} during {context}"
    
    return f"Error: {generic_message}"


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username with security checks.
    
    Args:
        username: Username to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not username or not isinstance(username, str):
        return False, "Username must be a non-empty string"
    
    # Length check
    if not (ValidationLimits.MIN_USERNAME_LENGTH <= len(username) <= ValidationLimits.MAX_USERNAME_LENGTH):
        return False, f"Username must be between {ValidationLimits.MIN_USERNAME_LENGTH}-{ValidationLimits.MAX_USERNAME_LENGTH} characters"
    
    # Character whitelist (alphanumeric, Korean, spaces, basic punctuation)
    if not re.match(r"^[a-zA-Z0-9가-힣\s\-_.,']+$", username):
        return False, "Username contains invalid characters"
    
    # Reserved words
    RESERVED_USERNAMES = ['admin', 'root', 'system', 'administrator']
    if username.lower() in RESERVED_USERNAMES:
        return False, "Username is reserved"
    
    return True, ""


# Example usage and testing
if __name__ == "__main__":
    # Test commit message validation
    print("Testing commit message validation:")
    test_messages = [
        ("feat: add new feature", True),
        ("fix: resolve bug", True),
        ("test; rm -rf /", False),
        ("update && malicious", False),
        ("a" * 600, False),
    ]
    
    for msg, expected in test_messages:
        valid, error = validate_commit_message(msg)
        status = "✅" if valid == expected else "❌"
        print(f"{status} '{msg[:50]}...' -> Valid: {valid}, Error: {error}")
    
    print("\nTesting command validation:")
    test_commands = [
        ("ls -la", True),
        ("cat file.txt", True),
        ("ls && rm file", False),
        ("python -c 'malicious'", False),
        ("rm -rf /", False),
    ]
    
    for cmd, expected in test_commands:
        valid, error, args = validate_command_strict(cmd)
        status = "✅" if valid == expected else "❌"
        print(f"{status} '{cmd}' -> Valid: {valid}, Args: {args}, Error: {error}")
    
    print("\nTesting filename validation:")
    test_files = [
        ("data.json", True),
        ("script.py", True),
        ("malware.exe", False),
        (".hidden", False),
        ("file.txt.exe", False),
    ]
    
    for filename, expected in test_files:
        valid, error = validate_filename(filename)
        status = "✅" if valid == expected else "❌"
        print(f"{status} '{filename}' -> Valid: {valid}, Error: {error}")
