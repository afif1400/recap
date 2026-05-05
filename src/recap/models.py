from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

EventCategory = Literal[
    "lab",
    "visit",
    "scan",
    "med",
    "note",
    "photo",
    "diagnosis",
    "procedure",
    "report",
    "other",
]


class Citation(BaseModel):
    source_id: str
    page: int | None = None
    snippet: str | None = None
    region: tuple[float, float, float, float] | None = None


class Event(BaseModel):
    id: str
    date: datetime
    category: EventCategory
    title: str
    source: str
    body: str = ""
    metadata: dict = Field(default_factory=dict)


class Patient(BaseModel):
    id: str
    display_name: str
    age: int | None = None
    gender: str | None = None  # "male" | "female" | "other"
    events: list[Event] = Field(default_factory=list)


class Answer(BaseModel):
    text: str
    citations: list[Citation] = Field(default_factory=list)
