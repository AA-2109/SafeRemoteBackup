from datetime import datetime
import os
import sqlite3
import settings


def run_query(query):
    try:
        with sqlite3.connect(settings.path_to_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            print("Table created successfully.")
    except sqlite3.OperationalError as e:
        print("Failed to create table:", e)

def run_query_with_params(query, params):
    try:
        with sqlite3.connect(settings.path_to_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            print("Data inserted successfully.")
    except sqlite3.OperationalError as e:
        print("Failed to execute query:", e)


def is_db_exists(path_to_db):
    return os.path.isfile(path_to_db)

def create_db():
    try:
        if not is_db_exists(settings.path_to_db):
            with open(settings.path_to_db, 'w') as db_file:
                return True
    except Exception as e:
        return False

def create_table():
    try:
        sql_statements = """CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY , 
                name text NOT NULL,
                path text NOT NULL, 
                hash text NOT NULL, 
                date_of_upload TEXT
            );"""
        run_query(sql_statements)
        return True
    except Exception as e:
        return False

def add_data_to_db(name, path, hash):
    query = '''INSERT INTO files(name, path, hash, date_of_upload)
               VALUES (?, ?, ?, ?)'''
    run_query_with_params(query, (name, path, hash, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        
def prepare_database():
    if not create_db():
        print("DB Creation failed")

    if not create_table():
        print("DB Creation failed")