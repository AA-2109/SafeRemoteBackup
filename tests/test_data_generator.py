import os
import random
import string
import tempfile
from datetime import datetime, timedelta
from PIL import Image
import io
import fpdf
import wave
import numpy as np

class TestDataGenerator:
    """Generate various types of test data for testing."""
    
    @staticmethod
    def generate_text_file(size_kb=100):
        """Generate a text file with random content."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            content = ''.join(random.choices(string.ascii_letters + string.digits + '\n', k=size_kb * 1024))
            f.write(content.encode())
            return f.name
    
    @staticmethod
    def generate_image(width=800, height=600):
        """Generate a test image file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            # Create a random colored image
            img = Image.new('RGB', (width, height), color=(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            ))
            img.save(f.name, 'JPEG')
            return f.name
    
    @staticmethod
    def generate_pdf(pages=5):
        """Generate a test PDF file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            pdf = fpdf.FPDF()
            for _ in range(pages):
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="Test PDF Content", ln=1, align="C")
            pdf.output(f.name)
            return f.name
    
    @staticmethod
    def generate_audio(duration_seconds=10, sample_rate=44100):
        """Generate a test audio file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            # Generate a simple sine wave
            t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
            audio_data = np.sin(2 * np.pi * 440 * t)
            
            with wave.open(f.name, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            return f.name
    
    @staticmethod
    def generate_code_file(language='python'):
        """Generate a test code file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{language}') as f:
            if language == 'python':
                content = '''def test_function():
    return "Hello, World!"

class TestClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value'''
            elif language == 'javascript':
                content = '''function testFunction() {
    return "Hello, World!";
}

class TestClass {
    constructor() {
        this.value = 42;
    }
    
    getValue() {
        return this.value;
    }
}'''
            f.write(content.encode())
            return f.name
    
    @staticmethod
    def generate_metadata():
        """Generate random metadata for files."""
        return {
            'description': ''.join(random.choices(string.ascii_letters + ' ', k=50)),
            'tags': random.sample(['test', 'document', 'image', 'code', 'audio', 'video'], random.randint(1, 3)),
            'category': random.choice(['work', 'personal', 'project', 'archive']),
            'created_at': (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),
            'modified_at': datetime.now().isoformat(),
            'author': ''.join(random.choices(string.ascii_letters, k=10)),
            'version': f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        }
    
    @staticmethod
    def generate_file_set(count=10):
        """Generate a set of test files with metadata."""
        files = []
        for i in range(count):
            file_type = random.choice(['text', 'image', 'pdf', 'audio', 'code'])
            if file_type == 'text':
                file_path = TestDataGenerator.generate_text_file()
            elif file_type == 'image':
                file_path = TestDataGenerator.generate_image()
            elif file_type == 'pdf':
                file_path = TestDataGenerator.generate_pdf()
            elif file_type == 'audio':
                file_path = TestDataGenerator.generate_audio()
            else:
                file_path = TestDataGenerator.generate_code_file()
            
            files.append({
                'path': file_path,
                'metadata': TestDataGenerator.generate_metadata()
            })
        return files
    
    @staticmethod
    def cleanup_files(files):
        """Clean up generated test files."""
        for file in files:
            if isinstance(file, dict):
                os.unlink(file['path'])
            else:
                os.unlink(file) 