import pytest
import time
import concurrent.futures
import os
from werkzeug.datastructures import FileStorage
from tests.test_data_generator import TestDataGenerator

@pytest.mark.performance
def test_concurrent_uploads(client, auth_headers):
    """Test concurrent file uploads performance."""
    generator = TestDataGenerator()
    files = generator.generate_file_set(count=10)
    
    try:
        start_time = time.time()
        
        def upload_file(file_data):
            with open(file_data['path'], 'rb') as f:
                data = {
                    'file': (FileStorage(f), os.path.basename(file_data['path'])),
                    'metadata': file_data['metadata']
                }
                return client.post('/upload', headers=auth_headers, data=data)
        
        # Upload files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, file_data) for file_data in files]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify all uploads were successful
        assert all(r.status_code == 200 for r in results)
        assert duration < 10  # Should complete within 10 seconds
    except Exception as e:
        pytest.fail(f"Concurrent upload test failed: {str(e)}")
    finally:
        generator.cleanup_files(files)

@pytest.mark.performance
def test_large_file_handling(client, auth_headers):
    """Test handling of large files."""
    generator = TestDataGenerator()
    large_file = generator.generate_text_file(size_kb=10240)  # 10MB file
    
    try:
        # Test upload
        start_time = time.time()
        with open(large_file, 'rb') as f:
            data = {
                'file': (FileStorage(f), 'large.txt'),
                'metadata': generator.generate_metadata()
            }
            response = client.post('/upload', headers=auth_headers, data=data)
        upload_time = time.time() - start_time
        
        assert response.status_code == 200
        assert upload_time < 30  # Should upload within 30 seconds
        
        # Test download
        start_time = time.time()
        response = client.get('/download/large.txt', headers=auth_headers)
        download_time = time.time() - start_time
        
        assert response.status_code == 200
        assert download_time < 20  # Should download within 20 seconds
        
        # Test preview
        start_time = time.time()
        response = client.get('/preview/large.txt', headers=auth_headers)
        preview_time = time.time() - start_time
        
        assert response.status_code == 200
        assert preview_time < 5  # Should preview within 5 seconds
    except Exception as e:
        pytest.fail(f"Large file handling test failed: {str(e)}")
    finally:
        generator.cleanup_files([large_file])

@pytest.mark.performance
def test_search_performance(client, auth_headers):
    """Test search performance with large dataset."""
    generator = TestDataGenerator()
    files = generator.generate_file_set(count=50)  # Generate 50 files
    
    try:
        # Upload files
        for file_data in files:
            with open(file_data['path'], 'rb') as f:
                data = {
                    'file': (FileStorage(f), os.path.basename(file_data['path'])),
                    'metadata': file_data['metadata']
                }
                client.post('/upload', headers=auth_headers, data=data)
        
        # Test search performance
        search_terms = ['test', 'document', 'image', 'code']
        for term in search_terms:
            start_time = time.time()
            response = client.get(f'/search?q={term}', headers=auth_headers)
            duration = time.time() - start_time
            
            assert response.status_code == 200
            assert duration < 1  # Should search within 1 second
    except Exception as e:
        pytest.fail(f"Search performance test failed: {str(e)}")
    finally:
        generator.cleanup_files(files)

@pytest.mark.performance
def test_batch_operations_performance(client, auth_headers):
    """Test performance of batch operations."""
    generator = TestDataGenerator()
    files = generator.generate_file_set(count=20)  # Generate 20 files
    
    try:
        # Upload files
        filenames = []
        for file_data in files:
            with open(file_data['path'], 'rb') as f:
                data = {
                    'file': (FileStorage(f), os.path.basename(file_data['path'])),
                    'metadata': file_data['metadata']
                }
                response = client.post('/upload', headers=auth_headers, data=data)
                filenames.append(os.path.basename(file_data['path']))
        
        # Test batch download
        start_time = time.time()
        response = client.post('/batch/download', headers=auth_headers, json={
            'files': filenames
        })
        download_time = time.time() - start_time
        
        assert response.status_code == 200
        assert download_time < 15  # Should complete within 15 seconds
        
        # Test batch share
        start_time = time.time()
        response = client.post('/batch/share', headers=auth_headers, json={
            'files': filenames
        })
        share_time = time.time() - start_time
        
        assert response.status_code == 200
        assert share_time < 5  # Should complete within 5 seconds
        
        # Test batch delete
        start_time = time.time()
        response = client.post('/batch/delete', headers=auth_headers, json={
            'files': filenames
        })
        delete_time = time.time() - start_time
        
        assert response.status_code == 200
        assert delete_time < 5  # Should complete within 5 seconds
    except Exception as e:
        pytest.fail(f"Batch operations performance test failed: {str(e)}")
    finally:
        generator.cleanup_files(files)

@pytest.mark.performance
def test_system_load(client, auth_headers):
    """Test system performance under load."""
    generator = TestDataGenerator()
    files = generator.generate_file_set(count=100)  # Generate 100 files
    
    try:
        # Simulate concurrent users
        def simulate_user():
            # Upload a file
            file_data = files[0]  # Reuse first file for simplicity
            with open(file_data['path'], 'rb') as f:
                data = {
                    'file': (FileStorage(f), f'user_{time.time()}.txt'),
                    'metadata': file_data['metadata']
                }
                client.post('/upload', headers=auth_headers, data=data)
            
            # Search for files
            client.get('/search?q=test', headers=auth_headers)
            
            # Access admin dashboard
            client.get('/admin', headers=auth_headers)
        
        # Simulate 10 concurrent users
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(simulate_user) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        duration = time.time() - start_time
        
        # Check system status
        response = client.get('/admin/status', headers=auth_headers)
        assert response.status_code == 200
        data = response.json
        
        # Verify system metrics
        assert data['requests_per_minute'] > 0
        assert data['average_response_time'] < 1  # Should be under 1 second
        assert data['error_rate'] < 0.1  # Should be under 10%
        
        # Verify system resources
        assert data['memory_usage']['percent'] < 80  # Should be under 80%
        assert data['cpu_usage']['percent'] < 80  # Should be under 80%
        
        assert duration < 30  # Should complete within 30 seconds
    except Exception as e:
        pytest.fail(f"System load test failed: {str(e)}")
    finally:
        generator.cleanup_files(files)

@pytest.mark.performance
def test_cache_performance(client, auth_headers):
    """Test caching system performance."""
    generator = TestDataGenerator()
    files = generator.generate_file_set(count=5)
    
    try:
        # Upload files
        for file_data in files:
            with open(file_data['path'], 'rb') as f:
                data = {
                    'file': (FileStorage(f), os.path.basename(file_data['path'])),
                    'metadata': file_data['metadata']
                }
                client.post('/upload', headers=auth_headers, data=data)
        
        # Test cache hit performance
        filename = os.path.basename(files[0]['path'])
        
        # First request (cache miss)
        start_time = time.time()
        response = client.get(f'/preview/{filename}', headers=auth_headers)
        first_request_time = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        response = client.get(f'/preview/{filename}', headers=auth_headers)
        second_request_time = time.time() - start_time
        
        assert response.status_code == 200
        assert second_request_time < first_request_time  # Cache hit should be faster
        assert second_request_time < 0.1  # Cache hit should be under 100ms
    except Exception as e:
        pytest.fail(f"Cache performance test failed: {str(e)}")
    finally:
        generator.cleanup_files(files) 