import logging
from config.config import MYSQL_CONFIG
from lesson_managers.api import APIClient
from lesson_managers.database import Database
from lesson_managers.lesson import Lesson

logger = logging.getLogger(__name__)

class Compositor:
    def __init__(self, config=None):
        self.config = config or MYSQL_CONFIG
        self.api_client = APIClient()

    def getHWbyID(self, hw_id: int) -> Lesson: 
        lessons = []
        lessons.extend(self.mergeListsScheduleHWWeek())
        lessons.extend(self.mergeListsScheduleHWNextWeek())
        for lesson in lessons:
            if lesson.id == hw_id:
                print(f"LESSON: {str(lesson)}")
                return lesson
        return None

    def mergeListsScheduleHWToday(self) -> list[Lesson]:
        return self._merge(
            api_method=self.api_client.getListLessonsForToday,
            db_method=lambda db: db.getListHWForToday()
        )

    def mergeListsScheduleHWTomorrow(self) -> list[Lesson]:
        return self._merge(
            api_method=self.api_client.getListLessonsForTomorrow,
            db_method=lambda db: db.getListHWForTomorrow()
        )

    def mergeListsScheduleHWWeek(self) -> list[Lesson]:
        return self._merge(
            api_method=self.api_client.getListLessonsForWeek,
            db_method=lambda db: db.getListHWForWeek()
        )

    def mergeListsScheduleHWNextWeek(self) -> list[Lesson]:
        return self._merge(
            api_method=self.api_client.getListLessonsForNextWeek,
            db_method=lambda db: db.getListHWForNextWeek()
        )

    def getLongtermHW(self) -> list[Lesson]:
        return self.db.getLongtermHW();

    def _merge(self, api_method, db_method) -> list[Lesson]:
        # 1. Получаем расписание из API
        try:
            lessons = api_method()
            logger.info(f"API returned {len(lessons)} lessons")
        except Exception as e:
            logger.error(f"API error: {e}")
            return []

        # 2. Получаем домашки из базы
        hw_list = []
        try:
            with Database(self.config) as db:
                hw_list = db_method(db) or []
                print("\t\t\t", hw_list)
                if (hw_list):
                    print("\t\t\t", str(hw_list[0]))
                logger.info(f"DB returned {len(hw_list)} HW items")
        except Exception as e:
            logger.error(f"Database error: {e}")
            hw_list = []

        # 3. Строим словарь по ключу = уникальный id урока
        print(3)
        print(hw_list)
        hw_dict = {}
        for hw in hw_list:
            hw_dict[hw.id] = hw;
        print(hw_dict)

        # 4. Пробегаем по расписанию и «пришиваем» ДЗ по id
        for lesson in lessons:
            print(str(lesson))
            hw = hw_dict.get(lesson.id)
            print(str(hw))
            if not hw:
                continue
            # если в БД есть текст — ставим дома
            if getattr(hw, 'hw_text', None):
                lesson.set_hw_text(hw.hw_text)
                lesson.has_hw = True
            # если в БД есть файл — ставим файл
            if getattr(hw, 'file_path', None):
                lesson.set_file_path(hw.file_path)
                lesson.has_file = True
                lesson.has_hw = True

        return lessons
