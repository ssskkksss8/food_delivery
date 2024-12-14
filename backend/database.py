from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import sql

# Загружаем переменные окружения из .env файла
load_dotenv()

# Читаем переменные окружения
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print("Ошибка подключения к базе данных:", e)
        raise

def initialize_database():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            script_path = os.path.join(os.path.dirname(__file__), "../db/init.sql")
            with open(script_path, "r") as sql_file:
                sql_script = sql_file.read()
            cursor.execute(sql_script)
            conn.commit()
            print("База данных успешно инициализирована!")
    except Exception as e:
        print("Ошибка инициализации базы данных:", e)
    finally:
        if conn:
            conn.close()  


if __name__ == "__main__":
    initialize_database()
