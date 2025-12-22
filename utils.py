"""
Utility functions for mathematical operations, string processing, and time handling.
This module provides reusable helper functions for the MCP server.
"""

from datetime import datetime


# Mathematical Operations
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


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
    """Format a personalized greeting with the current time."""
    current_time = get_current_time_only()
    return f"Hello, {name}! 현재 시간은 {current_time}입니다."
