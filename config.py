"""
Configuration management for MCP Server.
Loads settings from environment variables with sensible defaults.
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()


@dataclass
class PathConfig:
    """Path configuration."""
    base_dir: str
    project_dir: str
    
    @classmethod
    def from_env(cls) -> 'PathConfig':
        """Load path configuration from environment."""
        base_dir = os.getenv('BASE_DIR', str(Path.home() / 'Desktop'))
        project_dir = os.getenv('PROJECT_DIR', str(Path.cwd()))
        
        # Validate paths exist
        if not os.path.isdir(base_dir):
            raise ValueError(f"BASE_DIR does not exist: {base_dir}")
        if not os.path.isdir(project_dir):
            raise ValueError(f"PROJECT_DIR does not exist: {project_dir}")
        
        return cls(base_dir=base_dir, project_dir=project_dir)


@dataclass
class FileConstraints:
    """File operation constraints."""
    max_file_size_mb: int
    max_content_size_mb: int
    max_file_size_bytes: int
    max_content_size_bytes: int
    
    @classmethod
    def from_env(cls) -> 'FileConstraints':
        """Load file constraints from environment."""
        max_file_mb = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
        max_content_mb = int(os.getenv('MAX_CONTENT_SIZE_MB', '5'))
        
        return cls(
            max_file_size_mb=max_file_mb,
            max_content_size_mb=max_content_mb,
            max_file_size_bytes=max_file_mb * 1024 * 1024,
            max_content_size_bytes=max_content_mb * 1024 * 1024
        )


@dataclass
class ValidationLimits:
    """Input validation limits."""
    max_username_length: int = 100
    max_commit_msg_length: int = 500
    max_command_length: int = 1000
    max_screenshot_files: int = 1000


@dataclass
class TimeoutSettings:
    """Operation timeout settings."""
    git_operation: int
    command_execution: int
    
    @classmethod
    def from_env(cls) -> 'TimeoutSettings':
        """Load timeout settings from environment."""
        return cls(
            git_operation=int(os.getenv('GIT_OPERATION_TIMEOUT', '10')),
            command_execution=int(os.getenv('COMMAND_EXECUTION_TIMEOUT', '30'))
        )


@dataclass
class RateLimitSettings:
    """Rate limiting settings."""
    calls_per_minute: int
    
    @classmethod
    def from_env(cls) -> 'RateLimitSettings':
        """Load rate limit settings from environment."""
        return cls(
            calls_per_minute=int(os.getenv('RATE_LIMIT_CALLS_PER_MINUTE', '100'))
        )


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str
    log_file: str
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Load logging config from environment."""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE', 'mcp_server.log')
        )


class Config:
    """Main configuration class."""
    
    def __init__(self):
        """Initialize configuration from environment."""
        try:
            self.paths = PathConfig.from_env()
            self.files = FileConstraints.from_env()
            self.validation = ValidationLimits()
            self.timeouts = TimeoutSettings.from_env()
            self.rate_limit = RateLimitSettings.from_env()
            self.logging = LoggingConfig.from_env()
        except Exception as e:
            raise ValueError(f"Configuration error: {e}")
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.logging.level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logging.log_file),
                logging.StreamHandler()
            ]
        )


# Global configuration instance
try:
    config = Config()
    config.setup_logging()
except ValueError as e:
    print(f"ERROR: {e}")
    print("Please create a .env file based on .env.example")
    raise


# Export commonly used values for convenience
BASE_DIR = config.paths.base_dir
PROJECT_DIR = config.paths.project_dir
