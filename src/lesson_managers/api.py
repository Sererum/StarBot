import datetime
import logging
from typing import List, Optional

import requests
from lesson_managers.lesson import Lesson, LessonType

logger = logging.getLogger(__name__)

class APIClient:
    BASE_URL = "https://ruz.spbstu.ru/api/v1/ruz"
    ID_GROUP = "40446"
    WEEK_DAYS = 6

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def _request(self, path: str, params: dict = None) -> dict:
        url = f"{self.BASE_URL}/{path}"
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"API request error for {url}: {e}")
            raise

    def _parse_lesson(self, item: dict, date: str) -> Optional[Lesson]:
        # Определяем тип занятия из typeObj
        lesson_type = LessonType.UNDEF
        types = item.get("typeObj") or {} 
        if types != {} and isinstance(types, dict):
            abbr = types.get("abbr", "")
            mapping = {
                "Лек": LessonType.LECT,
                "Пр":  LessonType.PRACT,
                "Лаб": LessonType.LAB,
                "Кпр": LessonType.COURSE,
                "ЗаО": LessonType.DIF,
                "Зч":  LessonType.TEST,
                "Конс": LessonType.CONS,
                "Экз": LessonType.EXAM,
            }
            lesson_type = mapping.get(abbr, LessonType.UNDEF)
            if lesson_type == LessonType.UNDEF:
                logger.debug(f"NEW ABBR: {abbr}")

        # Фильтр: только основная группа
        addit = item.get("additional_info", "")
        if self._is_subgroup(addit):
            return None

        lesson = Lesson(
            title=item.get("subject", ""),
            lesson_type=lesson_type,
            date=date,
            time_str=item.get("time_start", "00:00"),
            has_hw=False,
            hw_text="",
            has_file=False,
            file_path="",
        )
        return lesson;

    @staticmethod
    def _is_subgroup(additional_info: str) -> bool:
        # Если "п/г" и не заканчивается на "1" — это подгруппа
        return "п/г" in additional_info and not additional_info.endswith("1")

    def _getListForDate(self, target_date: datetime.date) -> List[Lesson]:
        data = self._request(
            f"scheduler/{self.ID_GROUP}",
            {"date": target_date.isoformat()}
        )
        days = data.get("days", [])
        wd = target_date.weekday() + 1

        # Ищем в days запись с нужным weekday
        day = next((d for d in days if d.get("weekday") == wd), None)
        if not day:
            logger.info(f"No lessons on {target_date}")
            return []

        date_str = day.get("date", target_date.isoformat())
        lessons = []
        for item in day.get("lessons", []):
            lesson = self._parse_lesson(item, date_str)
            logger.info(str(lesson))
            if lesson:
                lessons.append(lesson)
        return lessons

    def getListLessonsForToday(self) -> List[Lesson]:
        return self._getListForDate(datetime.date.today())

    def getListLessonsForTomorrow(self) -> List[Lesson]:
        return self._getListForDate(datetime.date.today() + datetime.timedelta(days=1))

    def getListLessonsForWeek(self) -> List[Lesson]:
        return self._getLessonsByWeekOffset(0)

    def getListLessonsForNextWeek(self) -> List[Lesson]:
        return self._getLessonsByWeekOffset(1)

    def _getLessonsByWeekOffset(self, weeks_offset: int) -> List[Lesson]:
        today = datetime.date.today()
        # вычисляем понедельник нужной недели
        start = today + datetime.timedelta(days=7*weeks_offset - today.weekday())
        lessons: List[Lesson] = []
        for i in range(self.WEEK_DAYS):
            day = start + datetime.timedelta(days=i)
            lessons.extend(self._getListForDate(day))
        return lessons
