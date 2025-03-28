"""
Safe Remote Backup - Configuration Settings

This module contains all configuration settings for the application, including:
- File type organization structure
- TLS cipher configurations
- Security settings
- Application settings
- Cache configurations

The settings are designed to be easily configurable through environment variables
for different deployment environments.

Author: Your Name
Version: 1.0.0
"""

import os
from typing import Dict, Set

# Define folder structure for file organization
# Each key is a folder name, and the value is a set of file extensions
# that should be stored in that folder
folders_dict: Dict[str, Set[str]] = {
    "photos": {"jpg", "jpeg", "png", "gif", "bmp"},
    "videos": {"mp4", "avi", "mkv", "mov"},
    "documents": {"pdf", "doc", "docx", "txt", "xls", "xlsx"},
    "books": {"epub", "fb2"},
    "music": {"mp3", "aac", "m4a"},
    "archives": {"zip", "rar", "tar", "tar.bz", "tar.gz"},
    "unknown_format_files": {}
}

# TLS cipher configuration
# Only modern, secure ciphers are allowed
tls_ciphers = (
    'ECDHE-ECDSA-AES256-GCM-SHA384:'
    'ECDHE-RSA-AES256-GCM-SHA384:'
    'ECDHE-ECDSA-AES128-GCM-SHA256:'
    'ECDHE-RSA-AES128-GCM-SHA256:'
    'ECDHE-ECDSA-AES256-SHA384:'
    'ECDHE-RSA-AES256-SHA384:'
    'TLS_AES_256_GCM_SHA384:'
    'TLS_CHACHA20_POLY1305_SHA256:'
    'TLS_AES_128_GCM_SHA256'
)

def get_required_env_var(name: str) -> str:
    """
    Get a required environment variable or raise an error if not set.
    
    Args:
        name (str): The name of the environment variable
        
    Returns:
        str: The value of the environment variable
        
    Raises:
        ValueError: If the environment variable is not set
    """
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value

# Security settings
# These should be set via environment variables in production
STRONG_PASSWORD = get_required_env_var('ADMIN_PASSWORD')
STRONG_SECRET = get_required_env_var('FLASK_SECRET_KEY')

# Application settings
# Maximum file upload size in bytes (default: 100MB)
MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', '100')) * 1024 * 1024

# Set of all allowed file extensions
ALLOWED_EXTENSIONS = {ext for exts in folders_dict.values() for ext in exts}

# Session lifetime in minutes (default: 30)
SESSION_LIFETIME_MINUTES = int(os.getenv('SESSION_LIFETIME_MINUTES', '30'))

# Cache settings
# Cache type options: simple, filesystem, redis, memcached
CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')

# Cache timeout in seconds (default: 5 minutes)
CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))

