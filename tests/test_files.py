import os
import pytest
from werkzeug.datastructures import FileStorage

def test_file_upload(client, auth_headers, sample_file):
    """Test file upload functionality."""
    with open(sample_file, 'rb') as f:
        data = {
            'file': (FileStorage(f), 'test.txt')
        }
        response = client.post('/upload', headers=auth_headers, data=data)
        assert response.status_code == 200
        assert b'File uploaded successfully' in response.data

def test_file_upload_size_limit(client, auth_headers):
    """Test file upload size limit."""
    # Create a file larger than the limit
    with open('large_file.txt', 'wb') as f:
        f.write(b'0' * (1024 * 1024 + 1))  # 1MB + 1 byte
    
    with open('large_file.txt', 'rb') as f:
        data = {
            'file': (FileStorage(f), 'large_file.txt')
        }
        response = client.post('/upload', headers=auth_headers, data=data)
        assert response.status_code == 413  # Payload Too Large
        assert b'File too large' in response.data
    
    os.remove('large_file.txt')

def test_file_download(client, auth_headers, sample_file):
    """Test file download functionality."""
    # First upload a file
    with open(sample_file, 'rb') as f:
        data = {
            'file': (FileStorage(f), 'test.txt')
        }
        client.post('/upload', headers=auth_headers, data=data)
    
    # Then try to download it
    response = client.get('/download/test.txt', headers=auth_headers)
    assert response.status_code == 200
    assert response.headers['Content-Disposition'] == 'attachment; filename=test.txt'

def test_file_preview(client, auth_headers, sample_image):
    """Test file preview functionality."""
    # Upload an image
    with open(sample_image, 'rb') as f:
        data = {
            'file': (FileStorage(f), 'test.jpg')
        }
        client.post('/upload', headers=auth_headers, data=data)
    
    # Try to preview it
    response = client.get('/preview/test.jpg', headers=auth_headers)
    assert response.status_code == 200
    assert b'Preview' in response.data

def test_file_preview_pdf(client, auth_headers, sample_pdf):
    """Test PDF file preview."""
    # Upload a PDF
    with open(sample_pdf, 'rb') as f:
        data = {
            'file': (FileStorage(f), 'test.pdf')
        }
        client.post('/upload', headers=auth_headers, data=data)
    
    # Try to preview it
    response = client.get('/preview/test.pdf', headers=auth_headers)
    assert response.status_code == 200
    assert b'PDF Preview' in response.data

def test_file_preview_code(client, auth_headers, sample_code_file):
    """Test code file preview with syntax highlighting."""
    # Upload a code file
    with open(sample_code_file, 'rb') as f:
        data = {
            'file': (FileStorage(f), 'test.py')
        }
        client.post('/upload', headers=auth_headers, data=data)
    
    # Try to preview it
    response = client.get('/preview/test.py', headers=auth_headers)
    assert response.status_code == 200
    assert b'def test_function' in response.data
    assert b'highlight' in response.data

def test_file_share(client, auth_headers, sample_file):
    """Test file sharing functionality."""
    # Upload a file
    with open(sample_file, 'rb') as f:
        data = {
            'file': (FileStorage(f), 'test.txt')
        }
        client.post('/upload', headers=auth_headers, data=data)
    
    # Generate share link
    response = client.post('/share/test.txt', headers=auth_headers)
    assert response.status_code == 200
    assert 'share_link' in response.json
    
    # Try to access shared file
    share_link = response.json['share_link']
    response = client.get(share_link)
    assert response.status_code == 200
    assert b'Test file content' in response.data

def test_file_share_password(client, auth_headers, sample_file):
    """Test password-protected file sharing."""
    # Upload a file
    with open(sample_file, 'rb') as f:
        data = {
            'file': (FileStorage(f), 'test.txt')
        }
        client.post('/upload', headers=auth_headers, data=data)
    
    # Generate password-protected share link
    response = client.post('/share/test.txt', headers=auth_headers, json={
        'password': 'test123'
    })
    assert response.status_code == 200
    assert 'share_link' in response.json
    
    # Try to access shared file without password
    share_link = response.json['share_link']
    response = client.get(share_link)
    assert response.status_code == 200
    assert b'Enter Password' in response.data
    
    # Try to access with correct password
    response = client.post(share_link, data={'password': 'test123'})
    assert response.status_code == 200
    assert b'Test file content' in response.data

def test_file_delete(client, auth_headers, sample_file):
    """Test file deletion."""
    # Upload a file
    with open(sample_file, 'rb') as f:
        data = {
            'file': (FileStorage(f), 'test.txt')
        }
        client.post('/upload', headers=auth_headers, data=data)
    
    # Delete the file
    response = client.delete('/delete/test.txt', headers=auth_headers)
    assert response.status_code == 200
    assert b'File deleted successfully' in response.data
    
    # Verify file is deleted
    response = client.get('/download/test.txt', headers=auth_headers)
    assert response.status_code == 404 