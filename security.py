"""
Security utilities for input validation and sanitization.
Implements strict validation rules to prevent injection attacks.
"""

import re
import shlex
import logging
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)


# ==================== Command Validation ====================

# Safe read-only commands whitelist
SAFE_READ_ONLY_COMMANDS = {
    'ls', 'pwd', 'cat', 'grep', 'find', 'wc', 'head', 'tail',
    'echo', 'git status', 'git log', 'git diff'
}

# Git commands whitelist
SAFE_GIT_COMMANDS = {
    'git', 'gt'
}


def validate_commit_message(message: str) -> Tuple[bool, str]:
    """
    Validate git commit message for security.
    
    Prevents command injection in commit messages.
    
    Args:
        message: Commit message to validate
        
    Returns:
        (is_valid, error_message)
    
    Examples:
        >>> validate_commit_message("fix: bug")
        (True, "")
        
        >>> validate_commit_message("fix; rm -rf /")
        (False, "Commit message contains forbidden characters")
    """
    if not message or not isinstance(message, str):
        return False, "Commit message must be a non-empty string"
    
    # Length check
    if len(message) > 500:
        return False, "Commit message too long (max 500 characters)"
    
    # Character whitelist - only alphanumeric, spaces, and safe punctuation
    # Allowed: letters, numbers, spaces, -_.,:!?()[]
    if not re.match(r'^[a-zA-Z0-9\s\-_.,!?:()\[\]]+$', message):
        return False, "Commit message contains invalid characters"
    
    # Block command injection patterns
    dangerous_patterns = [
        ';', '&&', '||', '|', '`', '$', '>', '<', 
        '\n', '\r', '$(', '#{', '\\', '"', "'"
    ]
    
    for pattern in dangerous_patterns:
        if pattern in message:
            logger.warning(f"Commit message rejected - contains '{pattern}': {message[:50]}")
            return False, f"Commit message contains forbidden character: {pattern}"
    
    return True, ""


def validate_command_strict(command: str) -> Tuple[bool, str, List[str]]:
    """
    Strictly validate command for security.
    
    Only allows safe, read-only commands with no dangerous operators.
    
    Args:
        command: Shell command to validate
        
    Returns:
        (is_valid, error_message, parsed_args)
        
    Examples:
        >>> validate_command_strict("ls -la")
        (True, "", ["ls", "-la"])
        
        >>> validate_command_strict("ls; rm file")
        (False, "Forbidden character: ;", [])
    """
    if not command or not isinstance(command, str):
        return False, "Command must be non-empty string", []
    
    # Length check
    if len(command) > 1000:
        return False, "Command too long (max 1000 characters)", []
    
    # Parse command safely
    try:
        args = shlex.split(command)
    except ValueError as e:
        logger.warning(f"Command parsing failed: {e}")
        return False, f"Invalid command syntax: {e}", []
    
    if not args:
        return False, "Empty command", []
    
    base_cmd = args[0]
    
    # Whitelist check
    if base_cmd not in SAFE_READ_ONLY_COMMANDS:
        logger.warning(f"Command not in whitelist: {base_cmd}")
        return False, f"Command '{base_cmd}' not allowed", []
    
    # Block dangerous operators and characters
    dangerous_chars = [
        ';', '&&', '||', '|', '`', '$', '>', '<', 
        '$(', '#{', '\n', '\r', '\\\\', '&'
    ]
    
    for char in dangerous_chars:
        if char in command:
            logger.warning(f"Command rejected - contains '{char}': {command[:50]}")
            return False, f"Forbidden character: {char}", []
    
    # Block path traversal in arguments
    for arg in args[1:]:
        if '..' in arg:
            logger.warning(f"Path traversal attempt: {arg}")
            return False, "Path traversal not allowed", []
    
    return True, "", args


def validate_git_command(base_cmd: str) -> bool:
    """
    Validate if command is a safe git command.
    
    Args:
        base_cmd: Base command (e.g., 'git', 'gt')
        
    Returns:
        True if command is safe, False otherwise
    """
    return base_cmd in SAFE_GIT_COMMANDS


