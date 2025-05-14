import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self, config):
        self.config = config
        self.connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        try:
            # Создаём соединение
            self.connection = mysql.connector.connect(**self.config)
            # Включаем автокоммит
            self.connection.autocommit = True
            print("Successfully connected to MySQL")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise

    def close(self):
        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
                print("Connection closed")
            except Error as e:
                print(f"Error closing connection: {e}")

    def initialize_database(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("Table 'users' checked/created")
        except Error as e:
            print(f"Error creating table: {e}")
            raise
        finally:
            cursor.close()

    def get_user(self, user_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error getting user: {e}")
            return None
        finally:
            cursor.close()

    def set_admin_status(self, user_id, is_admin):
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, is_admin)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE is_admin = VALUES(is_admin)
            ''', (user_id, is_admin))
            print("Admin status set")
            return True
        except Error as e:
            print(f"Error setting admin status: {e}")
            return False
        finally:
            cursor.close()
