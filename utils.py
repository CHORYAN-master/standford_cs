"""
Utility functions for mathematical operations, string processing, and time handling.
This module provides reusable helper functions for the MCP server.
"""

from datetime import datetime
import os
import re


# Mathematical Operations
def add_numbers(a: int, b: int) -> int:
    """
    Add two numbers together with overflow protection.
    
    Raises:
        ValueError: If numbers are too large or result would overflow.
    """
    # Prevent integer overflow (Python handles big ints, but set reasonable limits)
    MAX_INT = 10**15
    MIN_INT = -10**15
    
    if not (MIN_INT <= a <= MAX_INT) or not (MIN_INT <= b <= MAX_INT):
        raise ValueError(f"Numbers must be between {MIN_INT} and {MAX_INT}")
    
    result = a + b
    if not (MIN_INT <= result <= MAX_INT):
        raise ValueError("Result exceeds safe integer range")
    
    return result


# Time Operations
def get_current_datetime() -> str:
    """Get the current date and time in YYYY-MM-DD HH:MM:SS format."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def get_current_time_only() -> str:
    """Get the current time in HH:MM:SS format."""
    now = datetime.now()
    return now.strftime("%H:%M:%S")


# String Processing
def format_greeting(name: str) -> str:
    """
    Format a personalized greeting with the current time.
    
    Args:
        name: User's name (max 100 characters, alphanumeric and spaces only)
        
    Raises:
        ValueError: If name is invalid or too long.
    """
    # Input validation
    if not name or not isinstance(name, str):
        raise ValueError("Name must be a non-empty string")
    
    # Length check
    if len(name) > 100:
        raise ValueError("Name must be 100 characters or less")
    
    # Sanitize: only allow alphanumeric, spaces, and basic punctuation
    if not re.match(r"^[a-zA-Z0-9가-힣\s\-_.,']+$", name):
        raise ValueError("Name contains invalid characters")
    
    current_time = get_current_time_only()
    return f"Hello, {name}! 현재 시간은 {current_time}입니다."


# File Path Security
def validate_safe_path(file_path: str, base_dir: str) -> str:
    """
    Validate that a file path is safe and within the allowed directory.
    
    Args:
        file_path: The file path to validate
        base_dir: The base directory that files must be within
        
    Returns:
        The absolute, normalized path if safe
        
    Raises:
        ValueError: If path is unsafe or outside base directory
    """
    # Normalize and resolve the path
    abs_base = os.path.abspath(base_dir)
    abs_path = os.path.abspath(os.path.join(base_dir, file_path))
    
    # Check if path is within base directory (prevent path traversal)
    if not abs_path.startswith(abs_base):
        raise ValueError(f"Access denied: Path must be within {base_dir}")
    
    return abs_path