# ==================== Filename Validation ====================

ALLOWED_EXTENSIONS = {
    '.txt', '.md', '.json', '.yaml', '.yml',
    '.py', '.js', '.html', '.css', '.xml',
    '.csv', '.log', '.cfg', '.ini', '.toml'
}

FORBIDDEN_FILENAMES = {
    'con', 'prn', 'aux', 'nul',  # Windows reserved
    'com1', 'com2', 'com3', 'com4',
    'lpt1', 'lpt2', 'lpt3', 'lpt4'
}


def validate_filename(file_path: str) -> Tuple[bool, str]:
    """
    Validate filename for security and compatibility.
    
    Prevents:
    - Executable files (.exe, .sh, .bat)
    - Hidden files
    - Reserved names
    - Invalid characters
    
    Args:
        file_path: File path to validate
        
    Returns:
        (is_valid, error_message)
    """
    from pathlib import Path
    
    path = Path(file_path)
    filename = path.name.lower()
    
    # Check extension
    if path.suffix and path.suffix not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{path.suffix}' not allowed"
    
    # Check for reserved names
    stem = path.stem.lower()
    if stem in FORBIDDEN_FILENAMES:
        return False, f"Filename '{stem}' is reserved"
    
    # Check for dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0', '\n']
    for char in dangerous_chars:
        if char in filename:
            return False, f"Filename contains invalid character: {char}"
    
    # Check for hidden files (starting with .)
    if filename.startswith('.'):
        return False, "Hidden files not allowed"
    
    # Check for path traversal
    if '..' in file_path:
        return False, "Path traversal not allowed"
    
    return True, ""


# ==================== Rate Limiting ====================

from time import time
from collections import defaultdict
from functools import wraps


class RateLimiter:
    """
    Rate limiter for function calls.
    
    Prevents abuse by limiting the number of calls per time window.
    """
    
    def __init__(self, max_calls: int, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds (default: 60)
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = defaultdict(list)
    
    def is_allowed(self, key: str) -> Tuple[bool, str]:
        """
        Check if call is allowed.
        
        Args:
            key: Identifier for rate limiting (e.g., function name)
            
        Returns:
            (is_allowed, error_message)
        """
        now = time()
        
        # Remove old calls outside time window
        self.calls[key] = [
            call_time for call_time in self.calls[key]
            if now - call_time < self.time_window
        ]
        
        # Check rate limit
        if len(self.calls[key]) >= self.max_calls:
            remaining_time = int(self.time_window - (now - self.calls[key][0]))
            return False, f"Rate limit exceeded. Try again in {remaining_time}s"
        
        # Record this call
        self.calls[key].append(now)
        
        return True, ""
    
    def __call__(self, func):
        """Decorator to apply rate limiting."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = func.__name__
            
            allowed, error = self.is_allowed(key)
            if not allowed:
                logger.warning(f"Rate limit hit for {key}")
                return f"Error: {error}"
            
            return func(*args, **kwargs)
        
        return wrapper


# ==================== Error Message Sanitization ====================

def sanitize_error_message(error: Exception, operation: str) -> str:
    """
    Sanitize error message for user display.
    
    Removes sensitive information while logging details internally.
    
    Args:
        error: Exception object
        operation: Operation being performed (for context)
        
    Returns:
        Sanitized error message safe for user display
    """
    # Log detailed error internally
    logger.error(f"{operation} failed: {error}", exc_info=True)
    
    # Return generic message to user
    error_type = type(error).__name__
    
    if isinstance(error, FileNotFoundError):
        return "Error: File not found"
    elif isinstance(error, PermissionError):
        return "Error: Access denied"
    elif isinstance(error, ValueError):
        return "Error: Invalid input"
    elif isinstance(error, TimeoutError):
        return "Error: Operation timed out"
    else:
        return f"Error: Unable to complete {operation}"
