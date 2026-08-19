"""Project / Task / ProcessStep のデータの形を定義するモジュール。"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

Priority = Literal["high", "medium", "low"]

Status = Literal["proposal", "ordered", "in_progress", "invoiced", "completed"]

STATUS_LABELS: dict[Status, str] = {
    "proposal": "提案中",
    "ordered": "受注済",
    "in_progress": "作業中",
    "invoiced": "請求済",
    "completed": "完了",
}

Kind = Literal["design", "ai_system", "resale", "other"]

KIND_LABELS: dict[Kind, str] = {
    "design": "デザイン",
    "ai_system": "AIシステム開発",
    "resale": "古着物販",
    "other": "その他",
}


@dataclass
class Project:
    id: str
    name: str
    color: str
    status: Status
    kind: Kind
    amount: int | None  # 受注金額（税込・円）。未入力はNone
    created_at: datetime
    updated_at: datetime

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"


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


@dataclass
class ProcessStep:
    """工程マスタの1行。default_kindsに含まれる種類の案件でデフォルトONになる。"""

    id: str
    name: str
    sort_order: int
    default_kinds: set[Kind] = field(default_factory=set)


def format_amount(amount: int | None) -> str | None:
    """受注金額の表示用文字列（未入力ならNone）。"""
    return f"¥{amount:,}" if amount is not None else None
