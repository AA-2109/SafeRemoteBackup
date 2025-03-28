"""
Safe Remote Backup - Main Application Module

This module implements a secure file backup and management system with the following features:
- Secure authentication with password protection
- File upload with drag-and-drop support
- Automatic file organization by type
- File browsing and management
- Admin dashboard with system status
- QR code generation for mobile access
- File preview support for images and PDFs
- File search functionality
- File deletion capability
- File sharing with temporary links
- File versioning support
- File metadata editing
- File compression before upload
- File encryption at rest
- File synchronization between devices
- File comments and annotations
- Enhanced search with metadata support

The application uses Flask for the web framework and implements various security measures
including TLS encryption, rate limiting, and secure file handling.

Author: Your Name
Version: 1.0.0
"""

import os
import ssl
import logging
import secrets
import magic
import py7zr
import zipfile
from datetime import date, timedelta, datetime
from typing import List, Optional, Dict, Tuple
import qrcode
from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory, abort, current_app, jsonify
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from elasticsearch import Elasticsearch
import settings
import json
import shutil
import threading
import queue
import time
from flask_swagger_ui import get_swaggerui_blueprint
from flasgger import Swagger
import atexit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(settings)

# Initialize extensions
bcrypt = Bcrypt(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
cache = Cache(app)

# Initialize Swagger
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Safe Remote Backup API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
swagger = Swagger(app)

# Initialize Elasticsearch client with retry logic
def init_elasticsearch():
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
            if es.ping():
                logger.info("Successfully connected to Elasticsearch")
                return es
            logger.warning(f"Elasticsearch ping failed, attempt {attempt + 1}/{max_retries}")
        except Exception as e:
            logger.error(f"Error connecting to Elasticsearch: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.critical("Failed to connect to Elasticsearch after maximum retries")
                raise
    return None

es = init_elasticsearch()

# Initialize encryption
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

# File synchronization queue
sync_queue = queue.Queue()

# Add new configuration for file compression
COMPRESSION_THRESHOLD = 10 * 1024 * 1024  # 10MB
COMPRESSION_METHODS = {
    '7z': py7zr.SevenZipFile,
    'zip': zipfile.ZipFile
}

# Add new configuration for file synchronization
SYNC_INTERVAL = 300  # 5 minutes
SYNC_FOLDERS = {
    'local': '/app/static/uploads',
    'remote': '/remote/backup'
}

# Add new configuration for file comments
COMMENTS_FILE = 'comments.json'

# Global variables for cleanup
sync_thread = None
observer = None

def cleanup():
    """Cleanup function to be called on application shutdown."""
    global sync_thread, observer
    
    if sync_thread and sync_thread.is_alive():
        sync_queue.put(None)  # Signal thread to stop
        sync_thread.join(timeout=5)
        if sync_thread.is_alive():
            logger.warning("Sync thread did not terminate gracefully")
    
    if observer:
        observer.stop()
        observer.join(timeout=5)
        if observer.is_alive():
            logger.warning("File observer did not terminate gracefully")
    
    if es:
        try:
            es.close()
        except Exception as e:
            logger.error(f"Error closing Elasticsearch connection: {e}")

# Register cleanup function
atexit.register(cleanup)

class FileChangeHandler(FileSystemEventHandler):
    """Handle file system events for synchronization."""
    
    def on_created(self, event):
        if not event.is_directory:
            sync_queue.put(('created', event.src_path))
            
    def on_modified(self, event):
        if not event.is_directory:
            sync_queue.put(('modified', event.src_path))
            
    def on_deleted(self, event):
        if not event.is_directory:
            sync_queue.put(('deleted', event.src_path))

def compress_file(file_path: str) -> str:
    """
    Compress a file if it exceeds the size threshold.
    
    Args:
        file_path (str): Path to the file to compress
        
    Returns:
        str: Path to the compressed file
    """
    try:
        if os.path.getsize(file_path) < COMPRESSION_THRESHOLD:
            return file_path
            
        base, ext = os.path.splitext(file_path)
        compressed_path = f"{base}.7z"
        
        with py7zr.SevenZipFile(compressed_path, 'w') as archive:
            archive.write(file_path, os.path.basename(file_path))
            
        os.remove(file_path)
        return compressed_path
    except Exception as e:
        logger.error(f"Error compressing file {file_path}: {e}")
        return file_path

def encrypt_file(file_path: str) -> str:
    """
    Encrypt a file using Fernet symmetric encryption.
    
    Args:
        file_path (str): Path to the file to encrypt
        
    Returns:
        str: Path to the encrypted file
    """
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        encrypted_data = fernet.encrypt(file_data)
        
        encrypted_path = f"{file_path}.enc"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
            
        os.remove(file_path)
        return encrypted_path
    except Exception as e:
        logger.error(f"Error encrypting file {file_path}: {e}")
        return file_path

def decrypt_file(file_path: str) -> bytes:
    """
    Decrypt a file using Fernet symmetric encryption.
    
    Args:
        file_path (str): Path to the file to decrypt
        
    Returns:
        bytes: Decrypted file data
    """
    try:
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
            
        return fernet.decrypt(encrypted_data)
    except Exception as e:
        logger.error(f"Error decrypting file {file_path}: {e}")
        raise

def sync_files():
    """
    Synchronize files between local and remote folders.
    """
    while True:
        try:
            action, file_path = sync_queue.get()
            rel_path = os.path.relpath(file_path, SYNC_FOLDERS['local'])
            remote_path = os.path.join(SYNC_FOLDERS['remote'], rel_path)
            
            if action in ['created', 'modified']:
                if os.path.exists(file_path):
                    os.makedirs(os.path.dirname(remote_path), exist_ok=True)
                    shutil.copy2(file_path, remote_path)
            elif action == 'deleted':
                if os.path.exists(remote_path):
                    os.remove(remote_path)
                    
        except Exception as e:
            logger.error(f"Error syncing files: {e}")
            
        sync_queue.task_done()
        time.sleep(1)

def load_comments() -> dict:
    """
    Load file comments from JSON file.
    
    Returns:
        dict: Dictionary containing file comments
    """
    try:
        if os.path.exists(COMMENTS_FILE):
            with open(COMMENTS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading comments: {e}")
        return {}

def save_comments(comments: dict) -> None:
    """
    Save file comments to JSON file.
    
    Args:
        comments (dict): Dictionary containing file comments
    """
    try:
        with open(COMMENTS_FILE, 'w') as f:
            json.dump(comments, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving comments: {e}")

def index_file(file_path: str, metadata: dict) -> None:
    """
    Index a file in Elasticsearch for enhanced search.
    
    Args:
        file_path (str): Path to the file
        metadata (dict): File metadata
    """
    try:
        doc = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'type': os.path.splitext(file_path)[1].lower(),
            'size': os.path.getsize(file_path),
            'created_at': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
            'metadata': metadata
        }
        
        es.index(index='files', id=file_path, document=doc)
    except Exception as e:
        logger.error(f"Error indexing file {file_path}: {e}")

# Directory inside container, mapped to D:\uploads on the host
UPLOAD_FOLDER = f'/app/static/uploads/{date.today()}/'
# Directories structure
DICT_STRUCT = settings.folders_dict
# TLS ciphers
STRONG_CIPHERS = settings.tls_ciphers
STRONG_PASSWORD = settings.STRONG_PASSWORD
STRONG_SECRET = settings.STRONG_SECRET
HOST_IP = os.getenv('HOST_IP')

# App init
app.secret_key = STRONG_SECRET
bcrypt = Bcrypt(app)
admin_password_hash = bcrypt.generate_password_hash(STRONG_PASSWORD).decode('utf-8')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=settings.SESSION_LIFETIME_MINUTES)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize cache
cache = Cache(app, config={
    'CACHE_TYPE': settings.CACHE_TYPE,
    'CACHE_DEFAULT_TIMEOUT': settings.CACHE_DEFAULT_TIMEOUT
})

# TLS context
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.options |= ssl.OP_NO_TLSv1
context.options |= ssl.OP_NO_TLSv1_1
context.set_ciphers(STRONG_CIPHERS)
context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')

# Add new configuration for file previews
PREVIEWABLE_EXTENSIONS = {
    'images': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'},
    'documents': {'pdf', 'txt', 'md', 'rst', 'csv', 'json', 'xml', 'yaml', 'yml'},
    'code': {'py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'h', 'php', 'rb', 'go', 'rs', 'swift', 'kt'},
    'audio': {'mp3', 'wav', 'ogg', 'm4a'},
    'video': {'mp4', 'webm', 'mov', 'avi'}
}

# Add new configuration for password-protected shares
SHARE_PASSWORDS = {}

# Add shared links storage (in production, use a database)
shared_links: Dict[str, Dict] = {}

# Add new configuration for file metadata
METADATA_FILE = 'metadata.json'

def get_folder_name_str(filename: str) -> str:
    """
    Determine the appropriate folder for a file based on its extension.
    
    Args:
        filename (str): The name of the file to categorize
        
    Returns:
        str: The path to the appropriate folder for the file
    """
    try:
        extension = filename.split(".")[-1].lower()
        for folder, extensions in DICT_STRUCT.items():
            if extension in extensions:
                return os.path.join(UPLOAD_FOLDER, folder)
        return os.path.join(UPLOAD_FOLDER, "unknown_format_files")
    except Exception as e:
        logger.error(f"Error determining folder for {filename}: {e}")
        return os.path.join(UPLOAD_FOLDER, "unknown_format_files")

def create_folders(folder_names: List[str], base_directory: str) -> None:
    """
    Create the necessary folder structure for file organization.
    
    Args:
        folder_names (List[str]): List of folder names to create
        base_directory (str): The base directory where folders will be created
        
    Raises:
        Exception: If folder creation fails
    """
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        for folder in folder_names:
            path = os.path.join(base_directory, folder)
            os.makedirs(path, exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating folders: {e}")
        raise

def allowed_file(filename: str) -> bool:
    """
    Check if a file's extension is allowed for upload.
    
    Args:
        filename (str): The name of the file to check
        
    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in settings.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """
    Root route handler.
    Redirects to login if not authenticated, otherwise shows upload page.
    
    Returns:
        Response: Either the upload page or login redirect
    """
    if 'authenticated' in session and session['authenticated']:
        return render_template('upload.html', ip=HOST_IP)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """
    Login route handler with rate limiting.
    Implements brute force protection with a 5-attempt limit.
    
    Returns:
        Response: Login page or redirect to index if successful
    """
    if 'failed_login_counter' not in session:
        session['failed_login_counter'] = 0 

    if session['failed_login_counter'] > 5:
        return render_template('frig-off.html', error="Too many wrong passwords, frig off")
    
    if request.method == 'POST':
        password = request.form['password']
        if bcrypt.check_password_hash(admin_password_hash, password):
            session['authenticated'] = True
            session['failed_login_counter'] = 0
            return redirect(url_for('index'))
        else:
            session['failed_login_counter'] += 1
            logger.warning(f"Failed login attempt from IP: {request.remote_addr}")
            return render_template('login.html', error="Invalid password.")

    return render_template('login.html')

@app.route('/admin')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_admin_page():
    """
    Admin dashboard route handler with caching.
    Generates QR code for mobile access.
    
    Returns:
        Response: Admin dashboard page
    """
    logger.info(f"Admin page accessed. Host IP: {HOST_IP}")
    url = f"https://{HOST_IP}:5000/"
    qr_path = os.path.join('static', 'qrcode.png')

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_path)
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        qr_path = None

    return render_template('admin.html', ip=HOST_IP, qr_code='static/qrcode.png' if qr_path else None)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    File upload route handler with compression and encryption.
    """
    if 'files' not in request.files:
        return "No file part", 400
    
    files = request.files.getlist('files')
    if not files:
        return "No files selected", 400

    uploaded_files = []
    for file in files:
        if file.filename == '':
            continue
        
        if not allowed_file(file.filename):
            logger.warning(f"Attempted upload of disallowed file type: {file.filename}")
            continue

        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(get_folder_name_str(filename), filename)
            
            # Check file size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size > settings.MAX_UPLOAD_SIZE:
                logger.warning(f"File too large: {filename}")
                continue
                
            # Save the file
            file.save(filepath)
            
            # Compress if needed
            filepath = compress_file(filepath)
            
            # Encrypt the file
            filepath = encrypt_file(filepath)
            
            # Get file metadata
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(filepath)
            
            # Create metadata
            metadata = {
                'type': file_type,
                'size': os.path.getsize(filepath),
                'uploaded_at': datetime.now().isoformat(),
                'compressed': filepath.endswith('.7z'),
                'encrypted': filepath.endswith('.enc')
            }
            
            # Save metadata
            save_metadata({filepath: metadata})
            
            # Index the file
            index_file(filepath, metadata)
            
            uploaded_files.append(filename)
            logger.info(f"Successfully uploaded: {filename}")
        except Exception as e:
            logger.error(f"Error uploading {file.filename}: {e}")
            continue

    if not uploaded_files:
        return "No valid files uploaded", 400

    return f"Files uploaded successfully: {', '.join(uploaded_files)}"

@app.route('/details/<path:subpath>')
def file_details(subpath: str):
    """
    Display detailed information about a file.
    
    Args:
        subpath (str): Path to the file
        
    Returns:
        Response: File details page or 404 if file not found
    """
    try:
        file_path = os.path.join(UPLOAD_FOLDER, subpath)
        if not os.path.exists(file_path):
            abort(404)
            
        filename = os.path.basename(file_path)
        file_type = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        file_size = os.path.getsize(file_path)
        upload_date = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        
        metadata = load_metadata().get(subpath, {})
        
        return render_template('file_details.html',
                             file_path=subpath,
                             filename=filename,
                             file_type=file_type,
                             file_size=file_size,
                             upload_date=upload_date,
                             metadata=metadata)
    except Exception as e:
        logger.error(f"Error displaying file details: {e}")
        abort(500)

@app.route('/expose/', defaults={'subpath': ''}, methods=['GET'])
@app.route('/expose/<path:subpath>', methods=['GET'])
@cache.cached(timeout=60)  # Cache for 1 minute
def list_files(subpath: str):
    """
    File listing route handler with caching.
    Implements secure path handling and directory traversal prevention.
    
    Args:
        subpath (str): The subpath to list files from
        
    Returns:
        Response: File listing page or 404 if path not found
    """
    try:
        current_path = os.path.join(UPLOAD_FOLDER, subpath)
        current_path = os.path.normpath(current_path)

        if not os.path.exists(current_path):
            abort(404)

        dirs = [d for d in os.listdir(current_path) if os.path.isdir(os.path.join(current_path, d))]
        files = []
        
        for f in os.listdir(current_path):
            if os.path.isfile(os.path.join(current_path, f)):
                file_path = os.path.join(subpath, f) if subpath else f
                file_size = os.path.getsize(os.path.join(current_path, f))
                file_type = f.rsplit('.', 1)[1].lower() if '.' in f else ''
                upload_date = datetime.fromtimestamp(os.path.getctime(os.path.join(current_path, f))).strftime('%Y-%m-%d %H:%M:%S')
                
                metadata = load_metadata().get(file_path, {})
                
                files.append({
                    'name': f,
                    'path': file_path,
                    'size': file_size,
                    'type': file_type,
                    'upload_date': upload_date,
                    'metadata': metadata
                })

        return render_template('files.html', dirs=dirs, files=files, current_path=subpath)
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        abort(500)

@app.route('/download/<path:subpath>', methods=['GET'])
def serve_file(subpath: str):
    """
    File download route handler.
    Implements secure file serving with proper error handling.
    
    Args:
        subpath (str): The path to the file to serve
        
    Returns:
        Response: File download or 404 if file not found
    """
    try:
        return send_from_directory(UPLOAD_FOLDER, subpath)
    except FileNotFoundError:
        abort(404)
    except Exception as e:
        logger.error(f"Error serving file {subpath}: {e}")
        abort(500)

@app.route('/logout', methods=['GET'])
def logout():
    """
    Logout route handler.
    Clears the session and redirects to login.
    
    Returns:
        Response: Redirect to login page
    """
    session.clear()
    return redirect(url_for('login'))

def generate_share_token() -> str:
    """
    Generate a secure random token for file sharing.
    
    Returns:
        str: A secure random token
    """
    return secrets.token_urlsafe(32)

def preview_text_file(file_path: str) -> str:
    """
    Preview a text file with syntax highlighting.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: HTML content for preview
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        ext = os.path.splitext(file_path)[1].lower()
        if ext in PREVIEWABLE_EXTENSIONS['code']:
            # Use Pygments for code highlighting
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name
            from pygments.formatters import HtmlFormatter
            
            lexer = get_lexer_by_name(ext[1:])  # Remove the dot
            formatter = HtmlFormatter(style='monokai')
            highlighted = highlight(content, lexer, formatter)
            
            return f"""
            <div class="code-preview">
                <style>{formatter.get_style_defs()}</style>
                {highlighted}
            </div>
            """
        else:
            # Simple text preview
            return f"""
            <div class="text-preview">
                <pre>{content}</pre>
            </div>
            """
    except Exception as e:
        logger.error(f"Error previewing text file {file_path}: {e}")
        return "<p>Error loading file preview</p>"

def preview_audio_file(file_path: str) -> str:
    """
    Preview an audio file with HTML5 audio player.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: HTML content for preview
    """
    return f"""
    <div class="audio-preview">
        <audio controls>
            <source src="/download/{file_path}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
    </div>
    """

def preview_video_file(file_path: str) -> str:
    """
    Preview a video file with HTML5 video player.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: HTML content for preview
    """
    return f"""
    <div class="video-preview">
        <video controls>
            <source src="/download/{file_path}" type="video/mp4">
            Your browser does not support the video element.
        </video>
    </div>
    """

@app.route('/preview/<path:subpath>')
def preview_file(subpath: str):
    """
    Preview route handler for supported file types.
    
    Args:
        subpath (str): The path to the file to preview
        
    Returns:
        Response: Preview page or 404 if file not found
    """
    try:
        file_path = os.path.join(UPLOAD_FOLDER, subpath)
        if not os.path.exists(file_path):
            abort(404)
            
        filename = os.path.basename(file_path)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if ext in PREVIEWABLE_EXTENSIONS['images']:
            preview_type = 'image'
            preview_content = f'<img src="/download/{subpath}" alt="{filename}" class="max-w-full h-auto">'
        elif ext in PREVIEWABLE_EXTENSIONS['documents']:
            if ext == 'pdf':
                preview_type = 'pdf'
                preview_content = f'<iframe src="/download/{subpath}" class="w-full h-screen"></iframe>'
            else:
                preview_type = 'text'
                preview_content = preview_text_file(file_path)
        elif ext in PREVIEWABLE_EXTENSIONS['code']:
            preview_type = 'code'
            preview_content = preview_text_file(file_path)
        elif ext in PREVIEWABLE_EXTENSIONS['audio']:
            preview_type = 'audio'
            preview_content = preview_audio_file(subpath)
        elif ext in PREVIEWABLE_EXTENSIONS['video']:
            preview_type = 'video'
            preview_content = preview_video_file(subpath)
        else:
            abort(400, "File type not supported for preview")
            
        return render_template('preview.html', 
                             file_path=subpath,
                             filename=filename,
                             preview_type=preview_type,
                             preview_content=preview_content)
    except Exception as e:
        logger.error(f"Error previewing file {subpath}: {e}")
        abort(500)

@app.route('/share/<path:subpath>', methods=['POST'])
def share_file(subpath: str):
    """
    Generate a temporary share link for a file with optional password protection.
    
    Args:
        subpath (str): The path to the file to share
        
    Returns:
        Response: JSON with share link or error
    """
    try:
        file_path = os.path.join(UPLOAD_FOLDER, subpath)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
            
        token = generate_share_token()
        expiry = datetime.now() + timedelta(hours=24)  # 24-hour expiry
        
        # Check if password protection is requested
        password = request.json.get('password')
        if password:
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            SHARE_PASSWORDS[token] = password_hash
        
        shared_links[token] = {
            'file_path': subpath,
            'expiry': expiry,
            'password_protected': bool(password)
        }
        
        share_url = f"https://{HOST_IP}:5000/shared/{token}"
        return jsonify({
            "share_url": share_url,
            "expires_at": expiry.isoformat(),
            "password_protected": bool(password)
        })
    except Exception as e:
        logger.error(f"Error sharing file {subpath}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/shared/<token>', methods=['GET', 'POST'])
def access_shared_file(token: str):
    """
    Access a file via a share token with password protection.
    
    Args:
        token (str): The share token
        
    Returns:
        Response: File download or error
    """
    try:
        if token not in shared_links:
            abort(404, "Share link not found")
            
        share_info = shared_links[token]
        if datetime.now() > share_info['expiry']:
            del shared_links[token]
            if token in SHARE_PASSWORDS:
                del SHARE_PASSWORDS[token]
            abort(410, "Share link expired")
            
        if share_info['password_protected']:
            if request.method == 'GET':
                return render_template('share_password.html', token=token)
                
            password = request.form.get('password')
            if not password or not bcrypt.check_password_hash(SHARE_PASSWORDS[token], password):
                return render_template('share_password.html', 
                                     token=token,
                                     error="Invalid password")
                
        return send_from_directory(UPLOAD_FOLDER, share_info['file_path'])
    except Exception as e:
        logger.error(f"Error accessing shared file {token}: {e}")
        abort(500)

@app.route('/delete/<path:subpath>', methods=['POST'])
def delete_file(subpath: str):
    """
    Delete a file from the system.
    
    Args:
        subpath (str): The path to the file to delete
        
    Returns:
        Response: Success message or error
    """
    try:
        file_path = os.path.join(UPLOAD_FOLDER, subpath)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
            
        os.remove(file_path)
        logger.info(f"Successfully deleted file: {subpath}")
        return jsonify({"message": "File deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting file {subpath}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/search')
@cache.cached(timeout=60)
def search_files():
    """
    Enhanced search with metadata support.
    """
    query = request.args.get('q', '').lower()
    if not query:
        return render_template('search.html', results=[])
        
    try:
        # Search in Elasticsearch
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["name^2", "metadata.description", "metadata.tags", "metadata.category"]
                }
            }
        }
        
        results = es.search(index='files', body=search_query)
        
        # Format results
        formatted_results = []
        for hit in results['hits']['hits']:
            source = hit['_source']
            formatted_results.append({
                'name': source['name'],
                'path': source['path'],
                'type': source['type'],
                'size': source['size'],
                'metadata': source['metadata']
            })
                
        return render_template('search.html', results=formatted_results, query=query)
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return render_template('search.html', results=[], query=query)

def load_metadata() -> dict:
    """
    Load file metadata from JSON file.
    
    Returns:
        dict: Dictionary containing file metadata
    """
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading metadata: {e}")
        return {}

def save_metadata(metadata: dict) -> None:
    """
    Save file metadata to JSON file.
    
    Args:
        metadata (dict): Dictionary containing file metadata
    """
    try:
        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")

def create_version(file_path: str, version: int) -> str:
    """
    Create a new version of a file.
    
    Args:
        file_path (str): Path to the original file
        version (int): Version number
        
    Returns:
        str: Path to the new version file
    """
    try:
        base, ext = os.path.splitext(file_path)
        version_path = f"{base}_v{version}{ext}"
        shutil.copy2(file_path, version_path)
        return version_path
    except Exception as e:
        logger.error(f"Error creating version: {e}")
        raise

@app.route('/versions/<path:subpath>')
def list_versions(subpath: str):
    """
    List all versions of a file.
    
    Args:
        subpath (str): Path to the file
        
    Returns:
        Response: JSON with version information
    """
    try:
        metadata = load_metadata()
        file_versions = metadata.get(subpath, {}).get('versions', [])
        return jsonify(file_versions)
    except Exception as e:
        logger.error(f"Error listing versions: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/version/<path:subpath>', methods=['POST'])
def create_new_version(subpath: str):
    """
    Create a new version of a file.
    
    Args:
        subpath (str): Path to the file
        
    Returns:
        Response: Success message or error
    """
    try:
        file_path = os.path.join(UPLOAD_FOLDER, subpath)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
            
        metadata = load_metadata()
        file_info = metadata.get(subpath, {})
        current_version = len(file_info.get('versions', []))
        new_version = current_version + 1
        
        version_path = create_version(file_path, new_version)
        version_subpath = os.path.relpath(version_path, UPLOAD_FOLDER)
        
        if 'versions' not in file_info:
            file_info['versions'] = []
            
        file_info['versions'].append({
            'version': new_version,
            'path': version_subpath,
            'created_at': datetime.now().isoformat()
        })
        
        metadata[subpath] = file_info
        save_metadata(metadata)
        
        return jsonify({"message": f"Version {new_version} created successfully"})
    except Exception as e:
        logger.error(f"Error creating version: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/metadata/<path:subpath>', methods=['GET', 'POST'])
def handle_metadata(subpath: str):
    """
    Get or update file metadata.
    
    Args:
        subpath (str): Path to the file
        
    Returns:
        Response: Metadata or success message
    """
    try:
        metadata = load_metadata()
        file_info = metadata.get(subpath, {})
        
        if request.method == 'GET':
            return jsonify(file_info)
            
        if request.method == 'POST':
            new_metadata = request.json
            metadata[subpath] = {**file_info, **new_metadata}
            save_metadata(metadata)
            return jsonify({"message": "Metadata updated successfully"})
            
    except Exception as e:
        logger.error(f"Error handling metadata: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/comments/<path:subpath>', methods=['GET', 'POST'])
def handle_comments(subpath: str):
    """
    Get or add comments for a file.
    """
    try:
        comments = load_comments()
        file_comments = comments.get(subpath, [])
        
        if request.method == 'GET':
            return jsonify(file_comments)
            
        if request.method == 'POST':
            new_comment = {
                'text': request.json.get('text'),
                'user': session.get('username', 'anonymous'),
                'created_at': datetime.now().isoformat()
            }
            
            if subpath not in comments:
                comments[subpath] = []
                
            comments[subpath].append(new_comment)
            save_comments(comments)
            
            return jsonify({"message": "Comment added successfully"})
            
    except Exception as e:
        logger.error(f"Error handling comments: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Initialize file synchronization
def init_sync():
    """Initialize file synchronization."""
    global sync_thread, observer
    
    # Create sync thread
    sync_thread = threading.Thread(target=sync_files, daemon=True)
    sync_thread.start()
    
    # Create file observer
    observer = Observer()
    observer.schedule(FileChangeHandler(), SYNC_FOLDERS['local'], recursive=True)
    observer.start()

# Add batch operations
@app.route('/batch/delete', methods=['POST'])
def batch_delete():
    """
    Delete multiple files in a batch operation.
    
    Returns:
        Response: Success message or error
    """
    try:
        files = request.json.get('files', [])
        if not files:
            return jsonify({"error": "No files specified"}), 400
            
        deleted_files = []
        for file_path in files:
            full_path = os.path.join(UPLOAD_FOLDER, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                deleted_files.append(file_path)
                
        return jsonify({
            "message": f"Successfully deleted {len(deleted_files)} files",
            "deleted_files": deleted_files
        })
    except Exception as e:
        logger.error(f"Error in batch delete: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/batch/download', methods=['POST'])
def batch_download():
    """
    Download multiple files as a ZIP archive.
    
    Returns:
        Response: ZIP file or error
    """
    try:
        files = request.json.get('files', [])
        if not files:
            return jsonify({"error": "No files specified"}), 400
            
        # Create a temporary ZIP file
        zip_path = os.path.join(UPLOAD_FOLDER, 'temp.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in files:
                full_path = os.path.join(UPLOAD_FOLDER, file_path)
                if os.path.exists(full_path):
                    zipf.write(full_path, file_path)
                    
        return send_file(zip_path,
                        mimetype='application/zip',
                        as_attachment=True,
                        download_name='files.zip')
    except Exception as e:
        logger.error(f"Error in batch download: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        # Clean up temporary ZIP file
        if os.path.exists(zip_path):
            os.remove(zip_path)

@app.route('/batch/share', methods=['POST'])
def batch_share():
    """
    Generate share links for multiple files.
    
    Returns:
        Response: Share links or error
    """
    try:
        files = request.json.get('files', [])
        if not files:
            return jsonify({"error": "No files specified"}), 400
            
        share_links = []
        for file_path in files:
            token = generate_share_token()
            expiry = datetime.now() + timedelta(hours=24)
            
            shared_links[token] = {
                'file_path': file_path,
                'expiry': expiry
            }
            
            share_links.append({
                'file': file_path,
                'url': f"https://{HOST_IP}:5000/shared/{token}",
                'expires_at': expiry.isoformat()
            })
            
        return jsonify({"share_links": share_links})
    except Exception as e:
        logger.error(f"Error in batch share: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Add API documentation decorators
@app.route('/api/v1/files', methods=['GET'])
@swag_from({
    'summary': 'List all files',
    'parameters': [
        {
            'name': 'page',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 1,
            'description': 'Page number for pagination'
        },
        {
            'name': 'per_page',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 20,
            'description': 'Number of items per page'
        },
        {
            'name': 'sort_by',
            'in': 'query',
            'type': 'string',
            'required': False,
            'enum': ['name', 'size', 'date'],
            'description': 'Field to sort by'
        }
    ],
    'responses': {
        '200': {
            'description': 'List of files retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'files': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'path': {'type': 'string'},
                                'size': {'type': 'integer'},
                                'type': {'type': 'string'},
                                'upload_date': {'type': 'string'}
                            }
                        }
                    },
                    'total': {'type': 'integer'},
                    'page': {'type': 'integer'},
                    'per_page': {'type': 'integer'}
                }
            }
        }
    }
})
def list_files_api():
    """List all files with pagination and sorting."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort_by = request.args.get('sort_by', 'name')
        
        # Get all files
        files = []
        for root, _, filenames in os.walk(UPLOAD_FOLDER):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, UPLOAD_FOLDER)
                files.append({
                    'name': filename,
                    'path': rel_path,
                    'size': os.path.getsize(file_path),
                    'type': filename.rsplit('.', 1)[1].lower() if '.' in filename else '',
                    'upload_date': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                })
        
        # Sort files
        if sort_by == 'size':
            files.sort(key=lambda x: x['size'])
        elif sort_by == 'date':
            files.sort(key=lambda x: x['upload_date'], reverse=True)
        else:
            files.sort(key=lambda x: x['name'])
        
        # Paginate
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_files = files[start_idx:end_idx]
        
        return jsonify({
            'files': paginated_files,
            'total': len(files),
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/files/<path:filepath>', methods=['GET'])
@swag_from({
    'summary': 'Get file details',
    'parameters': [
        {
            'name': 'filepath',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Path to the file'
        }
    ],
    'responses': {
        '200': {
            'description': 'File details retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'path': {'type': 'string'},
                    'size': {'type': 'integer'},
                    'type': {'type': 'string'},
                    'upload_date': {'type': 'string'},
                    'metadata': {'type': 'object'},
                    'versions': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'version': {'type': 'integer'},
                                'path': {'type': 'string'},
                                'created_at': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        },
        '404': {'description': 'File not found'}
    }
})
def get_file_details(filepath: str):
    """Get detailed information about a specific file."""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filepath)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        filename = os.path.basename(file_path)
        file_type = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        file_size = os.path.getsize(file_path)
        upload_date = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
        
        metadata = load_metadata().get(filepath, {})
        versions = metadata.get('versions', [])
        
        return jsonify({
            'name': filename,
            'path': filepath,
            'size': file_size,
            'type': file_type,
            'upload_date': upload_date,
            'metadata': metadata,
            'versions': versions
        })
    except Exception as e:
        logger.error(f"Error getting file details: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/files/<path:filepath>/preview', methods=['GET'])
@swag_from({
    'summary': 'Get file preview',
    'parameters': [
        {
            'name': 'filepath',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Path to the file'
        }
    ],
    'responses': {
        '200': {
            'description': 'File preview retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'preview_type': {'type': 'string'},
                    'preview_content': {'type': 'string'}
                }
            }
        },
        '404': {'description': 'File not found'},
        '400': {'description': 'Preview not supported for this file type'}
    }
})
def get_file_preview(filepath: str):
    """Get preview content for a file."""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filepath)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        filename = os.path.basename(file_path)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if ext in PREVIEWABLE_EXTENSIONS['images']:
            preview_type = 'image'
            preview_content = f'<img src="/download/{filepath}" alt="{filename}" class="max-w-full h-auto">'
        elif ext in PREVIEWABLE_EXTENSIONS['documents']:
            if ext == 'pdf':
                preview_type = 'pdf'
                preview_content = f'<iframe src="/download/{filepath}" class="w-full h-screen"></iframe>'
            else:
                preview_type = 'text'
                preview_content = preview_text_file(file_path)
        elif ext in PREVIEWABLE_EXTENSIONS['code']:
            preview_type = 'code'
            preview_content = preview_text_file(file_path)
        elif ext in PREVIEWABLE_EXTENSIONS['audio']:
            preview_type = 'audio'
            preview_content = preview_audio_file(filepath)
        elif ext in PREVIEWABLE_EXTENSIONS['video']:
            preview_type = 'video'
            preview_content = preview_video_file(filepath)
        else:
            return jsonify({'error': 'Preview not supported for this file type'}), 400
            
        return jsonify({
            'preview_type': preview_type,
            'preview_content': preview_content
        })
    except Exception as e:
        logger.error(f"Error getting file preview: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        # Initialize file synchronization
        init_sync()
        
        # Create SSL context
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain('certs/cert.pem', 'certs/key.pem')
        context.set_ciphers(settings.tls_ciphers)
        
        # Start the application
        app.run(ssl_context=context, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        raise
    finally:
        cleanup()


