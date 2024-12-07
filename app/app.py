from flask import Flask, request, render_template
import os
import qrcode
import ssl
from datetime import date

app = Flask(__name__)

# Directory mapped to D:\uploads on the host
UPLOAD_FOLDER = f'/app/static/uploads/' + str(date.today()) +'/'
STRONG_CIPHERS = (
    'ECDHE-ECDSA-AES256-GCM-SHA384:'
    'ECDHE-RSA-AES256-GCM-SHA384:'
    'ECDHE-ECDSA-AES128-GCM-SHA256:'
    'ECDHE-RSA-AES128-GCM-SHA256:'
    'ECDHE-ECDSA-AES256-SHA384:'
    'ECDHE-RSA-AES256-SHA384:'
    'TLS_AES_256_GCM_SHA384:'
    'TLS_CHACHA20_POLY1305_SHA256:'
    'TLS_AES_128_GCM_SHA256'
)

folders_map = {
    "photos": ["jpg", "jpeg", "png", "gif", "bmp"],
    "videos": ["mp4", "avi", "mkv", "mov"],
    "documents": ["pdf", "doc", "docx", "txt", "xls", "xlsx"],
    "books": ["epub", "fb2"],
    "music": ["mp3", "aac", "m4a"],
    "archives": ["zip", "rar", "tar", "tar.bz", "tar.gz"],
    "unknown_format_files": []
}
def get_folder_name_str(filename):
    for folder in folders_map.keys():
        if filename.split(".")[-1] in folders_map[folder]:
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
    return render_template('upload.html')


@app.route('/admin')
def get_admin_page():
    # Get the local IP address of the machine
    ip_address = os.getenv('HOST_IP')
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


if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.options |= ssl.OP_NO_TLSv1
    context.options |= ssl.OP_NO_TLSv1_1
    context.set_ciphers(STRONG_CIPHERS)
    context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
    create_folders(folders_map.keys(), UPLOAD_FOLDER)
    app.run(ssl_context=context, host='0.0.0.0', port=5000)

