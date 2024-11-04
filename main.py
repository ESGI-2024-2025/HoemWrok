import json
import uuid
from datetime import timedelta
from typing import Dict, List

import ics
from fastapi import FastAPI
from fastapi.responses import FileResponse


class Homework:

    def __init__(
        self,
        uid: int,
        subject: str,
        due_date: str,
        due_time: str,
        priority: int,
        description: str,
    ) -> None:
        self.uid = uid
        self.subject = subject
        self.due_date = due_date
        self.due_time = due_time
        self.priority = priority
        self.description = description

    def get_uid(self) -> int:
        return self.uid

    def get_subject(self) -> int:
        return self.subject

    def get_due_date(self) -> str:
        return self.due_date

    def get_due_time(self) -> str:
        return self.due_time

    def get_priority(self) -> int:
        return self.priority

    def get_description(self) -> str:
        return self.description

    def __str__(self) -> str:
        return f"""UID: {self.uid}\nSubject: {self.subject}\nDue Date: {self.due_date}\nDue Time: {self.due_time}\nPriority: {self.priority}\nDescription: {self.description}"""

    def set_uid(self, uid: int) -> None:
        self.uid = uid

    def set_subject(self, subject: int) -> None:
        self.subject = subject

    def set_due_date(self, due_date: str) -> None:
        self.due_date = due_date

    def set_due_time(self, due_time: str) -> None:
        self.due_time = due_time

    def set_priority(self, priority: int) -> None:
        self.priority = priority

    def set_description(self, description: str) -> None:
        self.description = description

    def format_to_event(self) -> ics.event.Event:
        event = ics.Event()
        event.uid = str(self.uid)
        event.name = self.subject
        event.begin = self.due_date + " " + self.due_time
        event.end = event.begin + timedelta(hours=1, minutes=30)
        event.description = (
            f"""Priority: {self.priority}\nDescription: {self.description}"""
        )
        return event

    def format_to_json(self) -> Dict:
        json_obj = {
            "uid": self.uid,
            "subject": self.subject,
            "due_date": self.due_date,
            "due_time": self.due_time,
            "priority": self.priority,
            "description": self.description,
        }
        return json_obj


class Calendar:

    def __init__(self) -> None:
        self.calendar = ics.Calendar()
        self.homeworks = []
        self.load_config()
        self.load_homeworks()

    def load_config(self, config_path: str = "config.json") -> None:
        with open(config_path, "r") as config_file:
            self.config = json.load(config_file)["calendar"]
            config_file.close()

    def get_config(self) -> Dict:
        return self.config

    def load_homeworks(self) -> List[Homework]:
        with open(self.config["db_path"], "r") as homeworks_file:
            for homework in json.load(homeworks_file)["homeworks"]:
                self.homeworks.append(
                    Homework(
                        uid=homework["uid"],
                        subject=homework["subject"],
                        due_date=homework["due_date"],
                        due_time=homework["due_time"],
                        priority=homework["priority"],
                        description=homework["description"],
                    )
                )
            homeworks_file.close()
        return self.homeworks

    def generate_homeworks_calendar(self) -> str:
        for homework in self.load_homeworks():
            print(homework)
            self.calendar.events.add(homework.format_to_event())
        with open(self.config["file_path"], "w") as calendar_file:
            calendar_file.writelines(self.calendar.serialize())
            calendar_file.close()
        return self.config["file_path"]


class AppUtils:

    def __init__(self) -> None:
        self.load_config()
        self.calendar = Calendar()

    def load_config(self, file_path: str = "./config.json") -> None:
        with open(file_path) as configFile:
            self.config = json.load(configFile)
            configFile.close()

    def get_info(self) -> dict:
        return self.config

    def get_calendar(self) -> str:
        self.calendar.generate_homeworks_calendar()
        return self.calendar.get_config()["file_path"]

    def add_homework(self, homework: Homework) -> bool:
        homeworks = []
        with open(self.calendar.get_config()["db_path"], "r") as homeworks_file:
            homeworks = json.load(homeworks_file)
            homeworks_file.close()

        homeworks["homeworks"].append(homework.format_to_json())

        with open(self.calendar.get_config()["db_path"], "w") as homeworks_file:
            homeworks_file.write(json.dumps(homeworks))
            homeworks_file.close()

        return True


app_utils = AppUtils()

app = FastAPI()


@app.get("/config")
def read_root() -> Dict:
    return {"config": app_utils.get_info()}


@app.get("/")
def read_homeworks() -> FileResponse:
    return FileResponse(
        app_utils.get_calendar(),
        media_type="text/calendar",
    )


@app.post("/add")
def post_add_homework(
    name: str, due_date: str, due_time: str, priority: int, description: str
) -> Dict:
    homework = Homework(
        uid=uuid.uuid4().int,
        subject=name,
        due_date=due_date,
        due_time=due_time,
        priority=priority,
        description=description,
    )
    if app_utils.add_homework(homework):
        return {"message": "Homework added successfully"}
    else:
        return {"message": "Error adding homework"}
