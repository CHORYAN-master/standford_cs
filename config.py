"""
Configuration Management for MCP AI Agent
Centralized configuration using environment variables with validation.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'mcp_server.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


class Config:
    """
    Centralized configuration with validation.
    All settings are loaded from environment variables with sensible defaults.
    """
    
    def __init__(self):
        """Initialize configuration with validation."""
        self._load_and_validate()
    
    def _load_and_validate(self):
        """Load and validate all configuration settings."""
        # Directory paths
        self.BASE_DIR = self._validate_directory(
            os.getenv('BASE_DIR', str(Path.home() / 'Desktop')),
            'BASE_DIR'
        )
        
        self.PROJECT_DIR = self._validate_directory(
            os.getenv('PROJECT_DIR', str(Path.cwd())),
            'PROJECT_DIR'
        )
        
        # File size limits (in bytes)
        self.MAX_FILE_SIZE = self._validate_size(
            os.getenv('MAX_FILE_SIZE_MB', '10'),
            'MAX_FILE_SIZE_MB'
        ) * 1024 * 1024
        
        self.MAX_CONTENT_SIZE = self._validate_size(
            os.getenv('MAX_CONTENT_SIZE_MB', '5'),
            'MAX_CONTENT_SIZE_MB'
        ) * 1024 * 1024
        
        # Security settings
        self.RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
        
        # Log successful initialization
        logger.info("Configuration loaded successfully")
        logger.info(f"BASE_DIR: {self.BASE_DIR}")
        logger.info(f"PROJECT_DIR: {self.PROJECT_DIR}")
        logger.info(f"MAX_FILE_SIZE: {self.MAX_FILE_SIZE / (1024*1024):.1f}MB")
        logger.info(f"MAX_CONTENT_SIZE: {self.MAX_CONTENT_SIZE / (1024*1024):.1f}MB")
    
    def _validate_directory(self, path: str, name: str) -> str:
        """
        Validate that a directory path exists and is accessible.
        
        Args:
            path: Directory path to validate
            name: Configuration variable name (for error messages)
        
        Returns:
            Absolute path as string
        
        Raises:
            ConfigurationError: If directory is invalid
        """
        try:
            abs_path = Path(path).resolve()
            
            if not abs_path.exists():
                logger.warning(f"{name} does not exist: {abs_path}")
                logger.info(f"Creating directory: {abs_path}")
                abs_path.mkdir(parents=True, exist_ok=True)
            
            if not abs_path.is_dir():
                raise ConfigurationError(f"{name} is not a directory: {abs_path}")
            
            # Test write access
            test_file = abs_path / '.mcp_access_test'
            try:
                test_file.touch()
                test_file.unlink()
            except PermissionError:
                raise ConfigurationError(f"No write access to {name}: {abs_path}")
            
            return str(abs_path)
            
        except Exception as e:
            raise ConfigurationError(f"Invalid {name}: {path} - {e}")
    
    def _validate_size(self, size_str: str, name: str) -> int:
        """
        Validate size configuration (in MB).
        
        Args:
            size_str: Size as string (e.g., "10")
            name: Configuration variable name
        
        Returns:
            Size as integer (MB)
        
        Raises:
            ConfigurationError: If size is invalid
        """
        try:
            size = int(size_str)
            if size <= 0:
                raise ValueError("Size must be positive")
            if size > 100:  # Max 100MB
                logger.warning(f"{name} exceeds recommended maximum (100MB): {size}MB")
            return size
        except ValueError as e:
            raise ConfigurationError(f"Invalid {name}: {size_str} - {e}")


class FileConstraints:
    """File operation constraints based on configuration."""
    
    def __init__(self, config: Config):
        self.MAX_FILE_SIZE = config.MAX_FILE_SIZE
        self.MAX_CONTENT_SIZE = config.MAX_CONTENT_SIZE
        self.MAX_MEMORY_BUFFER = 1024 * 1024  # 1MB chunks for reading


class ValidationLimits:
    """Input validation limits."""
    MAX_USERNAME_LENGTH = 100
    MAX_COMMIT_MSG_LENGTH = 500
    MAX_COMMAND_LENGTH = 1000
    MIN_USERNAME_LENGTH = 3


class TimeoutSettings:
    """Operation timeout settings (in seconds)."""
    GIT_OPERATION = 10
    GRAPHITE_OPERATION = 15
    COMMAND_EXECUTION = 10
    FILE_OPERATION = 5


class SecuritySettings:
    """Security-related settings."""
    
    # Allowed file extensions for write operations
    ALLOWED_WRITE_EXTENSIONS = {
        '.txt', '.md', '.json', '.yaml', '.yml',
        '.py', '.js', '.html', '.css', '.xml',
        '.csv', '.log', '.cfg', '.ini', '.toml'
    }
    
    # Forbidden filenames (Windows reserved names)
    FORBIDDEN_FILENAMES = {
        'con', 'prn', 'aux', 'nul',
        'com1', 'com2', 'com3', 'com4',
        'lpt1', 'lpt2', 'lpt3', 'lpt4'
    }
    
    # Safe read-only commands (whitelist)
    SAFE_READ_ONLY_COMMANDS = {
        'ls', 'pwd', 'cat', 'grep', 'find', 'wc',
        'head', 'tail', 'echo', 'git status', 'git log', 'git diff'
    }
    
    # Dangerous patterns to block in commands
    BLOCKED_COMMAND_PATTERNS = [
        ';', '&&', '||', '|', '`', '$', '>', '<',
        '$(', '#{', '\n', '\r', '&', 'rm -rf'
    ]


# Global configuration instance
try:
    config = Config()
    file_constraints = FileConstraints(config)
    logger.info("Configuration initialized successfully")
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    raise
