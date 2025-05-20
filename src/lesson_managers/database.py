import logging
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from lesson_managers.lesson import Lesson
from typing import List, Optional

logger = logging.getLogger(__name__)

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
            self.connection = mysql.connector.connect(**self.config)
            self.connection.autocommit = True
            logger.info("Successfully connected to MySQL")
            self.initialize_database()
            logger.info("Successfully initialize database")
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            raise

    def close(self):
        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
                logger.info("Connection closed")
            except Error as e:
                logger.error(f"Error closing connection: {e}")

    def initialize_database(self):
        create_users = '''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                academ_group VARCHAR(13) NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        '''
        create_lesson = '''
            CREATE TABLE IF NOT EXISTS lesson (
                id BIGINT PRIMARY KEY,
                lesson_name VARCHAR(100) NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                text_of_hw TEXT,
                path_for_file TEXT,
                is_longterm BOOLEAN DEFAULT FALSE
            );
        '''
        try:
            cursor = self.connection.cursor()
            cursor.execute(create_users)
            cursor.execute(create_lesson)
            logger.info("Tables 'users' and 'lesson' checked/created")
        except Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
        finally:
            cursor.close()

    def addHW(self, lesson: Lesson) -> int:
        try:
            with self.connection.cursor() as cursor:
                print(f"db: {str(lesson)}")
                cursor.execute(
                    """
                    INSERT INTO lesson (id, lesson_name, date, time, text_of_hw, path_for_file, is_longterm)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        id = VALUES(id),
                        text_of_hw = VALUES(text_of_hw),
                        path_for_file = VALUES(path_for_file)
                    """, 
                    (lesson.id, lesson.title, lesson.date, lesson.time, lesson.hw_text, lesson.file_path, lesson.is_longterm)
                )
                logger.info(f"Added/updated lesson '{lesson.title}' with ID {cursor.lastrowid}")
                return cursor.lastrowid
        except Error as e:
            logger.error(f"Error adding/updating lesson: {e}")
            self.connection.rollback()
            return None

    def removeHWLastWeek(self) -> int:
        today = datetime.now().date()
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        return self._delete_by_date_range(last_monday, last_sunday)

    def addAdmin(self, user_id: int, academ_group: str) -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO users (user_id, academ_group, is_admin)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE is_admin = VALUES(is_admin)
                    ''',
                    (user_id, academ_group, True)
                )
                return True
        except Error as e:
            logger.error(f"Error setting admin status: {e}")
            return False

    def removeAdmin(self, user_id) -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET is_admin = FALSE WHERE user_id = %s", (user_id,)
                )
                if cursor.rowcount:
                    logger.info(f"Removed admin rights for user {user_id}")
                    return True
                logger.info(f"User {user_id} not found")
                return False
        except Error as e:
            logger.error(f"Error removing admin: {e}")
            self.connection.rollback()
            return False

    def isAdmin(self, user_id: int) -> bool:
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    'SELECT is_admin FROM users WHERE user_id = %s', (user_id,)
                )
                row = cursor.fetchone()
                return bool(row and row.get('is_admin'))
        except Error as e:
            logger.error(f"Error checking admin status: {e}")
            return False

    def addUser(self, user_id: int, academ_group: str, is_admin: bool = False) -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (user_id, academ_group, is_admin)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        academ_group = VALUES(academ_group),
                        is_admin     = VALUES(is_admin)
                    """,
                    (user_id, academ_group, is_admin)
                )
                return True
        except Error as e:
            logger.error(f"Error adding/updating user: {e}")
            self.connection.rollback()
            return False

    def userExist(self, user_id: int) -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM users WHERE id = %s",
                    (user_id,)
                )
                return cursor.fetchone() is not None
        except Error as e:
            logger.error(f"Error checking user existence: {e}")
            self.connection.rollback()
            return False

    def getUser(self, user_id: int) -> dict | None:
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT user_id, academ_group, is_admin FROM users WHERE user_id = %s",
                    (user_id,)
                )
                row = cursor.fetchone()
                return row  # либо None
        except Error as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None

    def getListAdmin(self, academ_group: str) -> list[int]:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    'SELECT user_id FROM users WHERE academ_group = %s AND is_admin = TRUE',
                    (academ_group,)
                )
                return [row[0] for row in cursor.fetchall()]
        except Error as e:
            logger.error(f"Error fetching admins: {e}")
            return []

    def getLongtermHW(self) -> list[Lesson]:
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT id, lesson_name, date, time, text_of_hw, path_for_file, is_longterm
                    FROM lesson
                    WHERE is_longterm = TRUE 
                    """
                )
                rows = cursor.fetchall()

                return [Lesson(
                    title=row.get('lesson_name'),
                    date=row.get('date'),
                    time_str=str(row.get('time')),
                    has_hw=(bool(row.get('text_of_hw')) or bool(row.get('path_for_file'))),
                    hw_text=row.get('text_of_hw'),
                    has_file=bool(row.get('path_for_file')),
                    file_path=row.get('path_for_file'),
                    is_longterm=bool(row.get('is_longterm'))
                ) for row in rows] 

        except Error as e:
            logger.error(f"Error fetching HW is longterm ={hw_id}: {e}")
            return None

    def getHWbyID(self, hw_id: int) -> Optional[Lesson]:
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT id, lesson_name, date, time, text_of_hw, path_for_file, is_longterm
                    FROM lesson
                    WHERE id = %s
                    """,
                    (hw_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None

                return Lesson(
                    title=row['lesson_name'],
                    date=row['date'],
                    time=row['time'],
                    hw_text=row['text_of_hw'] or "",
                    file_path=row['path_for_file'] or "",
                    has_hw=(bool(row.get('text_of_hw')) or bool(row.get('path_for_file'))),
                    has_file=bool(row['path_for_file']),
                    is_longterm=bool(row['is_longterm'])
                )
        except Error as e:
            logger.error(f"Error fetching HW by id={hw_id}: {e}")
            return None

    def getListHWForToday(self) -> list[Lesson]:
        today = datetime.now().date()
        return self._fetch_hw_by_date(today)

    def getListHWForTomorrow(self) -> list[Lesson]:
        tomorrow = datetime.now().date() + timedelta(days=1)
        return self._fetch_hw_by_date(tomorrow)

    def getListHWForWeek(self) -> list[Lesson]:
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return self._fetch_hw_by_date_range(monday, sunday)

    def getListHWForNextWeek(self) -> list[Lesson]:
        today = datetime.now().date()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        next_sunday = next_monday + timedelta(days=6)
        return self._fetch_hw_by_date_range(next_monday, next_sunday)

    # --- Private helpers ---
    def _fetch_hw_by_date(self, target_date) -> list[Lesson]:
        return self._fetch_hw_by_date_range(target_date, target_date)

    def _fetch_hw_by_date_range(self, start_date, end_date) -> list[Lesson]:
        query = '''
            SELECT id, lesson_name, date, time, text_of_hw, path_for_file, is_longterm
            FROM lesson
            WHERE date BETWEEN %s AND %s
            ORDER BY date
        '''
        try:
            # ensure connection
            if not self.connection or not self.connection.is_connected():
                self.connect()
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (start_date, end_date))
                rows = cursor.fetchall()
                lessons = [Lesson(
                    title=row.get('lesson_name'),
                    date=row.get('date'),
                    time_str=str(row.get('time')),
                    has_hw=(bool(row.get('text_of_hw')) or bool(row.get('path_for_file'))),
                    hw_text=row.get('text_of_hw'),
                    has_file=bool(row.get('path_for_file')),
                    file_path=row.get('path_for_file'),
                    is_longterm=bool(row.get('is_longterm'))
                ) for row in rows] 
                print("\t\t\t", lessons)
                if (lessons):
                    print("\t\t\t", lessons[0])
                return lessons 

        except Error as e:
            logger.error(f"Error fetching HW from {start_date} to {end_date}: {e}")
            return []

    def _delete_by_date_range(self, start_date, end_date) -> int:
        query = '''
            DELETE FROM lesson WHERE date BETWEEN %s AND %s
        '''
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, (start_date, end_date))
                deleted = cursor.rowcount
                logger.info(f"Deleted {deleted} lessons between {start_date} and {end_date}")
                return deleted
        except Error as e:
            logger.error(f"Error deleting lessons: {e}")
            self.connection.rollback()
            return 0
