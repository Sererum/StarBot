from enum import Enum
import hashlib
from datetime import datetime

class LessonType(Enum):
    LECT = "Лекция"
    LAB = "Лабораторная"
    PRACT = "Практика"
    UNDEF = "???"


class Lesson:
    def __init__(
            self,
            title: str = None,  # Необязательный (по умолчанию None)
            lesson_type: LessonType = LessonType.UNDEF,  # По умолчанию "???"
            date: str = None,  # Можно установить текущую дату
            time_str: str = None,  # Можно установить текущее время
            has_hw: bool = False,  # Уже необязательный
            hw_text: str = None,  # Уже необязательный
            has_file: bool = False,  # Уже необязательный
            file_path: str = None  # Уже необязательный
    ):
        self.title = title or "Без названия"  # Если None, заменяем на "Без названия"
        self.lesson_type = lesson_type
        self.date = date or datetime.now().strftime("%Y-%m-%d")  # Текущая дата, если не задана
        self.time = time_str or datetime.now().strftime("%H:%M")  # Текущее время, если не задано
        self.has_hw = has_hw
        self.hw_text = hw_text
        self.has_file = has_file
        self.file_path = file_path

        # Генерация ID (если title=None, всё равно сработает)
        unique_str = f"{self.title}-{self.date}-{self.time}"
        self.id = int(hashlib.sha256(unique_str.encode()).hexdigest(), 16) & ((1 << 63) - 1)


    # Getters and setters
    def get_id(self) -> int:
        return self.id

    def get_title(self) -> str:
        return self.title

    def set_title(self, title: str):
        self.title = title

    def get_lesson_type(self) -> LessonType:
        return self.lesson_type

    def set_lesson_type(self, lesson_type: LessonType):
        self.lesson_type = lesson_type

    def get_date(self) -> str:
        return self.date

    def set_date(self, date: str):
        self.date = date

    def get_time(self) -> str:
        return self.time

    def set_time(self, time_str: str):
        self.time = time_str

    def get_hw_text(self) -> str:
        return self.hw_text

    def set_hw_text(self, text: str):
        self.hw_text = text
        self.has_hw = bool(text)

    def get_file_path(self) -> str:
        return self.file_path

    def set_file_path(self, path: str):
        self.file_path = path
        self.has_file = bool(path)
