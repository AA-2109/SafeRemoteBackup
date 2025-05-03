import os
import ssl
import utils
from datetime import timedelta
import qrcode
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import settings
from werkzeug.utils import secure_filename


# Directory inside container, mapped to D:\uploads on the host
UPLOAD_FOLDER = settings.path_to_upload
UPLOAD_DIR = os.getenv('UPLOAD_DIR')
HOST_IP = os.getenv('HOST_IP')
# Directories structure
DICT_STRUCT = settings.folders_dict
#TLS ciphers
STRONG_PASSWORD = settings.strong_password
STRONG_SECRET = os.urandom(24)


#App init
app = Flask(__name__)
app.secret_key = STRONG_SECRET
bcrypt = Bcrypt(app)
admin_password_hash = bcrypt.generate_password_hash(STRONG_PASSWORD).decode('utf-8')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# TLS context
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.minimum_version = ssl.TLSVersion.TLSv1_2
context.maximum_version = ssl.TLSVersion.TLSv1_3
context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20")
context.set_ecdh_curve("X25519")
context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
context.options |= ssl.OP_NO_COMPRESSION
context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')

@app.route('/')
def index():
    if 'authenticated' in session and session['authenticated']:
        # If authenticated, render the admin page
        return render_template('upload.html', ip=HOST_IP)
    else:
        # Otherwise, redirect to login
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'failed_login_counter' not in session:
        session['failed_login_counter'] = 0 

    if session['failed_login_counter'] > 3:
        return render_template('frig-off.html', error="Too many wrong passwords, frig off")
    if request.method == 'POST':
        password = request.form['password']
        if bcrypt.check_password_hash(admin_password_hash, password):
            # Password is correct, set session and redirect to admin page
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            # Password is incorrect
            session['failed_login_counter'] += 1
            return render_template('login.html', error="Invalid password.")

    return render_template('login.html')


@app.route('/admin')
def get_admin_page():
    print(f"Host IP Address: {HOST_IP}")

    # URL to be encoded in the QR code
    url = f"https://{HOST_IP}:5000/"

    # Path to save the QR code (temporary)
    qr_path = os.path.join('static', 'qrcode.png')

    # Generate and save the QR code
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

    # Pass the IP address and QR code path to the admin.html template
    return render_template('admin.html', ip=HOST_IP, qr_code='static/qrcode.png')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return "No file part", 400
    files = request.files.getlist('files')

    if not files:
        return "No files selected", 400
    
    try:
        uploaded_files = []
        for file in files:
            if file.filename == '':
                continue
            filename = secure_filename(file.filename)
            folder = utils.get_folder_name_str(filename)
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, filename)
            with open(filepath, 'wb') as f:
                file.stream.seek(0)
                while chunk := file.stream.read(4096):
                    f.write(chunk)
            utils.update_logfile(filepath, settings.path_to_upload_logfile, True)
            uploaded_files.append(filename)
    
    except Exception as e:
        utils.update_logfile(filepath, settings.path_to_failed_logfile, False, e)
    
    if not uploaded_files:
        return "No valid files uploaded", 400

    return redirect(url_for('index'))


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('authenticated', None)  # Clear the session
    return redirect(url_for('login'))


if __name__ == '__main__':
    utils.create_folders(DICT_STRUCT.keys(), UPLOAD_FOLDER)
    app.run(ssl_context=context, host=f"{HOST_IP}", port=5000)


