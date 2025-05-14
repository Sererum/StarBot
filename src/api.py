import datetime
import requests
from typing import List
from lesson import Lesson, LessonType

class APIClient:
    BASE_URL = "https://ruz.spbstu.ru/api/v1/ruz"
    ID_GROUP = "40446"

    def __init__(self):
        self.session = requests.Session()

    def _request(self, path: str, params: dict = None) -> dict:
        url = f"{self.BASE_URL}/{path}"
        try:
            resp = self.session.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"API request error: {e}")
            return {}

    def _parse_lessons_for_day(self, data: dict) -> List[Lesson]:
        lessons: List[Lesson] = []
        date = data.get("date", datetime.date.today().isoformat())

        for item in data.get("lessons", []):
            title = item.get("subject", "")
            time_start = item.get("time_start", "00:00")

            type_obj = item.get("typeObj", []) 
            lesson_type = LessonType.UNDEF
            if type_obj != []:
                abbr = type_obj.get("abbr", "")
                if (abbr == "Лек"):
                    lesson_type = LessonType.LECT
                if (abbr == "Пр"):
                    lesson_type = LessonType.PRACT
                if (abbr == "Лаб"):
                    lesson_type = LessonType.LAB

            addit = item.get("additional_info", "")
            if "п/г" in addit and addit[-1] != "1":
                continue

            lessons.append(
                Lesson(
                    title=title,
                    lesson_type=lesson_type,
                    date=date,
                    time_str=time_start,
                    has_hw=False,
                    hw_text="",
                    has_file=False,
                    file_path="",
                )
            )
        return lessons

    def get_list_for_date(self, target_date: datetime.date) -> List[Lesson]:
        data_on_week = self._request(f"scheduler/{self.ID_GROUP}", params={
            "date": target_date.strftime("%Y-%m-%d")
        })

        days = data_on_week.get("days", [])
        print(len(days))
        print(target_date.weekday())
        if target_date.weekday() >= len(days):
            print("В этот день нет занятий!")
            return []

        day = days[target_date.weekday()] 
        return self._parse_lessons_for_day(day)

    def getListLessonsForToday(self) -> List[Lesson]:
        return self.get_list_for_date(datetime.date.today())

    def getListLessonsForTomorrow(self) -> List[Lesson]:
        return self.get_list_for_date(datetime.date.today() + datetime.timedelta(days=1))

    def getListLessonsForWeek(self) -> List[Lesson]:
        cur_date = datetime.date.today()
        start_date = cur_date - datetime.timedelta(days=cur_date.weekday())

        lessons = []
        for i in range(6):
            date = start_date + datetime.timedelta(days=i)
            lessons.extend(self.get_list_for_date(date))

        return lessons 

    def getListLessonsForNextWeek(self) -> List[Lesson]:
        next_week_date = datetime.date.today() + datetime.timedelta(days=7)
        start_date = next_week_date - datetime.timedelta(days=next_week_date.weekday())

        lessons = []
        for i in range(6):
            date = start_date + datetime.timedelta(days=i)
            lessons.extend(self.get_list_for_date(date))

        return lessons 

