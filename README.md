# Safe Remote Backup

A secure, modern web application for remote file backup and management. Built with Flask and featuring a beautiful, responsive UI powered by Tailwind CSS.

## Features

- 🔒 Secure authentication with password protection
- 📱 Modern, responsive UI with drag-and-drop file upload
- 📁 Automatic file organization by type
- 🔄 Real-time upload progress tracking
- 📱 QR code for quick mobile access
- 🚀 Fast file browsing with caching
- 🔒 TLS encryption with strong ciphers
- 📊 Admin dashboard with system status
- 🎨 Beautiful, intuitive interface

## Security Features

- TLS encryption with modern cipher suites
- Password hashing with bcrypt
- Rate limiting for login attempts
- Session management with timeout
- File type validation
- File size limits
- Secure file handling
- Input sanitization

## Prerequisites

- Python 3.8 or higher
- Docker (optional, for containerized deployment)
- SSL certificates (for HTTPS)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SafeRemoteBackup.git
cd SafeRemoteBackup
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the template:
```bash
cp .env.example .env
```

5. Edit the `.env` file with your configuration:
```env
# Security settings
ADMIN_PASSWORD=your_secure_password_here
FLASK_SECRET_KEY=your_secret_key_here

# Application settings
MAX_UPLOAD_SIZE=100  # Maximum file upload size in MB
SESSION_LIFETIME_MINUTES=30

# Cache settings
CACHE_TYPE=simple  # Options: simple, filesystem, redis, memcached
CACHE_DEFAULT_TIMEOUT=300  # Cache timeout in seconds

# Server settings
HOST_IP=your_server_ip_here
```

## Running the Application

### Local Development

1. Start the Flask development server:
```bash
python app/app.py
```

2. Access the application at `https://localhost:5000`

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t safe-remote-backup .
```

2. Run the container:
```bash
docker-compose up -d
```

3. Access the application at `https://your-server-ip:5000`

## Usage

### File Organization

Files are automatically organized into the following categories:
- 📸 Photos: jpg, jpeg, png, gif, bmp
- 🎥 Videos: mp4, avi, mkv, mov
- 📄 Documents: pdf, doc, docx, txt, xls, xlsx
- 📚 Books: epub, fb2
- 🎵 Music: mp3, aac, m4a
- 📦 Archives: zip, rar, tar, tar.bz, tar.gz

### Features

1. **File Upload**
   - Drag and drop files or click to select
   - Multiple file upload support
   - Real-time upload progress
   - File size validation
   - File type validation

2. **File Management**
   - Browse files by category
   - Download files
   - View file details
   - Breadcrumb navigation

3. **Admin Dashboard**
   - Server status monitoring
   - Quick access QR code
   - System configuration
   - Quick actions

## Security Considerations

1. Always use HTTPS in production
2. Set a strong password in the `.env` file
3. Generate a secure secret key
4. Configure appropriate file size limits
5. Set up proper session timeouts
6. Use secure file permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask web framework
- Tailwind CSS for styling
- Inter font family
- Heroicons for icons

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

---
