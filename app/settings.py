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
import logging

# Configure logging
logger = logging.getLogger(__name__)

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

def get_optional_env_var(name: str, default: str) -> str:
    """
    Get an optional environment variable with a default value.
    
    Args:
        name (str): The name of the environment variable
        default (str): Default value if not set
        
    Returns:
        str: The value of the environment variable or default
    """
    return os.getenv(name, default)

# Security settings
# These should be set via environment variables in production
STRONG_PASSWORD = get_required_env_var('ADMIN_PASSWORD')
STRONG_SECRET = get_required_env_var('FLASK_SECRET_KEY')

# Application settings
# Maximum file upload size in bytes (default: 100MB)
MAX_UPLOAD_SIZE = int(get_optional_env_var('MAX_UPLOAD_SIZE', '100')) * 1024 * 1024

# Set of all allowed file extensions
ALLOWED_EXTENSIONS = {ext for exts in folders_dict.values() for ext in exts}

# Session lifetime in minutes (default: 30)
SESSION_LIFETIME_MINUTES = int(get_optional_env_var('SESSION_LIFETIME_MINUTES', '30'))

# Cache settings
# Cache type options: simple, filesystem, redis, memcached
CACHE_TYPE = get_optional_env_var('CACHE_TYPE', 'simple')

# Cache timeout in seconds (default: 5 minutes)
CACHE_DEFAULT_TIMEOUT = int(get_optional_env_var('CACHE_DEFAULT_TIMEOUT', '300'))

# File upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE

# Elasticsearch settings
ELASTICSEARCH_HOST = get_optional_env_var('ELASTICSEARCH_HOST', 'localhost')
ELASTICSEARCH_PORT = int(get_optional_env_var('ELASTICSEARCH_PORT', '9200'))

# File synchronization settings
SYNC_INTERVAL = int(get_optional_env_var('SYNC_INTERVAL', '300'))  # 5 minutes
SYNC_FOLDERS = {
    'local': UPLOAD_FOLDER,
    'remote': get_optional_env_var('REMOTE_BACKUP_FOLDER', '/remote/backup')
}

# Compression settings
COMPRESSION_THRESHOLD = int(get_optional_env_var('COMPRESSION_THRESHOLD', '10485760'))  # 10MB
COMPRESSION_METHOD = get_optional_env_var('COMPRESSION_METHOD', '7z')

# File metadata settings
METADATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'metadata.json')
COMMENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'comments.json')

# SSL/TLS settings
SSL_CERT_PATH = get_optional_env_var('SSL_CERT_PATH', 'certs/cert.pem')
SSL_KEY_PATH = get_optional_env_var('SSL_KEY_PATH', 'certs/key.pem')

# Create necessary directories
def create_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        UPLOAD_FOLDER,
        os.path.dirname(METADATA_FILE),
        os.path.dirname(COMMENTS_FILE),
        os.path.dirname(SSL_CERT_PATH),
        os.path.dirname(SSL_KEY_PATH)
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise

# Initialize directories
create_directories()

