import pytest
import os
import time
from pathlib import Path
from werkzeug.datastructures import FileStorage
from tests.test_data_generator import TestDataGenerator

@pytest.mark.file_operations
def test_file_compression(client, auth_headers):
    """Test file compression functionality."""
    generator = TestDataGenerator()
    large_file = generator.generate_text_file(size_kb=10240)  # 10MB file
    
    try:
        # Upload large file
        with open(large_file, 'rb') as f:
            data = {
                'file': (FileStorage(f), 'large.txt'),
                'metadata': generator.generate_metadata()
            }
            response = client.post('/upload', headers=auth_headers, data=data)
        
        assert response.status_code == 200
        
        # Check if file was compressed
        response = client.get('/admin/status', headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        assert any(f['name'] == 'large.txt' and f['compressed'] for f in data['files'])
        
        # Verify compressed file can be downloaded
        response = client.get('/download/large.txt', headers=auth_headers)
        assert response.status_code == 200
    finally:
        generator.cleanup_files([large_file])

@pytest.mark.file_operations
def test_file_encryption(client, auth_headers):
    """Test file encryption functionality."""
    generator = TestDataGenerator()
    sensitive_file = generator.generate_text_file(size_kb=100)
    
    try:
        # Upload sensitive file
        with open(sensitive_file, 'rb') as f:
            data = {
                'file': (FileStorage(f), 'sensitive.txt'),
                'metadata': generator.generate_metadata()
            }
            response = client.post('/upload', headers=auth_headers, data=data)
        
        assert response.status_code == 200
        
        # Check if file was encrypted
        response = client.get('/admin/status', headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        assert any(f['name'] == 'sensitive.txt' and f['encrypted'] for f in data['files'])
        
        # Verify encrypted file can be downloaded
        response = client.get('/download/sensitive.txt', headers=auth_headers)
        assert response.status_code == 200
    finally:
        generator.cleanup_files([sensitive_file])

@pytest.mark.file_operations
def test_file_synchronization(client, auth_headers):
    """Test file synchronization between devices."""
    generator = TestDataGenerator()
    files = generator.generate_file_set(count=3)
    
    try:
        # Upload files
        for file_data in files:
            with open(file_data['path'], 'rb') as f:
                data = {
                    'file': (FileStorage(f), os.path.basename(file_data['path'])),
                    'metadata': file_data['metadata']
                }
                response = client.post('/upload', headers=auth_headers, data=data)
                assert response.status_code == 200
        
        # Trigger synchronization
        response = client.post('/admin/sync', headers=auth_headers)
        assert response.status_code == 200
        
        # Wait for sync to complete
        time.sleep(2)
        
        # Check sync status
        response = client.get('/admin/status', headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        assert data['sync_status']['last_sync'] is not None
        assert data['sync_status']['files_synced'] == len(files)
    finally:
        generator.cleanup_files(files)

@pytest.mark.file_operations
def test_file_versioning(client, auth_headers):
    """Test file versioning functionality."""
    generator = TestDataGenerator()
    test_file = generator.generate_text_file(size_kb=100)
    
    try:
        # Upload initial version
        with open(test_file, 'rb') as f:
            data = {
                'file': (FileStorage(f), 'versioned.txt'),
                'metadata': generator.generate_metadata()
            }
            response = client.post('/upload', headers=auth_headers, data=data)
        assert response.status_code == 200
        
        # Create new version
        new_content = "Updated content"
        with open(test_file, 'w') as f:
            f.write(new_content)
        
        with open(test_file, 'rb') as f:
            data = {
                'file': (FileStorage(f), 'versioned.txt'),
                'metadata': generator.generate_metadata()
            }
            response = client.post('/upload', headers=auth_headers, data=data)
        assert response.status_code == 200
        
        # Check versions
        response = client.get('/versions/versioned.txt', headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        assert len(data['versions']) == 2
        
        # Download specific version
        response = client.get('/download/versioned.txt?version=1', headers=auth_headers)
        assert response.status_code == 200
    finally:
        generator.cleanup_files([test_file])

@pytest.mark.file_operations
def test_file_recovery(client, auth_headers):
    """Test file recovery functionality."""
    generator = TestDataGenerator()
    test_file = generator.generate_text_file(size_kb=100)
    
    try:
        # Upload file
        with open(test_file, 'rb') as f:
            data = {
                'file': (FileStorage(f), 'recoverable.txt'),
                'metadata': generator.generate_metadata()
            }
            response = client.post('/upload', headers=auth_headers, data=data)
        assert response.status_code == 200
        
        # Simulate file corruption
        file_path = Path('uploads/recoverable.txt')
        with open(file_path, 'wb') as f:
            f.write(b'corrupted')
        
        # Attempt to download corrupted file
        response = client.get('/download/recoverable.txt', headers=auth_headers)
        assert response.status_code == 500
        
        # Trigger recovery
        response = client.post('/admin/recover', headers=auth_headers)
        assert response.status_code == 200
        
        # Verify file was recovered
        response = client.get('/download/recoverable.txt', headers=auth_headers)
        assert response.status_code == 200
    finally:
        generator.cleanup_files([test_file]) 