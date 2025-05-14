from enum import Enum
import hashlib

class LessonType(Enum):
    LECT = "Лекция"
    LAB = "Лабораторная"
    PRACT = "Практика"
    UNDEF = "???"

class Lesson:
    def __init__(self, title: str, lesson_type: LessonType, date: str, time_str: str,
                 has_hw: bool = False, hw_text: str = None,
                 has_file: bool = False, file_path: str = None):
        self.title = title
        self.lesson_type = lesson_type
        self.date = date  # YYYY-MM-DD
        self.time = time_str  # HH:MM
        self.has_hw = has_hw
        self.hw_text = hw_text
        self.has_file = has_file
        self.file_path = file_path 

        # Generate deterministic ID based on title + timestamp
        unique_str = f"{title}-{self.date}-{self.time}"
        self.id = int(hashlib.sha256(unique_str.encode()).hexdigest(), 16) & ((1<<63)-1)

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
