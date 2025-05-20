from api import APIClient
from src.config import MYSQL_CONFIG
from src.database import Database
from src.lesson import Lesson
from datetime import datetime


class Compositor:
    def __init__(self, config=None, ):
        self.config = config
        self.api_client = APIClient()

    def __enter__(self):

        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        self.close()

    def connect(self):

        pass

    def close(self):

        pass

    def mergeListsScheduleHWToday(self) -> list[Lesson]:

        lessons = self.api_client.getListLessonsForToday()

        with Database(MYSQL_CONFIG) as database:
            hw_list = database.fillListHWForToday()

            hw_dict = {hw.get_title(): hw for hw in hw_list}

        for lesson in lessons:
            if lesson.get_title() in hw_dict:
                hw = hw_dict[lesson.get_title()]
                lesson.set_hw_text(hw.get_hw_text())
                lesson.set_file_path(hw.get_file_path())
                lesson.has_hw = bool(hw.get_hw_text())
                lesson.has_file = bool(hw.get_file_path())

        return lessons

    def mergeListsScheduleHWTomorrow(self) -> list[Lesson]:
        lessons = self.api_client.getListLessonsForTomorrow()

        with Database(MYSQL_CONFIG) as database:
            hw_list = database.fillListHWForTomorrow()
            hw_dict = {hw.get_title(): hw for hw in hw_list}
        for lesson in lessons:
            if lesson.get_title() in hw_dict:
                hw = hw_dict[lesson.get_title()]
                lesson.set_hw_text(hw.get_hw_text())
                lesson.set_file_path(hw.get_file_path())
                lesson.has_hw = bool(hw.get_hw_text())
                lesson.has_file = bool(hw.get_file_path())

        return lessons

    def mergeListsScheduleHWWeek(self) -> list[Lesson]:
        lessons = self.api_client.getListLessonsForWeek()

        with Database(MYSQL_CONFIG) as database:
            hw_list = database.fillListHWForWeek()

            # Создаем словарь с нормализованными ключами
            hw_dict = {}
            for hw in hw_list:
                if hw and hw.get_title() and hw.get_date():
                    # Получаем дату (уже в формате datetime.date)
                    hw_date = hw.get_date()
                    if isinstance(hw_date, str):
                        # Если дата пришла как строка, преобразуем в date
                        try:
                            hw_date = datetime.strptime(hw_date, "%Y-%m-%d").date()
                        except ValueError:
                            continue

                    key = (
                        hw.get_title().strip().lower(),  # Нормализованное название
                        hw_date.isoformat()  # Дата в формате YYYY-MM-DD
                    )
                    hw_dict[key] = hw

        for lesson in lessons:
            if not lesson or not lesson.get_title() or not lesson.get_date():
                continue

            # Обрабатываем дату урока
            lesson_date = lesson.get_date()
            if isinstance(lesson_date, str):
                try:
                    lesson_date = datetime.strptime(lesson_date, "%Y-%m-%d").date()
                except ValueError:
                    continue

            lesson_key = (
                lesson.get_title().strip().lower(),
                lesson_date.isoformat()
            )

            if lesson_key in hw_dict:
                hw = hw_dict[lesson_key]
                if hw.get_hw_text():
                    lesson.set_hw_text(hw.get_hw_text())
                if hw.get_file_path():
                    lesson.set_file_path(hw.get_file_path())

        return lessons

    def mergeListsScheduleHWNextWeek(self) -> list[Lesson]:
        lessons = self.api_client.getListLessonsForNextWeek()

        with Database(MYSQL_CONFIG) as database:
            hw_list = database.fillListHWForNextWeek()

            # Создаем словарь с нормализованными ключами
            hw_dict = {}
            for hw in hw_list:
                if hw and hw.get_title() and hw.get_date():
                    # Получаем дату (уже в формате datetime.date)
                    hw_date = hw.get_date()
                    if isinstance(hw_date, str):
                        # Если дата пришла как строка, преобразуем в date
                        try:
                            hw_date = datetime.strptime(hw_date, "%Y-%m-%d").date()
                        except ValueError:
                            continue

                    key = (
                        hw.get_title().strip().lower(),  # Нормализованное название
                        hw_date.isoformat()  # Дата в формате YYYY-MM-DD
                    )
                    hw_dict[key] = hw

        for lesson in lessons:
            if not lesson or not lesson.get_title() or not lesson.get_date():
                continue

            # Обрабатываем дату урока
            lesson_date = lesson.get_date()
            if isinstance(lesson_date, str):
                try:
                    lesson_date = datetime.strptime(lesson_date, "%Y-%m-%d").date()
                except ValueError:
                    continue

            lesson_key = (
                lesson.get_title().strip().lower(),
                lesson_date.isoformat()
            )

            if lesson_key in hw_dict:
                hw = hw_dict[lesson_key]
                if hw.get_hw_text():
                    lesson.set_hw_text(hw.get_hw_text())
                if hw.get_file_path():
                    lesson.set_file_path(hw.get_file_path())

        return lessons
