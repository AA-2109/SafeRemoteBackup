from datetime import datetime
import os
import sqlite3
import settings
import utils



def run_query(query):
    try:
        with sqlite3.connect(settings.path_to_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            print("Table created successfully.")
    except sqlite3.OperationalError as e:
        print("Failed to create table:", e)

def is_db_exists(path_to_db):
    return os.path.isfile(path_to_db)

def create_db():
    try:
        if not is_db_exists(settings.path_to_db):
            with open(os.path.join(settings.path_to_db, settings.path_to_db), 'w') as db_file:
                return True
    except Exception as e:
        return False

def create_table():
    try:
        sql_statements = """CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY, 
                name text NOT NULL,
                path text NOT NULL, 
                hash text NOT NULL, 
                date_of_upload DATE
            );"""
        run_query(sql_statements)
        return True
    except Exception as e:
        return False

def add_data_to_db(name, path, hash):
    with sqlite3.connect(settings.path_to_db) as conn:
        # insert table statement
        query = f''' INSERT INTO files(name,type,hash, date_of_upload)
                  VALUES({str(datetime.now().ctime())},{name},{path},{hash}) '''
        run_query(query)
        
def prepare_database():
    if not create_db():
        print("DB Creation failed")

    if not create_table():
        print("DB Creation failed")