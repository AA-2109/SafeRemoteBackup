import pytest
from werkzeug.datastructures import FileStorage

def test_batch_upload(client, auth_headers, sample_file, sample_image, sample_pdf):
    """Test batch file upload."""
    files = [
        ('files', (FileStorage(open(sample_file, 'rb')), 'test.txt')),
        ('files', (FileStorage(open(sample_image, 'rb')), 'test.jpg')),
        ('files', (FileStorage(open(sample_pdf, 'rb')), 'test.pdf'))
    ]
    
    response = client.post('/upload', headers=auth_headers, data=files)
    assert response.status_code == 200
    assert b'Files uploaded successfully' in response.data

def test_batch_delete(client, auth_headers, sample_file, sample_image):
    """Test batch file deletion."""
    # First upload some files
    files = [
        ('files', (FileStorage(open(sample_file, 'rb')), 'test.txt')),
        ('files', (FileStorage(open(sample_image, 'rb')), 'test.jpg'))
    ]
    client.post('/upload', headers=auth_headers, data=files)
    
    # Then delete them in batch
    response = client.post('/batch/delete', headers=auth_headers, json={
        'files': ['test.txt', 'test.jpg']
    })
    assert response.status_code == 200
    assert len(response.json['deleted_files']) == 2
    
    # Verify files are deleted
    for filename in ['test.txt', 'test.jpg']:
        response = client.get(f'/download/{filename}', headers=auth_headers)
        assert response.status_code == 404

def test_batch_download(client, auth_headers, sample_file, sample_image):
    """Test batch file download."""
    # First upload some files
    files = [
        ('files', (FileStorage(open(sample_file, 'rb')), 'test.txt')),
        ('files', (FileStorage(open(sample_image, 'rb')), 'test.jpg'))
    ]
    client.post('/upload', headers=auth_headers, data=files)
    
    # Then download them in batch
    response = client.post('/batch/download', headers=auth_headers, json={
        'files': ['test.txt', 'test.jpg']
    })
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/zip'
    assert response.headers['Content-Disposition'] == 'attachment; filename=files.zip'

def test_batch_share(client, auth_headers, sample_file, sample_image):
    """Test batch file sharing."""
    # First upload some files
    files = [
        ('files', (FileStorage(open(sample_file, 'rb')), 'test.txt')),
        ('files', (FileStorage(open(sample_image, 'rb')), 'test.jpg'))
    ]
    client.post('/upload', headers=auth_headers, data=files)
    
    # Then share them in batch
    response = client.post('/batch/share', headers=auth_headers, json={
        'files': ['test.txt', 'test.jpg']
    })
    assert response.status_code == 200
    assert len(response.json['share_links']) == 2
    
    # Verify share links work
    for link in response.json['share_links']:
        response = client.get(link['url'])
        assert response.status_code == 200

def test_file_search(client, auth_headers, sample_file, sample_image, sample_pdf):
    """Test file search functionality."""
    # Upload some files with different names
    files = [
        ('files', (FileStorage(open(sample_file, 'rb')), 'document.txt')),
        ('files', (FileStorage(open(sample_image, 'rb')), 'image.jpg')),
        ('files', (FileStorage(open(sample_pdf, 'rb')), 'report.pdf'))
    ]
    client.post('/upload', headers=auth_headers, data=files)
    
    # Test search by filename
    response = client.get('/search?q=document', headers=auth_headers)
    assert response.status_code == 200
    assert b'document.txt' in response.data
    
    # Test search by file type
    response = client.get('/search?q=pdf', headers=auth_headers)
    assert response.status_code == 200
    assert b'report.pdf' in response.data
    
    # Test search with no results
    response = client.get('/search?q=nonexistent', headers=auth_headers)
    assert response.status_code == 200
    assert b'No files found' in response.data

def test_file_search_with_metadata(client, auth_headers, sample_file):
    """Test file search with metadata."""
    # Upload a file with metadata
    with open(sample_file, 'rb') as f:
        data = {
            'file': (FileStorage(f), 'test.txt'),
            'metadata': {
                'description': 'Test document',
                'tags': ['test', 'document'],
                'category': 'test'
            }
        }
        client.post('/upload', headers=auth_headers, data=data)
    
    # Test search by metadata
    response = client.get('/search?q=test', headers=auth_headers)
    assert response.status_code == 200
    assert b'test.txt' in response.data
    
    response = client.get('/search?q=document', headers=auth_headers)
    assert response.status_code == 200
    assert b'test.txt' in response.data

def test_file_search_with_filters(client, auth_headers, sample_file, sample_image):
    """Test file search with filters."""
    # Upload files of different types
    files = [
        ('files', (FileStorage(open(sample_file, 'rb')), 'test.txt')),
        ('files', (FileStorage(open(sample_image, 'rb')), 'test.jpg'))
    ]
    client.post('/upload', headers=auth_headers, data=files)
    
    # Test search with file type filter
    response = client.get('/search?q=test&type=image', headers=auth_headers)
    assert response.status_code == 200
    assert b'test.jpg' in response.data
    assert b'test.txt' not in response.data
    
    # Test search with date filter
    response = client.get('/search?q=test&date=2024-01-01', headers=auth_headers)
    assert response.status_code == 200
    assert b'test.txt' in response.data
    assert b'test.jpg' in response.data 