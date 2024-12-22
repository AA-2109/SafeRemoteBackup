import os
import ssl
from datetime import date
from datetime import timedelta
import qrcode
from flask import Flask, request, render_template, redirect, url_for, session
from flask_bcrypt import Bcrypt
import settings


# Directory inside container, mapped to D:\uploads on the host
UPLOAD_FOLDER = f'/app/static/uploads/' + str(date.today()) +'/'
DICT_STRUCT = settings.folders_dict
STRONG_CIPHERS = settings.tls_ciphers
STRONG_PASSWORD = settings.strong_password
STRONG_SECRET = settings.strong_secret
ip_address = os.getenv('HOST_IP')


app = Flask(__name__)
app.secret_key = STRONG_SECRET  # Replace with a strong secret key
bcrypt = Bcrypt(app)
# Hardcoded password hash (use bcrypt to generate a hash for your password)
admin_password_hash = bcrypt.generate_password_hash(STRONG_PASSWORD).decode('utf-8')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.options |= ssl.OP_NO_TLSv1
context.options |= ssl.OP_NO_TLSv1_1
context.set_ciphers(STRONG_CIPHERS)
context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')


def get_folder_name_str(filename):
    for folder in DICT_STRUCT.keys():
        if filename.split(".")[-1] in DICT_STRUCT[folder]:
            return UPLOAD_FOLDER+folder
    return UPLOAD_FOLDER+"unknown_format_files"

def create_folders(folder_names, base_directory):
    for folder in folder_names:
        path = os.path.join(base_directory, folder)
        os.makedirs(path, exist_ok=True)


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    if 'authenticated' in session and session['authenticated']:
        # If authenticated, render the admin page
        return render_template('upload.html', ip=ip_address)
    else:
        # Otherwise, redirect to login
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'failed_login_counter' not in session:
        session['failed_login_counter'] = 0  # Initialize the counter

    if session['failed_login_counter'] > 5:
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
    print(f"Host IP Address: {ip_address}")

    # URL to be encoded in the QR code
    url = f"https://{ip_address}:5000/"

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
    return render_template('admin.html', ip=ip_address, qr_code='static/qrcode.png')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return "No file part", 400
    files = request.files.getlist('files')  # Get a list of uploaded files

    if not files:
        return "No files selected", 400

    uploaded_files = []
    for file in files:
        if file.filename == '':
            continue  # Skip files with no name
        filepath = os.path.join(get_folder_name_str(file.filename), file.filename)
        file.save(filepath)
        uploaded_files.append(file.filename)

    if not uploaded_files:
        return "No valid files uploaded", 400

    return f"Files uploaded successfully: {', '.join(uploaded_files)}"


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('authenticated', None)  # Clear the session
    return redirect(url_for('login'))


if __name__ == '__main__':
    create_folders(DICT_STRUCT.keys(), UPLOAD_FOLDER)
    app.run(ssl_context=context, host='0.0.0.0', port=5000)


