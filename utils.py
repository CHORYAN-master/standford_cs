"""
Utility functions for mathematical operations, string processing, and time handling.
This module provides reusable helper functions for the MCP server.
"""

from datetime import datetime
import os
import re
import logging

logger = logging.getLogger(__name__)


# ==================== Mathematical Operations ====================

def add_numbers(a: int, b: int) -> int:
    """
    Add two numbers together with overflow protection.
    
    Args:
        a, b: Integers to add
        
    Returns:
        Sum of a and b
        
    Raises:
        ValueError: If numbers are too large or result would overflow
    """
    # Prevent integer overflow
    MAX_INT = 10**15
    MIN_INT = -10**15
    
    if not (MIN_INT <= a <= MAX_INT) or not (MIN_INT <= b <= MAX_INT):
        raise ValueError(f"Numbers must be between {MIN_INT} and {MAX_INT}")
    
    result = a + b
    if not (MIN_INT <= result <= MAX_INT):
        raise ValueError("Result exceeds safe integer range")
    
    return result


# ==================== Time Operations ====================

def get_current_datetime() -> str:
    """Get the current date and time in YYYY-MM-DD HH:MM:SS format."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def get_current_time_only() -> str:
    """Get the current time in HH:MM:SS format."""
    now = datetime.now()
    return now.strftime("%H:%M:%S")


# ==================== String Processing ====================

def format_greeting(name: str) -> str:
    """
    Format a personalized greeting with the current time.
    
    Args:
        name: User's name (max 100 characters, alphanumeric and spaces only)
        
    Returns:
        Formatted greeting string
        
    Raises:
        ValueError: If name is invalid or too long
    """
    # Input validation
    if not name or not isinstance(name, str):
        raise ValueError("Name must be a non-empty string")
    
    # Length check
    if len(name) > 100:
        raise ValueError("Name must be 100 characters or less")
    
    # Sanitize: only allow alphanumeric, spaces, Korean, and basic punctuation
    if not re.match(r"^[a-zA-Z0-9가-힣\s\-_.,']+$", name):
        raise ValueError("Name contains invalid characters")
    
    current_time = get_current_time_only()
    return f"Hello, {name}! 현재 시간은 {current_time}입니다."


# ==================== File Path Security ====================

def validate_safe_path(file_path: str, base_dir: str) -> str:
    """
    Validate that a file path is safe and within the allowed directory.
    
    Prevents path traversal attacks (../../../etc/passwd).
    
    Args:
        file_path: The file path to validate
        base_dir: The base directory that files must be within
        
    Returns:
        The absolute, normalized path if safe
        
    Raises:
        ValueError: If path is unsafe or outside base directory
        
    Example:
        >>> validate_safe_path("test.txt", "/home/user/project")
        '/home/user/project/test.txt'
        
        >>> validate_safe_path("../../etc/passwd", "/home/user/project")
        ValueError: Access denied
    """
    # Normalize and resolve the path
    abs_base = os.path.abspath(base_dir)
    abs_path = os.path.abspath(os.path.join(base_dir, file_path))
    
    # Check if path is within base directory (prevent path traversal)
    if not abs_path.startswith(abs_base):
        logger.warning(f"Path traversal attempt: {file_path}")
        raise ValueError(f"Access denied: Path must be within {base_dir}")
    
    return abs_path


# ==================== Secret Detection ====================

def perform_secret_scan(base_dir: str, scan_all: bool = True) -> dict:
    """
    Scan project files for hardcoded secrets and sensitive information.
    
    Detects patterns like API keys, passwords, tokens, and credentials.
    
    Args:
        base_dir: Directory to scan
        scan_all: If True, scan all text files; if False, only Python files
        
    Returns:
        Dictionary with scan results:
        {
            "files_scanned": int,
            "secrets_found": [
                {
                    "file": str,
                    "line": int,
                    "type": str,
                    "severity": str,
                    "context": str
                }
            ],
            "summary": {"high": int, "medium": int, "low": int}
        }
    """
    results = {
        "files_scanned": 0,
        "secrets_found": [],
        "summary": {"high": 0, "medium": 0, "low": 0}
    }
    
    # Secret detection patterns
    secret_patterns = [
        {"name": "OpenAI API Key", "pattern": r'sk-[a-zA-Z0-9]{48}', "severity": "high"},
        {"name": "Anthropic API Key", "pattern": r'AI[a-zA-Z0-9]{40,}', "severity": "high"},
        {"name": "Generic API Key", "pattern": r'api[_-]?key\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "severity": "high"},
        {"name": "Password", "pattern": r'password\s*=\s*["\']([^"\']{3,})["\']', "severity": "high"},
        {"name": "Secret Key", "pattern": r'secret[_-]?key\s*=\s*["\']([^"\']{10,})["\']', "severity": "high"},
        {"name": "AWS Access Key", "pattern": r'AKIA[0-9A-Z]{16}', "severity": "high"},
        {"name": "Private Key Header", "pattern": r'-----BEGIN\s+(RSA\s+)?PRIVATE KEY-----', "severity": "high"},
        {"name": "JWT Token", "pattern": r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', "severity": "medium"},
        {"name": "Database Connection", "pattern": r'(mysql|postgres|mongodb):\/\/[^\s]+', "severity": "medium"},
        {"name": "Generic Token", "pattern": r'token\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "severity": "medium"}
    ]
    
    try:
        for root, dirs, files in os.walk(base_dir):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                # Determine which files to scan
                if scan_all:
                    if not file.endswith(('.py', '.js', '.json', '.yaml', '.yml', '.env', '.txt', '.md', '.sh')):
                        continue
                else:
                    if not file.endswith('.py'):
                        continue
                
                file_path = os.path.join(root, file)
                results["files_scanned"] += 1
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    # Check each pattern
                    for pattern_info in secret_patterns:
                        matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE)
                        
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            context_line = lines[line_num - 1].strip()
                            
                            secret = {
                                "file": file_path.replace(base_dir, "."),
                                "line": line_num,
                                "type": pattern_info["name"],
                                "severity": pattern_info["severity"],
                                "context": context_line[:80] + "..." if len(context_line) > 80 else context_line
                            }
                            
                            results["secrets_found"].append(secret)
                            results["summary"][pattern_info["severity"]] += 1
                            
                            logger.info(f"Secret detected: {pattern_info['name']} in {file_path}:{line_num}")
                            
                except Exception as e:
                    # Skip files that can't be read
                    logger.debug(f"Could not scan {file_path}: {e}")
                    continue
        
        return results
        
    except Exception as e:
        logger.error(f"Secret scan failed: {e}", exc_info=True)
        return {"error": str(e)}
