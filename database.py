import mariadb
from mariadb import Error

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
            self.connection = mariadb.connect(**self.config)
            print("Successfully connected to database")  # Добавим логирование
        except Error as e:
            print(f"Error connecting to MariaDB: {e}")
            raise
    
    def close(self):
        if self.connection:
            try:
                self.connection.close()
                print("Connection closed")  # Логирование закрытия
            except Error as e:
                print(f"Error closing connection: {e}")
    
    def initialize_database(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.connection.commit()
                print("Таблица users успешно создана/проверена")
        except Error as e:
            print(f"Ошибка при создании таблицы: {e}")
            raise
    
    def get_user(self, user_id):
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                return cursor.fetchone()
        except Error as e:
            print(f"Error getting user: {e}")
            return None
    
    def set_admin_status(self, user_id, is_admin):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO users (user_id, is_admin)
                    VALUES (?, ?)
                    ON DUPLICATE KEY UPDATE is_admin = ?
                ''', (user_id, is_admin, is_admin))
                self.connection.commit()
                return True
        except Error as e:
            print(f"Error setting admin status: {e}")
            return False
