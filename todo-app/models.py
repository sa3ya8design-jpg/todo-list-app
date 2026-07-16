"""Project / Task のデータの形を定義するモジュール。"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

Priority = Literal["high", "medium", "low"]


@dataclass
class Project:
    id: str
    name: str
    color: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class Task:
    id: str
    project_id: str | None
    title: str
    memo: str
    priority: Priority
    due_date: date | None
    completed: bool
    completed_at: datetime | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
