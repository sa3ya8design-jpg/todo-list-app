"""データの保存・取得を Google スプレッドシートで行うモジュール。

公開関数のインターフェースは旧SQLite版と同じにしてあり、画面側のコードは変更不要。
1つのスプレッドシートに projects / tasks の2ワークシートを持ち、1行目をヘッダーとする。
Sheets APIは遅いため、読み取りは短時間キャッシュし、書き込み時にキャッシュを破棄する。

認証はサービスアカウント方式。鍵は .streamlit/secrets.toml の [gcp_service_account] に設定する。
公開サーバー（Streamlit Community Cloud等）では、ホスティング側のSecrets設定に同じ内容を入れる。
"""

import uuid
from datetime import date, datetime

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

from models import Priority, Project, Task

PROJECT_HEADERS = ["id", "name", "color", "is_archived", "created_at", "updated_at"]
TASK_HEADERS = [
    "id", "project_id", "title", "memo", "priority", "due_date",
    "completed", "completed_at", "sort_order", "created_at", "updated_at",
]

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
_CACHE_TTL_SECONDS = 60  # スプレッドシートを直接編集した場合も最大1分で反映される


# --- 接続 -------------------------------------------------------------------

def _secrets_ready() -> bool:
    try:
        return "spreadsheet_id" in st.secrets and "gcp_service_account" in st.secrets
    except Exception:
        return False


def init_db() -> None:
    """接続設定を確認し、ワークシートが無ければ作成する。"""
    if not _secrets_ready():
        st.error(
            "Google スプレッドシートの接続情報が未設定です。\n\n"
            "`todo-app/.streamlit/secrets.toml` に `spreadsheet_id` と "
            "`[gcp_service_account]`（サービスアカウントの鍵）を設定してください。\n"
            "雛形は `todo-app/.streamlit/secrets.toml.example` にあります。"
        )
        st.stop()
    _get_worksheets()


@st.cache_resource
def _get_worksheets() -> tuple[gspread.Worksheet, gspread.Worksheet]:
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=_SCOPES
    )
    spreadsheet = gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"])
    return (
        _ensure_worksheet(spreadsheet, "projects", PROJECT_HEADERS),
        _ensure_worksheet(spreadsheet, "tasks", TASK_HEADERS),
    )


def _ensure_worksheet(
    spreadsheet: gspread.Spreadsheet, title: str, headers: list[str]
) -> gspread.Worksheet:
    try:
        worksheet = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(headers))
    if not worksheet.row_values(1):
        worksheet.append_row(headers)
    return worksheet


# --- 読み取り（キャッシュ付き） ---------------------------------------------

@st.cache_data(ttl=_CACHE_TTL_SECONDS)
def _load_project_rows() -> list[dict]:
    projects_ws, _ = _get_worksheets()
    return projects_ws.get_all_records()


@st.cache_data(ttl=_CACHE_TTL_SECONDS)
def _load_task_rows() -> list[dict]:
    _, tasks_ws = _get_worksheets()
    return tasks_ws.get_all_records()


def _clear_cache() -> None:
    _load_project_rows.clear()
    _load_task_rows.clear()


def _row_number_by_id(rows: list[dict], entity_id: str) -> int | None:
    """キャッシュ済みの行リストからシート上の行番号を求める（1行目はヘッダー）。"""
    for index, row in enumerate(rows):
        if str(row["id"]) == entity_id:
            return index + 2
    return None


# --- 行 ⇔ モデルの変換 ------------------------------------------------------

def _row_to_project(row: dict) -> Project:
    return Project(
        id=str(row["id"]),
        name=str(row["name"]),
        color=str(row["color"]),
        is_archived=bool(int(row["is_archived"] or 0)),
        created_at=datetime.fromisoformat(str(row["created_at"])),
        updated_at=datetime.fromisoformat(str(row["updated_at"])),
    )


def _project_to_row(project: Project) -> list:
    return [
        project.id,
        project.name,
        project.color,
        int(project.is_archived),
        project.created_at.isoformat(),
        project.updated_at.isoformat(),
    ]


def _row_to_task(row: dict) -> Task:
    return Task(
        id=str(row["id"]),
        project_id=str(row["project_id"]) if row["project_id"] else None,
        title=str(row["title"]),
        memo=str(row["memo"]) if row["memo"] else "",
        priority=str(row["priority"]),
        due_date=date.fromisoformat(str(row["due_date"])) if row["due_date"] else None,
        completed=bool(int(row["completed"] or 0)),
        completed_at=datetime.fromisoformat(str(row["completed_at"])) if row["completed_at"] else None,
        sort_order=int(row["sort_order"] or 0),
        created_at=datetime.fromisoformat(str(row["created_at"])),
        updated_at=datetime.fromisoformat(str(row["updated_at"])),
    )


