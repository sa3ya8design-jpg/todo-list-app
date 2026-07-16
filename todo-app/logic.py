"""「今日 / 期限切れ」などの並び替え・グループ分けロジック。"""

from datetime import date, timedelta

from models import Priority, Task

PRIORITY_ORDER: dict[Priority, int] = {"high": 0, "medium": 1, "low": 2}

HOME_GROUPS = (
    "overdue",
    "today",
    "tomorrow",
    "this_week",
    "this_month",
    "later",
    "no_due_date",
)

HOME_GROUP_LABELS: dict[str, str] = {
    "overdue": "期限切れ",
    "today": "今日",
    "tomorrow": "明日",
    "this_week": "今週",
    "this_month": "今月",
    "later": "それ以降",
    "no_due_date": "期限なし",
}


def week_end(today: date) -> date:
    """今週の土曜日を返す。"""
    if today.weekday() == 5:
        return today
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    return today + timedelta(days=days_until_saturday)


def _month_end(today: date) -> date:
    next_month = today.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def classify_task_group(task: Task, today: date | None = None) -> str:
    """タスクをホーム画面のグループに分類する。"""
    today = today or date.today()

    if task.due_date is None:
        return "no_due_date"
    if task.due_date < today:
        return "overdue"
    if task.due_date == today:
        return "today"
    if task.due_date == today + timedelta(days=1):
        return "tomorrow"
    if task.due_date <= week_end(today):
        return "this_week"
    if task.due_date <= _month_end(today):
        return "this_month"
    return "later"


def sort_tasks(tasks: list[Task]) -> list[Task]:
    """優先度 → 期限 → 作成日時 の順で並べ替える。"""
    return sorted(
        tasks,
        key=lambda t: (
            PRIORITY_ORDER[t.priority],
            t.due_date or date.max,
            t.created_at,
        ),
    )


def group_tasks(tasks: list[Task], today: date | None = None) -> dict[str, list[Task]]:
    """未完了タスクをホーム画面用のグループに分ける。空のグループは含めない。"""
    today = today or date.today()
    grouped: dict[str, list[Task]] = {key: [] for key in HOME_GROUPS}

    for task in tasks:
        if task.completed:
            continue
        grouped[classify_task_group(task, today)].append(task)

    return {
        key: sort_tasks(items)
        for key, items in grouped.items()
        if items
    }
