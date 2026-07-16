"""プロジェクト一覧・詳細画面。"""

import sys
from datetime import date
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st

import db
import logic
from project_modal import open_project_modal
from task_modal import open_task_modal
from task_row import render_task_row

QUICK_FILTERS = ["すべて", "今日", "期限切れ", "高優先度"]


def _matches_filter(task, filter_choice: str, today: date) -> bool:
    if filter_choice == "今日":
        return task.due_date == today
    if filter_choice == "期限切れ":
        return task.due_date is not None and task.due_date < today
    if filter_choice == "高優先度":
        return task.priority == "high"
    return True


def _render_project_list() -> None:
    st.title("プロジェクト")

    if st.button("+ 新しいプロジェクト", type="primary"):
        open_project_modal(None)

    projects = db.list_projects(include_archived=False)
    if not projects:
        st.caption("プロジェクトはまだありません")

    for project in projects:
        col_color, col_name = st.columns([0.08, 0.92])
        with col_color:
            st.markdown(
                f'<div style="width:20px;height:20px;border-radius:50%;'
                f'background:{project.color};margin-top:8px;"></div>',
                unsafe_allow_html=True,
            )
        with col_name:
            if st.button(project.name, key=f"open_project_{project.id}", use_container_width=True):
                st.session_state["selected_project_id"] = project.id
                st.rerun()


def _render_project_detail(project_id: str) -> None:
    project = db.get_project(project_id)
    if project is None:
        st.session_state.pop("selected_project_id", None)
        st.rerun()
        return

    if st.button("← プロジェクト一覧に戻る"):
        st.session_state.pop("selected_project_id", None)
        st.rerun()

    col_title, col_edit = st.columns([0.8, 0.2])
    with col_title:
        st.title(project.name)
    with col_edit:
        if st.button("編集"):
            open_project_modal(project.id)

    if st.button("+ 新しいタスク", type="primary"):
        open_task_modal(None, default_project_id=project.id)

    filter_choice = st.segmented_control("フィルター", QUICK_FILTERS, default="すべて") or "すべて"

    incomplete = db.list_tasks(project_id=project.id, include_completed=False)
    today = date.today()
    filtered = [t for t in incomplete if _matches_filter(t, filter_choice, today)]
    filtered = logic.sort_tasks(filtered)

    if not filtered:
        st.caption("表示できるタスクはありません")
    for task in filtered:
        render_task_row(task, show_postpone=False)

    all_tasks = db.list_tasks(project_id=project.id, include_completed=True)
    completed = logic.sort_tasks([t for t in all_tasks if t.completed])
    with st.expander(f"完了したタスク（{len(completed)}）"):
        if not completed:
            st.caption("完了したタスクはありません")
        for task in completed:
            render_task_row(task, show_postpone=False)


selected_id = st.session_state.get("selected_project_id")
if selected_id:
    _render_project_detail(selected_id)
else:
    _render_project_list()
