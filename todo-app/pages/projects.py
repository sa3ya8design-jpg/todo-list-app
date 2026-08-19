"""プロジェクト一覧・詳細画面。"""

import sys
from datetime import date
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st

import db
import logic
from models import KIND_LABELS, STATUS_LABELS, Status, format_amount
from project_modal import open_project_modal
from task_modal import open_task_modal
from task_row import render_task_row

QUICK_FILTERS = ["すべて", "今日", "期限切れ", "高優先度"]

STATUS_LABEL_TO_VALUE: dict[str, Status] = {v: k for k, v in STATUS_LABELS.items()}


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

    if st.button("新しいプロジェクト", icon=":material/add:", type="primary"):
        open_project_modal(None)

    projects = db.list_projects(include_completed=False)
    if not projects:
        st.caption("プロジェクトはまだありません")

    for project in projects:
        col_color, col_name, col_status = st.columns([0.08, 0.72, 0.2])
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
        with col_status:
            st.markdown(
                f'<div style="margin-top:8px;text-align:right;color:#6B7280;">'
                f'{STATUS_LABELS[project.status]}</div>',
                unsafe_allow_html=True,
            )


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

    # ステータスは保存ボタンなしで即時変更する。「完了」を選ぶと完了プロジェクトへ移動
    status_key = f"status_select_{project.id}"
    # 他の場所（編集モーダル等）での変更を確実に反映するため、毎回DBの値で上書きする
    st.session_state[status_key] = STATUS_LABELS[project.status]

    def _on_status_change() -> None:
        new_label = st.session_state[status_key]
        if new_label is None:
            # segmented_controlは選択中のものを再クリックすると選択解除されるため、
            # ステータス未選択にはならないよう何もしない（次の再描画で現在値に戻る）
            return
        new_status = STATUS_LABEL_TO_VALUE[new_label]
        if new_status == project.status:
            return
        db.set_project_status(project.id, new_status)
        if new_status == "completed":
            st.session_state["_completed_toast"] = (
                f"「{project.name}」を完了プロジェクトへ移動しました"
            )
            st.session_state.pop("selected_project_id", None)

    st.segmented_control(
        "ステータス",
        list(STATUS_LABELS.values()),
        key=status_key,
        on_change=_on_status_change,
    )
    meta_parts = [f"種類: {KIND_LABELS[project.kind]}"]
    amount_text = format_amount(project.amount)
    if amount_text:
        meta_parts.append(f"受注金額: {amount_text}")
    st.caption(" ・ ".join(meta_parts))

    if st.button("新しいタスク", icon=":material/add:", type="primary"):
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
