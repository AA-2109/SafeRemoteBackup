import pytest
import os
from datetime import datetime, timedelta

def test_admin_dashboard(client, auth_headers):
    """Test admin dashboard access and content."""
    response = client.get('/admin', headers=auth_headers)
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data
    assert b'System Status' in response.data
    assert b'Storage Usage' in response.data

def test_system_status(client, auth_headers):
    """Test system status information."""
    response = client.get('/admin/status', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    
    # Check required status fields
    assert 'disk_usage' in data
    assert 'memory_usage' in data
    assert 'cpu_usage' in data
    assert 'uptime' in data
    assert 'file_count' in data
    assert 'last_backup' in data

def test_storage_usage(client, auth_headers, sample_file):
    """Test storage usage calculation."""
    # Upload a file
    with open(sample_file, 'rb') as f:
        data = {
            'file': (FileStorage(f), 'test.txt')
        }
        client.post('/upload', headers=auth_headers, data=data)
    
    # Check storage usage
    response = client.get('/admin/status', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    
    assert data['disk_usage']['used'] > 0
    assert data['disk_usage']['total'] > data['disk_usage']['used']
    assert data['file_count'] > 0

def test_backup_status(client, auth_headers):
    """Test backup status information."""
    response = client.get('/admin/status', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    
    assert 'last_backup' in data
    assert 'backup_size' in data
    assert 'backup_status' in data

def test_system_metrics(client, auth_headers):
    """Test system metrics collection."""
    response = client.get('/admin/metrics', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    
    # Check required metrics
    assert 'requests_per_minute' in data
    assert 'average_response_time' in data
    assert 'error_rate' in data
    assert 'active_users' in data

def test_error_logs(client, auth_headers):
    """Test error logs access."""
    response = client.get('/admin/logs', headers=auth_headers)
    assert response.status_code == 200
    assert b'Error Logs' in response.data

def test_user_activity(client, auth_headers):
    """Test user activity tracking."""
    # Perform some actions
    client.get('/expose/', headers=auth_headers)
    client.get('/admin', headers=auth_headers)
    
    # Check activity logs
    response = client.get('/admin/activity', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    
    assert len(data['activities']) > 0
    for activity in data['activities']:
        assert 'timestamp' in activity
        assert 'action' in activity
        assert 'user' in activity

def test_system_health(client, auth_headers):
    """Test system health check."""
    response = client.get('/admin/health', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    
    assert data['status'] == 'healthy'
    assert 'checks' in data
    for check in data['checks']:
        assert 'name' in check
        assert 'status' in check
        assert 'message' in check

def test_system_config(client, auth_headers):
    """Test system configuration access."""
    response = client.get('/admin/config', headers=auth_headers)
    assert response.status_code == 200
    data = response.json
    
    # Check configuration fields
    assert 'max_upload_size' in data
    assert 'compression_threshold' in data
    assert 'sync_interval' in data
    assert 'cache_type' in data
    assert 'session_lifetime' in data

def test_system_maintenance(client, auth_headers):
    """Test system maintenance mode."""
    # Enable maintenance mode
    response = client.post('/admin/maintenance/enable', headers=auth_headers)
    assert response.status_code == 200
    
    # Check that regular access is blocked
    response = client.get('/expose/', headers=auth_headers)
    assert response.status_code == 503
    
    # Disable maintenance mode
    response = client.post('/admin/maintenance/disable', headers=auth_headers)
    assert response.status_code == 200
    
    # Check that access is restored
    response = client.get('/expose/', headers=auth_headers)
    assert response.status_code == 200 