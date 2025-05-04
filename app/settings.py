# Define a folders structure, e.g. :
# folders_dict = {'folder_name':[set of file extensions that you want to ut inside a folder]}
folders_dict = {
    "photos": {"jpg", "jpeg", "png", "gif", "bmp", "heic"},
    "videos": {"mp4", "avi", "mkv", "mov"},
    "documents": {"pdf", "doc", "docx", "txt", "xls", "xlsx"},
    "logs": {"log"},
    "configuration": {"cfg", "ini", "conf"},
    "books": {"epub", "fb2"},
    "music": {"mp3", "aac", "m4a", "flac", "wav", "aac", "alac"},
    "archives": {"zip", "rar", "tar", "tar.bz", "tar.gz"},
    "unknown_format_files": {}
}


path_to_upload = f'/app/static/uploads'
path_to_upload_logfile=f"{path_to_upload}/upload.log"
path_to_failed_logfile=f"{path_to_upload}/failed_upload.log"
path_to_db = f"{path_to_upload}/files.db"
hash_algo = 'md5'
strong_password = "HelloWorld123!"