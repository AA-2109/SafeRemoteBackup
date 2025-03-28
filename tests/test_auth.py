import pytest
from flask import session

def test_login_page(client):
    """Test that the login page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login_success(client, auth_headers):
    """Test successful login."""
    response = client.post('/', headers=auth_headers)
    assert response.status_code == 302  # Redirect to /expose/
    assert 'session' in response.headers.get('Set-Cookie', '')

def test_login_failure(client):
    """Test failed login attempt."""
    response = client.post('/', headers={
        'Authorization': 'Basic invalid_credentials'
    })
    assert response.status_code == 401
    assert b'Invalid credentials' in response.data

def test_logout(client, auth_headers):
    """Test logout functionality."""
    # First login
    client.post('/', headers=auth_headers)
    # Then logout
    response = client.get('/logout')
    assert response.status_code == 302  # Redirect to login page
    assert 'session' not in response.headers.get('Set-Cookie', '')

def test_session_expiry(client, auth_headers):
    """Test that sessions expire correctly."""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['expires_at'] = 0  # Set expiry to past
    
    response = client.get('/expose/')
    assert response.status_code == 302  # Redirect to login page

def test_unauthorized_access(client):
    """Test that unauthorized users can't access protected routes."""
    response = client.get('/expose/')
    assert response.status_code == 302  # Redirect to login page

def test_admin_access(client, auth_headers):
    """Test admin access to protected routes."""
    response = client.get('/expose/', headers=auth_headers)
    assert response.status_code == 200
    assert b'Files' in response.data

def test_rate_limiting(client):
    """Test rate limiting on login attempts."""
    for _ in range(5):  # Make 5 failed attempts
        client.post('/', headers={
            'Authorization': 'Basic invalid_credentials'
        })
    
    response = client.post('/', headers={
        'Authorization': 'Basic invalid_credentials'
    })
    assert response.status_code == 429  # Too Many Requests
    assert b'Too many login attempts' in response.data 