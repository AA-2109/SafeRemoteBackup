import os
from app.utils import is_db_exists
import settings


def create_db():
    if not is_db_exists(settings.path_to_db):
        with open(os.path.join(settings.path_to_db, "files.db"), 'w') as db_file:
            pass
