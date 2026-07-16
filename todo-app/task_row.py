"""タスク一覧の1行表示（チェックボックス＋タイトル＋優先度/期限）を共通化するモジュール。

ホーム画面・プロジェクト詳細画面の両方から使う。
"""

from datetime import date, timedelta

import streamlit as st

import db
import logic
from colors import color_emoji
from models import Project
from task_modal import PRIORITY_LABELS, open_task_modal


def render_task_row(task, *, show_postpone: bool = True, project: Project | None = None) -> None:
    """タスクを1行表示する。projectを渡すと所属プロジェクト名（カラー付き）も表示する。"""
    if show_postpone:
        col_check, col_main, col_postpone = st.columns([0.08, 0.72, 0.2])
    else:
        col_check, col_main = st.columns([0.08, 0.92])

    with col_check:
        checked = st.checkbox(
            "完了", value=task.completed, key=f"complete_{task.id}", label_visibility="collapsed"
        )
        if checked != task.completed:
            db.set_task_completed(task.id, checked)
            if checked:
                # 再実行をまたいで表示するため、トーストはapp.py側で出す
                st.session_state["_completed_toast"] = (
                    f"「{task.title}」を完了しました（『完了したタスク』から戻せます）"
                )
            st.rerun()

    with col_main:
        if st.button(task.title, key=f"open_{task.id}", use_container_width=True):
            open_task_modal(task.id)
        due_text = task.due_date.strftime("%Y/%m/%d") if task.due_date else "期限なし"
        parts = []
        if project is not None:
            parts.append(f"{color_emoji(project.color)} {project.name}")
        parts.append(f"優先度: {PRIORITY_LABELS[task.priority]}")
        parts.append(due_text)
        st.caption(" ・ ".join(parts))

    if show_postpone:
        with col_postpone:
            _postpone_menu(task.id)


def _postpone_menu(task_id: str) -> None:
    today = date.today()
    with st.popover("延期"):
        if st.button("明日", key=f"postpone_tomorrow_{task_id}"):
            db.postpone_task(task_id, today + timedelta(days=1))
            st.rerun()
        if st.button("今週末", key=f"postpone_weekend_{task_id}"):
            db.postpone_task(task_id, logic.week_end(today))
            st.rerun()
        if st.button("来週", key=f"postpone_nextweek_{task_id}"):
            days_to_next_monday = (7 - today.weekday()) % 7 or 7
            db.postpone_task(task_id, today + timedelta(days=days_to_next_monday))
            st.rerun()

        def _on_date_pick() -> None:
            picked = st.session_state[f"postpone_date_{task_id}"]
            if picked:
                db.postpone_task(task_id, picked)

        st.date_input("日付選択", value=None, key=f"postpone_date_{task_id}", on_change=_on_date_pick)
