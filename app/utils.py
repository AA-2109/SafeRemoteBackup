import os 
from datetime import date
import app

def get_folder_name_str(filename):
    for folder in app.DICT_STRUCT.keys():
        if filename.split(".")[-1] in app.DICT_STRUCT[folder]:
            return app.UPLOAD_FOLDER+folder
    return app.UPLOAD_FOLDER+"unknown_format_files"


def create_folders(folder_names, base_directory):
    os.makedirs(app.UPLOAD_FOLDER, exist_ok=True)
    for folder in folder_names:
        path = os.path.join(base_directory, folder)
        os.makedirs(path, exist_ok=True)