def _task_to_row(task: Task) -> list:
    return [
        task.id,
        task.project_id or "",
        task.title,
        task.memo,
        task.priority,
        task.due_date.isoformat() if task.due_date else "",
        int(task.completed),
        task.completed_at.isoformat() if task.completed_at else "",
        task.sort_order,
        task.created_at.isoformat(),
        task.updated_at.isoformat(),
    ]


# --- Project ---------------------------------------------------------------

def list_projects(include_archived: bool = True) -> list[Project]:
    projects = [_row_to_project(row) for row in _load_project_rows()]
    if not include_archived:
        projects = [p for p in projects if not p.is_archived]
    return sorted(projects, key=lambda p: p.created_at)


def get_project(project_id: str) -> Project | None:
    for row in _load_project_rows():
        if str(row["id"]) == project_id:
            return _row_to_project(row)
    return None


def create_project(name: str, color: str) -> Project:
    now = datetime.now()
    project = Project(
        id=str(uuid.uuid4()),
        name=name,
        color=color,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    projects_ws, _ = _get_worksheets()
    projects_ws.append_row(_project_to_row(project))
    _clear_cache()
    return project


def _write_project(project: Project) -> None:
    project.updated_at = datetime.now()
    projects_ws, _ = _get_worksheets()
    row_number = _row_number_by_id(_load_project_rows(), project.id)
    if row_number is not None:
        projects_ws.update(values=[_project_to_row(project)], range_name=f"A{row_number}")
    _clear_cache()


def update_project(project: Project) -> None:
    _write_project(project)


def delete_project(project_id: str) -> None:
    """プロジェクトと、そのプロジェクトに属するタスクをまとめて削除する。"""
    projects_ws, tasks_ws = _get_worksheets()

    task_rows = _load_task_rows()
    doomed = [
        index + 2
        for index, row in enumerate(task_rows)
        if str(row["project_id"]) == project_id
    ]
    for row_number in sorted(doomed, reverse=True):
        tasks_ws.delete_rows(row_number)

    row_number = _row_number_by_id(_load_project_rows(), project_id)
    if row_number is not None:
        projects_ws.delete_rows(row_number)
    _clear_cache()


def set_project_archived(project_id: str, is_archived: bool) -> None:
    project = get_project(project_id)
    if project is None:
        return
    project.is_archived = is_archived
    _write_project(project)


# --- Task --------------------------------------------------------------

def list_tasks(project_id: str | None = None, include_completed: bool = True) -> list[Task]:
    tasks = [_row_to_task(row) for row in _load_task_rows()]
    if project_id is not None:
        tasks = [t for t in tasks if t.project_id == project_id]
    if not include_completed:
        tasks = [t for t in tasks if not t.completed]
    return tasks


def get_task(task_id: str) -> Task | None:
    for row in _load_task_rows():
        if str(row["id"]) == task_id:
            return _row_to_task(row)
    return None


def create_task(
    title: str,
    project_id: str | None = None,
    memo: str = "",
    priority: Priority = "medium",
    due_date: date | None = None,
) -> Task:
    now = datetime.now()
    task = Task(
        id=str(uuid.uuid4()),
        project_id=project_id,
        title=title,
        memo=memo,
        priority=priority,
        due_date=due_date,
        completed=False,
        completed_at=None,
        sort_order=0,
        created_at=now,
        updated_at=now,
    )
    _, tasks_ws = _get_worksheets()
    tasks_ws.append_row(_task_to_row(task))
    _clear_cache()
    return task


def _write_task(task: Task) -> None:
    task.updated_at = datetime.now()
    _, tasks_ws = _get_worksheets()
    row_number = _row_number_by_id(_load_task_rows(), task.id)
    if row_number is not None:
        tasks_ws.update(values=[_task_to_row(task)], range_name=f"A{row_number}")
    _clear_cache()


def update_task(task: Task) -> None:
    _write_task(task)


def delete_task(task_id: str) -> None:
    _, tasks_ws = _get_worksheets()
    row_number = _row_number_by_id(_load_task_rows(), task_id)
    if row_number is not None:
        tasks_ws.delete_rows(row_number)
    _clear_cache()


def set_task_completed(task_id: str, completed: bool) -> None:
    task = get_task(task_id)
    if task is None:
        return
    task.completed = completed
    task.completed_at = datetime.now() if completed else None
    _write_task(task)


def postpone_task(task_id: str, new_due_date: date) -> None:
    task = get_task(task_id)
    if task is None:
        return
    task.due_date = new_due_date
    _write_task(task)
