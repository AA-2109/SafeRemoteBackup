import os 
import app
import hashlib
from datetime import datetime
from settings import path_to_upload, hash_algo


def get_folder_name_str(filename: str):
    for folder in app.DICT_STRUCT.keys():
        if filename.split(".")[-1] in app.DICT_STRUCT[folder]:
            return f"{path_to_upload}/"+folder
    return f"{path_to_upload}/unknown_format_files"


def create_folders(folder_names: str, base_directory: str):
    os.makedirs(app.UPLOAD_FOLDER, exist_ok=True)
    for folder in folder_names:
        path = os.path.join(base_directory, folder)
        os.makedirs(path, exist_ok=True)


def hash_file(filepath: str, algo: str = hash_algo):
    h = hashlib.new(algo)
    with open(filepath, 'rb') as f:
       while chunk := f.read(8192):
           h.update(chunk)
    return h.hexdigest()


def get_relative_filepath(filepath: str):
    relative_path_str = filepath.split("/")[3:]
    return f"{app.UPLOAD_DIR}"+"/".join(relative_path_str)


def update_logfile(filepath: str, path_to_logfile: str, success: bool, e: Exception = None):
    message = hash_file(filepath) if success else f"upload failed with {e}" 
    with open(path_to_logfile, "a") as log:
        log.write(f"{str(datetime.now().ctime())} -- {get_relative_filepath(filepath)} -- {message}\n")