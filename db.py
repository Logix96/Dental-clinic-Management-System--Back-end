import mysql.connector
import os
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env
load_dotenv() 

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME")
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Lỗi kết nối database: {err}")
        return None
