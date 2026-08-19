"""ホーム画面（未完了タスクのグループ表示）。"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st

import db
import logic
from task_modal import open_task_modal
from task_row import render_task_row

st.title("ホーム")
st.caption("今やるべきこと")

if st.button("新しいタスク", icon=":material/add:", type="primary"):
    open_task_modal(None)

tasks = db.list_tasks(include_completed=False)
grouped = logic.group_tasks(tasks)

# どのプロジェクトのタスクか分かるように、行表示にプロジェクト情報を渡す
projects_by_id = {p.id: p for p in db.list_projects()}

if "today" not in grouped:
    st.info("今日のタスクはありません")

for group_key, group_tasks in grouped.items():
    st.subheader(logic.HOME_GROUP_LABELS[group_key])
    for task in group_tasks:
        render_task_row(task, project=projects_by_id.get(task.project_id))

# 誤って完了にしたタスクをすぐ戻せるように、完了済みも折りたたみで表示する
completed = [t for t in db.list_tasks(include_completed=True) if t.completed]
completed.sort(key=lambda t: t.completed_at or t.created_at, reverse=True)
with st.expander(f"完了したタスク（{len(completed)}）"):
    if not completed:
        st.caption("完了したタスクはありません")
    for task in completed:
        render_task_row(task, show_postpone=False, project=projects_by_id.get(task.project_id))
