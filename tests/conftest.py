import os
import pytest
import tempfile
from flask import Flask
from app.app import create_app
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test configuration
        class TestConfig:
            TESTING = True
            SECRET_KEY = 'test-secret-key'
            UPLOAD_FOLDER = os.path.join(temp_dir, 'uploads')
            MAX_CONTENT_LENGTH = 1000000  # 1MB for testing
            CACHE_TYPE = 'simple'
            CACHE_DEFAULT_TIMEOUT = 300
            ELASTICSEARCH_HOST = 'localhost'
            ELASTICSEARCH_PORT = 9200
            COMPRESSION_THRESHOLD = 1048576  # 1MB for testing
            SYNC_INTERVAL = 60
            SYNC_FOLDERS_LOCAL = os.path.join(temp_dir, 'local')
            SYNC_FOLDERS_REMOTE = os.path.join(temp_dir, 'remote')

        # Create the app with test configuration
        app = create_app(TestConfig)
        
        # Create necessary directories
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['SYNC_FOLDERS_LOCAL'], exist_ok=True)
        os.makedirs(app.config['SYNC_FOLDERS_REMOTE'], exist_ok=True)

        yield app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    return {
        'Authorization': f'Basic {generate_password_hash("admin:admin")}'
    }

@pytest.fixture
def sample_file():
    """Create a sample file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b'Test file content')
        return f.name

@pytest.fixture
def sample_image():
    """Create a sample image file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        # Create a minimal valid JPEG file
        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\xff\xd9')
        return f.name

@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        # Create a minimal valid PDF file
        f.write(b'%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF')
        return f.name

@pytest.fixture
def sample_code_file():
    """Create a sample code file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
        f.write(b'def test_function():\n    return "Hello, World!"')
        return f.name 