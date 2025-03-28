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

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- SSL certificates (for HTTPS)

## Quick Start Guide

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/SafeRemoteBackup.git
   cd SafeRemoteBackup
   ```

2. **Set Up Environment Variables**
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your configuration:
   ```env
   # Security settings (REQUIRED)
   ADMIN_PASSWORD=your_secure_password_here
   FLASK_SECRET_KEY=your_secret_key_here

   # Application settings (OPTIONAL)
   MAX_UPLOAD_SIZE=100  # Maximum file upload size in MB
   SESSION_LIFETIME_MINUTES=30
   HOST_IP=your_server_ip_here

   # Cache settings (OPTIONAL)
   CACHE_TYPE=simple
   CACHE_DEFAULT_TIMEOUT=300
   ```

3. **Generate SSL Certificates**
   ```bash
   mkdir -p certs
   openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365
   ```

4. **Create Required Directories**
   ```bash
   mkdir -p uploads data
   ```

5. **Start the Application**
   ```bash
   docker-compose up -d
   ```

6. **Check Application Status**
   ```bash
   docker-compose ps
   ```

7. **View Application Logs**
   ```bash
   docker-compose logs -f app
   ```

8. **Access the Application**
   - Open your browser and navigate to `https://your_server_ip:5000`
   - Use the admin password you set in the `.env` file
   - The QR code on the admin page provides quick mobile access

## File Organization

Files are automatically organized into the following categories:
- 📸 Photos: jpg, jpeg, png, gif, bmp
- 🎥 Videos: mp4, avi, mkv, mov
- 📄 Documents: pdf, doc, docx, txt, xls, xlsx
- 📚 Books: epub, fb2
- 🎵 Music: mp3, aac, m4a
- 📦 Archives: zip, rar, tar, tar.bz, tar.gz

## Docker Commands Reference

### Starting the Application
```bash
# Start in detached mode
docker-compose up -d

# Start with logs
docker-compose up
```

### Stopping the Application
```bash
# Stop the containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Managing Containers
```bash
# View running containers
docker-compose ps

# Restart containers
docker-compose restart

# Rebuild containers
docker-compose up -d --build
```

### Viewing Logs
```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs -f app
docker-compose logs -f elasticsearch
```

### Backup and Restore

1. **Backup Data**
   ```bash
   # Create backup directory
   mkdir -p backups

   # Backup uploads
   tar -czf backups/uploads.tar.gz uploads/

   # Backup Elasticsearch data
   docker-compose exec elasticsearch elasticsearch-dump --input=http://localhost:9200/files --output=/tmp/files.json
   docker cp $(docker-compose ps -q elasticsearch):/tmp/files.json backups/
   ```

2. **Restore Data**
   ```bash
   # Restore uploads
   tar -xzf backups/uploads.tar.gz -C ./

   # Restore Elasticsearch data
   docker cp backups/files.json $(docker-compose ps -q elasticsearch):/tmp/
   docker-compose exec elasticsearch elasticsearch-dump --input=/tmp/files.json --output=http://localhost:9200/files
   ```

## Troubleshooting

### Common Issues

1. **Container Won't Start**
   - Check logs: `docker-compose logs app`
   - Verify environment variables
   - Ensure ports are not in use
   - Check SSL certificates

2. **Elasticsearch Issues**
   - Check logs: `docker-compose logs elasticsearch`
   - Verify memory settings
   - Check disk space
   - Ensure proper permissions

3. **File Upload Issues**
   - Check file size limits
   - Verify file permissions
   - Check disk space
   - Review application logs

### Health Checks

1. **Application Health**
   ```bash
   curl -k https://localhost:5000/
   ```

2. **Elasticsearch Health**
   ```bash
   curl http://localhost:9200/_cluster/health
   ```

## Security Considerations

1. **SSL/TLS**
   - Always use HTTPS in production
   - Keep SSL certificates secure
   - Regularly update certificates

2. **Passwords**
   - Use strong passwords
   - Change default passwords
   - Rotate passwords regularly

3. **File Permissions**
   - Ensure proper file permissions
   - Use non-root user
   - Implement proper access controls

4. **Network Security**
   - Use firewall rules
   - Limit port exposure
   - Implement rate limiting

## Maintenance

### Regular Tasks

1. **Update Application**
   ```bash
   git pull
   docker-compose up -d --build
   ```

2. **Clean Up Old Files**
   ```bash
   # Remove files older than 30 days
   find uploads -type f -mtime +30 -delete
   ```

3. **Backup Data**
   ```bash
   # Run backup script
   ./backup.sh
   ```

### Monitoring

1. **System Resources**
   ```bash
   # View container stats
   docker stats

   # View disk usage
   df -h
   ```

2. **Application Logs**
   ```bash
   # View recent logs
   docker-compose logs --tail=100
   ```

## Support

For support, please:
1. Check the troubleshooting guide
2. Review the logs
3. Open an issue in the GitHub repository
4. Contact the maintainers

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask web framework
- Tailwind CSS for styling
- Inter font family
- Heroicons for icons

---
