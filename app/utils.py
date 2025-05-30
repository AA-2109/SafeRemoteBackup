import os 
import app
import hashlib
from datetime import datetime
from settings import path_to_upload, hash_algo


def get_folder_name_str(filename):
    for folder in app.DICT_STRUCT.keys():
        if filename.split(".")[-1] in app.DICT_STRUCT[folder]:
            return f"{path_to_upload}/"+folder
    return f"{path_to_upload}/unknown_format_files"


def create_folders(folder_names, base_directory):
    os.makedirs(app.UPLOAD_FOLDER, exist_ok=True)
    for folder in folder_names:
        path = os.path.join(base_directory, folder)
        os.makedirs(path, exist_ok=True)


def hash_file(path, algo=hash_algo):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
       while chunk := f.read(8192):
           h.update(chunk)
    return h.hexdigest()


def update_logfile(filepath):
    logfile=f"{path_to_upload}/upload_log.log"
    with open(logfile, "a") as log:
        log.write(f"{str(datetime.now().ctime())} -- {filepath} -- {hash_file(filepath)}\n")