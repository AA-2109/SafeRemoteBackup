# Safe Remote Backup

- TLS/SSL encryption for secure communication
- Brute-force protection during login attempts
- Dynamic folder creation for organizing uploads
- QR code generation for accessing upload page from mobile devices
- Session management with authentication and logout functionality

---

## Features

1. **Secure Login System**
   - Passwords are securely hashed using `bcrypt`.
   - Brute-force protection with a failed login counter.
   - Sessions managed with Flask's `session` module.

2. **TLS/SSL Configuration**
   - TLS/SSL enforced using strong ciphers.
   - Certificates loaded for secure communication.

3. **Dynamic File Organization**
   - Files are uploaded to structured directories based on their extensions.
   - Unsupported file types are placed in an `unknown_format_files` folder.

4. **QR Code Generation**
   - QR code created dynamically for accessing the admin portal.

5. **Session Management**
   - Authenticated sessions for secure access to admin features.
   - Automatic session timeout after 30 minutes.

---

## Prerequisites

1. **Python (>= 3.8)**
2. **Flask and Required Dependencies**
   - Install dependencies using `pip install -r requirements.txt`.
3. **Docker**

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Obluchatel/SafeRemoteBackup.git
   cd SafeRemoteBackup
   ```

2. Add your configuration in `settings.py`, e.g.:
   ```python
   folders_dict = {
       'images': ['jpg', 'png', 'gif'],
       'documents': ['pdf', 'docx', 'txt'],
       'videos': ['mp4', 'avi'],
   }

   strong_password = 'your_admin_password'
   ```
3. Update `docker-compose.yaml` file, e.g.:
    ```bash
    ports:
      - "${APP_PORT:-5000}:${CONTAINER_PORT:-5000}"
    environment:
      - HOST_IP=${HOST_IP:-127.0.0.1}
    volumes:
      - "${UPLOAD_DIR:-/mnt/share/uploads}:/app/static/uploads"
   ```
---

## Usage

1. **Run the Application:**
   ```bash
   docker compose up --build
   ```

2. **Access the Web Interface:**
   - Navigate to `https://<$HOST_IP>:5000/` in your browser.

3. **Login:**
   - Enter the admin password defined in `settings.py`.

4. **Upload Files:**
   - Files are saved in structured directories under `UPLOAD_DIR` in `docker-compose.yaml`.

5. **Admin Page:**
   - Find a link for mobile devices on admin portal - QR code and IP address are available there.

---

## Security Features

1. **Password Hashing:**
   - Admin password is hashed using `bcrypt`.

2. **Session Management:**
   - Sessions expire after 30 minutes of inactivity.

3. **Brute Force Protection:**
   - Limits login attempts to 5 before locking the user out.

4. **TLS Enforcement:**
   - Secure communication enforced using strong TLS ciphers.

---

## Notes

1. Ensure the `settings.py` file is configured correctly.
2. Store `cert.pem` and `key.pem` securely and update them as needed.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests for improvements.

---
