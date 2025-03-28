import pytest
import os
import time
from werkzeug.datastructures import FileStorage
from tests.test_data_generator import TestDataGenerator

@pytest.mark.integration
def test_file_lifecycle(client, auth_headers):
    """Test complete file lifecycle: upload, preview, share, download, delete."""
    # Generate test files
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
        
        # Preview files
        for file_data in files:
            filename = os.path.basename(file_data['path'])
            response = client.get(f'/preview/{filename}', headers=auth_headers)
            assert response.status_code == 200
        
        # Share files
        share_links = []
        for file_data in files:
            filename = os.path.basename(file_data['path'])
            response = client.post(f'/share/{filename}', headers=auth_headers)
            assert response.status_code == 200
            share_links.append(response.json['share_link'])
        
        # Access shared files
        for link in share_links:
            response = client.get(link)
            assert response.status_code == 200
        
        # Download files
        for file_data in files:
            filename = os.path.basename(file_data['path'])
            response = client.get(f'/download/{filename}', headers=auth_headers)
            assert response.status_code == 200
        
        # Delete files
        for file_data in files:
            filename = os.path.basename(file_data['path'])
            response = client.delete(f'/delete/{filename}', headers=auth_headers)
            assert response.status_code == 200
        
        # Verify files are deleted
        for file_data in files:
            filename = os.path.basename(file_data['path'])
            response = client.get(f'/download/{filename}', headers=auth_headers)
            assert response.status_code == 404
    
    finally:
        # Clean up test files
        generator.cleanup_files(files)

@pytest.mark.integration
def test_batch_operations_with_metadata(client, auth_headers):
    """Test batch operations with file metadata."""
    # Generate test files
    generator = TestDataGenerator()
    files = generator.generate_file_set(count=5)
    
    try:
        # Upload files with metadata
        for file_data in files:
            with open(file_data['path'], 'rb') as f:
                data = {
                    'file': (FileStorage(f), os.path.basename(file_data['path'])),
                    'metadata': file_data['metadata']
                }
                response = client.post('/upload', headers=auth_headers, data=data)
                assert response.status_code == 200
        
        # Test batch search with metadata
        for file_data in files:
            # Search by tag
            tag = file_data['metadata']['tags'][0]
            response = client.get(f'/search?q={tag}', headers=auth_headers)
            assert response.status_code == 200
            assert os.path.basename(file_data['path']).encode() in response.data
        
        # Test batch download
        filenames = [os.path.basename(f['path']) for f in files]
        response = client.post('/batch/download', headers=auth_headers, json={
            'files': filenames
        })
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/zip'
        
        # Test batch share
        response = client.post('/batch/share', headers=auth_headers, json={
            'files': filenames
        })
        assert response.status_code == 200
        assert len(response.json['share_links']) == len(files)
        
        # Test batch delete
        response = client.post('/batch/delete', headers=auth_headers, json={
            'files': filenames
        })
        assert response.status_code == 200
        assert len(response.json['deleted_files']) == len(files)
        
        # Verify files are deleted
        for filename in filenames:
            response = client.get(f'/download/{filename}', headers=auth_headers)
            assert response.status_code == 404
    
    finally:
        # Clean up test files
        generator.cleanup_files(files)

@pytest.mark.integration
def test_file_synchronization(client, auth_headers):
    """Test file synchronization between local and remote folders."""
    # Generate test files
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
        
        # Trigger sync
        response = client.post('/sync', headers=auth_headers)
        assert response.status_code == 200
        
        # Wait for sync to complete
        time.sleep(2)
        
        # Check sync status
        response = client.get('/admin/status', headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        assert 'sync_status' in data
        assert data['sync_status']['last_sync'] is not None
        assert data['sync_status']['files_synced'] == len(files)
    
    finally:
        # Clean up test files
        generator.cleanup_files(files)

@pytest.mark.integration
def test_file_compression_and_encryption(client, auth_headers):
    """Test file compression and encryption features."""
    # Generate a large text file
    generator = TestDataGenerator()
    large_file = generator.generate_text_file(size_kb=1024)  # 1MB file
    
    try:
        # Upload large file
        with open(large_file, 'rb') as f:
            data = {
                'file': (FileStorage(f), 'large.txt'),
                'metadata': generator.generate_metadata()
            }
            response = client.post('/upload', headers=auth_headers, data=data)
            assert response.status_code == 200
        
        # Check if file is compressed
        response = client.get('/admin/status', headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        assert data['compressed_files'] > 0
        
        # Download and verify file
        response = client.get('/download/large.txt', headers=auth_headers)
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/octet-stream'
        
        # Check if file is encrypted
        response = client.get('/admin/status', headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        assert data['encrypted_files'] > 0
    
    finally:
        # Clean up test file
        generator.cleanup_files([large_file])

@pytest.mark.integration
def test_error_handling_and_recovery(client, auth_headers):
    """Test error handling and recovery mechanisms."""
    # Generate test files
    generator = TestDataGenerator()
    files = generator.generate_file_set(count=2)
    
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
        
        # Simulate file corruption
        for file_data in files:
            filename = os.path.basename(file_data['path'])
            file_path = os.path.join(client.application.config['UPLOAD_FOLDER'], filename)
            with open(file_path, 'wb') as f:
                f.write(b'corrupted data')
        
        # Try to download corrupted files
        for file_data in files:
            filename = os.path.basename(file_data['path'])
            response = client.get(f'/download/{filename}', headers=auth_headers)
            assert response.status_code == 500
        
        # Trigger recovery
        response = client.post('/admin/recover', headers=auth_headers)
        assert response.status_code == 200
        
        # Verify recovery
        for file_data in files:
            filename = os.path.basename(file_data['path'])
            response = client.get(f'/download/{filename}', headers=auth_headers)
            assert response.status_code == 200
    
    finally:
        # Clean up test files
        generator.cleanup_files(files) 