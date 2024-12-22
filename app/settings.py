# Define a folders structure, e.g. :
# folders_dict = {'folder_name':[set of file extensions that you want to ut inside a folder]}

folders_dict = {
    "photos": {"jpg", "jpeg", "png", "gif", "bmp"},
    "videos": {"mp4", "avi", "mkv", "mov"},
    "documents": {"pdf", "doc", "docx", "txt", "xls", "xlsx"},
    "books": {"epub", "fb2"},
    "music": {"mp3", "aac", "m4a"},
    "archives": {"zip", "rar", "tar", "tar.bz", "tar.gz"},
    "unknown_format_files": {}
}

tls_ciphers = (
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

strong_password = "HelloWorld123!"
strong_secret = "superSecret"

