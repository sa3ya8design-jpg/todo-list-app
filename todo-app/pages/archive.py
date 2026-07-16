"""完了プロジェクト一覧画面（アーカイブ済みプロジェクトを表示する）。"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st

import db
import logic
from task_row import render_task_row


def _render_archive_list() -> None:
    st.title("完了プロジェクト")
    st.caption("完了にしたプロジェクトの置き場所です。タスクと完了履歴は保持されます。")

    projects = [p for p in db.list_projects(include_archived=True) if p.is_archived]
    if not projects:
        st.caption("完了にしたプロジェクトはありません")

    for project in projects:
        col_color, col_name = st.columns([0.08, 0.92])
        with col_color:
            st.markdown(
                f'<div style="width:20px;height:20px;border-radius:50%;'
                f'background:{project.color};margin-top:8px;"></div>',
                unsafe_allow_html=True,
            )
        with col_name:
            if st.button(project.name, key=f"open_archived_{project.id}", use_container_width=True):
                st.session_state["archive_selected_project_id"] = project.id
                st.rerun()


def _render_archived_project_detail(project_id: str) -> None:
    project = db.get_project(project_id)
    if project is None:
        st.session_state.pop("archive_selected_project_id", None)
        st.rerun()
        return

    if st.button("← 完了プロジェクト一覧に戻る"):
        st.session_state.pop("archive_selected_project_id", None)
        st.rerun()

    st.title(project.name)

    if st.button("進行中に戻す"):
        db.set_project_archived(project.id, False)
        st.session_state.pop("archive_selected_project_id", None)
        st.rerun()

    tasks = logic.sort_tasks(db.list_tasks(project_id=project.id, include_completed=True))
    incomplete = [t for t in tasks if not t.completed]
    completed = [t for t in tasks if t.completed]

    st.subheader("未完了タスク")
    if not incomplete:
        st.caption("未完了タスクはありません")
    for task in incomplete:
        render_task_row(task, show_postpone=False)

    with st.expander(f"完了したタスク（{len(completed)}）"):
        if not completed:
            st.caption("完了したタスクはありません")
        for task in completed:
            render_task_row(task, show_postpone=False)


selected_id = st.session_state.get("archive_selected_project_id")
if selected_id:
    _render_archived_project_detail(selected_id)
else:
    _render_archive_list()
