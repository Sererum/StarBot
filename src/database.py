import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

from src.lesson import Lesson


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
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS lesson (
                   id INT PRIMARY KEY AUTO_INCREMENT,
                  lesson_name VARCHAR(100) NOT NULL  ,
                  date DATE NOT NULL  ,
                  lesson_description TEXT,
                  paths_for_files  TEXT  
             )
            ''')
            print("Table 'lesson' checked/create")
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

    def fillListHWForToday(self):
        """Получение всех уроков на сегодняшний день"""
        try:
            today = datetime.now().date()
            with self.connection.cursor() as cursor:
                query = """
                   SELECT id, lesson_name, date, lesson_description, paths_for_files 
                   FROM lesson 
                   WHERE date = %s
                   """
                cursor.execute(query, (today,))
                lessons = cursor.fetchall()
                response = "📅 Уроки на сегодня:\n\n"

                for lesson in lessons:
                    response += f"📖 <b>{lesson[1]}</b>\n"  # lesson_name (индекс 1)
                    response += f"📝 {lesson[3]}\n"  # lesson_description (индекс 3)

                    if lesson[4]:  # paths_for_files (индекс 4)
                        response += f"📎 Файлы: {lesson[4]}\n"

                    response += "\n"
                return response
        except Error as err:
            print(f"Ошибка при получении данных: {err}")
            return []

    def fillListHWForTomorrow(self):
        try:
            tomorrow = datetime.now().date() + timedelta(days=1)
            with self.connection.cursor() as cursor:
                query = """
                      SELECT id, lesson_name, date, lesson_description, paths_for_files 
                      FROM lesson 
                      WHERE date = %s
                      """
                cursor.execute(query, (tomorrow,))
                lessons = cursor.fetchall()
                response = "📅 Уроки на сегодня:\n\n"

                for lesson in lessons:
                    response += f"📖 <b>{lesson[1]}</b>\n"  # lesson_name (индекс 1)
                    response += f"📝 {lesson[3]}\n"  # lesson_description (индекс 3)

                    if lesson[4]:  # paths_for_files (индекс 4)
                        response += f"📎 Файлы: {lesson[4]}\n"

                    response += "\n"
                return response
        except Error as err:
            print(f"Ошибка при получении данных: {err}")
            return []

    def fillListHWForWeek(self):
        """Получение уроков на текущую неделю"""
        try:
            # Получаем текущую дату и границы недели
            today = datetime.now().date()
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)

            # Проверяем соединение с БД
            if not self.connection or not self.connection.is_connected():
                self.connect()

            with self.connection.cursor(dictionary=True) as cursor:
                # Выполняем запрос к БД
                query = """
                    SELECT id, lesson_name, date, lesson_description, paths_for_files 
                    FROM lesson 
                    WHERE date BETWEEN %s AND %s
                    ORDER BY date
                """
                cursor.execute(query, (monday, sunday))
                lessons = cursor.fetchall()

                # Инициализируем структуру для хранения уроков по дням
                week_lessons = {
                    'Понедельник': [],
                    'Вторник': [],
                    'Среда': [],
                    'Четверг': [],
                    'Пятница': [],
                    'Суббота': [],
                    'Воскресенье': []
                }

                # Распределяем уроки по дням недели
                for lesson in lessons:
                    try:
                        day_num = lesson['date'].weekday()
                        day_name = list(week_lessons.keys())[day_num]
                        week_lessons[day_name].append(lesson)
                    except (KeyError, IndexError) as e:
                        print(f"Ошибка обработки урока: {e}")
                        continue

                response = "📅 Уроки на текущую неделю:\n\n"

                # Русские названия дней недели
                days_translation = {
                    'Monday': 'Понедельник',
                    'Tuesday': 'Вторник',
                    'Wednesday': 'Среда',
                    'Thursday': 'Четверг',
                    'Friday': 'Пятница',
                    'Saturday': 'Суббота',
                    'Sunday': 'Воскресенье'
                }

                for day, lessons in week_lessons.items():
                    day_name = days_translation.get(day, day)
                    response += f"📌 <b>{day_name}</b>\n"

                    for lesson in lessons:
                        response += f"   📖 {lesson['lesson_name']}\n"
                        response += f"   📝 {lesson['lesson_description']}\n"
                        if lesson['paths_for_files']:
                            response += f"   📎 Файлы: {lesson['paths_for_files']}\n"
                        response += "\n"

                return response

        except Error as err:
            print(f"Ошибка при работе с базой данных: {err}")
            return {}
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return {}

    def fillListHWForNextWeek(self):
        """Получение уроков на текущую неделю"""
        try:
            # Получаем текущую дату и границы недели
            today = datetime.now().date()
            next_monday = today + timedelta(days=(7 - today.weekday()))
            next_sunday = next_monday + timedelta(days=6)
            # Проверяем соединение с БД
            if not self.connection or not self.connection.is_connected():
                self.connect()

            with self.connection.cursor(dictionary=True) as cursor:
                # Выполняем запрос к БД
                query = """
                           SELECT id, lesson_name, date, lesson_description, paths_for_files 
                           FROM lesson 
                           WHERE date BETWEEN %s AND %s
                           ORDER BY date
                       """
                cursor.execute(query, (next_monday, next_sunday))
                lessons = cursor.fetchall()

                # Инициализируем структуру для хранения уроков по дням
                week_lessons = {
                    'Понедельник': [],
                    'Вторник': [],
                    'Среда': [],
                    'Четверг': [],
                    'Пятница': [],
                    'Суббота': [],
                    'Воскресенье': []
                }

                # Распределяем уроки по дням недели
                for lesson in lessons:
                    try:
                        day_num = lesson['date'].weekday()
                        day_name = list(week_lessons.keys())[day_num]
                        week_lessons[day_name].append(lesson)
                    except (KeyError, IndexError) as e:
                        print(f"Ошибка обработки урока: {e}")
                        continue

                response = "📅 Уроки на текущую неделю:\n\n"

                # Русские названия дней недели
                days_translation = {
                    'Monday': 'Понедельник',
                    'Tuesday': 'Вторник',
                    'Wednesday': 'Среда',
                    'Thursday': 'Четверг',
                    'Friday': 'Пятница',
                    'Saturday': 'Суббота',
                    'Sunday': 'Воскресенье'
                }

                for day, lessons in week_lessons.items():
                    day_name = days_translation.get(day, day)
                    response += f"📌 <b>{day_name}</b>\n"

                    for lesson in lessons:
                        response += f"   📖 {lesson['lesson_name']}\n"
                        response += f"   📝 {lesson['lesson_description']}\n"
                        if lesson['paths_for_files']:
                            response += f"   📎 Файлы: {lesson['paths_for_files']}\n"
                        response += "\n"

                return response

        except Error as err:
            print(f"Ошибка при работе с базой данных: {err}")
            return {}
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return {}

    def addHW(self, lesson: Lesson):
        try:
            with self.connection.cursor() as cursor:
                query = """
                      INSERT INTO lesson 
                      (lesson_name, date, lesson_description, paths_for_files)
                      VALUES (%s, %s, %s, %s)
                  """
                cursor.execute(query, (
                    lesson.get_title(),
                    lesson.date,
                    lesson.get_hw_text(),
                    lesson.get_file_path()
                ))
                self.connection.commit()
                print(f"Урок '{lesson.get_title()}' успешно добавлен")
                return cursor.lastrowid  # Возвращаем ID новой записи

        except Error as err:
            print(f"Ошибка при добавлении урока: {err}")
            self.connection.rollback()
            return None

    def removeHWLastWeek(self):
        try:
            today = datetime.now().date()

            last_week_monday = today - timedelta(days=today.weekday() + 7)
            last_week_sunday = last_week_monday + timedelta(days=6)

            with self.connection.cursor() as cursor:
                query = """
                       DELETE FROM lesson 
                       WHERE date BETWEEN %s AND %s
                   """
                cursor.execute(query, (last_week_monday, last_week_sunday))
                deleted_rows = cursor.rowcount
                self.connection.commit()

                print(f"Удалено записей за прошлую неделю: {deleted_rows}")
                return deleted_rows  # Возвращаем количество удаленных записей

        except Error as err:
            print(f"Ошибка при удалении записей: {err}")
            self.connection.rollback()
            return 0
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return 0

    def removeAdmin(self, user_id):
        try:
            with self.connection.cursor() as cursor:

                query = "DELETE FROM users WHERE user_id = %s"
                cursor.execute(query, (user_id,))
                if cursor.rowcount > 0:
                    self.connection.commit()
                    print(f"Пользователь {user_id} успешно удален")
                    return True
                else:
                    print(f"Пользователь {user_id} не найден")
                    return False
        except Error as err:
            print(f"Ошибка при удалении пользователя {user_id}: {err}")
            self.connection.rollback()
            return False

    def isAdmin(self, user_id):
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                query = "SELECT is_admin FROM users WHERE user_id = %s"
                cursor.execute(query, (user_id,))
                result = cursor.fetchone()

                if result and result['is_admin'] == 1:
                    return True
                return False

        except Error as err:
            print(f"Ошибка при проверке прав администратора: {err}")
            return False

    def getListAdmin(self):
        try:
            with self.connection.cursor() as cursor:
                query = "SELECT * from users"
                cursor.execute(query, )
                listAdmins = cursor.fetchall()
                return listAdmins
        except Error as err:
            print(f"Ошибка при получении списка администраторов:{err}")
            return None
