import mysql.connector

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",          # Thay
            password="4Melaqlosr$", # Thay
            database="db"   # Thay
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Lỗi kết nối database: {err}")
        return None