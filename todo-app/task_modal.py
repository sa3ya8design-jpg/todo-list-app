"""タスク作成・編集モーダル（「保存」で確定して閉じる）。"""

import streamlit as st

import db
from models import Priority, Project

PRIORITY_ORDER: list[Priority] = ["high", "medium", "low"]
PRIORITY_LABELS: dict[Priority, str] = {"high": "高", "medium": "中", "low": "低"}
PRIORITY_LABEL_TO_VALUE: dict[str, Priority] = {v: k for k, v in PRIORITY_LABELS.items()}

NO_PROJECT_LABEL = "（プロジェクトなし）"


def _project_options(projects: list[Project]) -> dict[str, str | None]:
    options: dict[str, str | None] = {NO_PROJECT_LABEL: None}
    for project in projects:
        options[project.name] = project.id
    return options


def _close_modal() -> None:
    st.session_state.pop("_task_modal_target", None)
    st.rerun()


@st.dialog("タスク")
def open_task_modal(task_id: str | None, default_project_id: str | None = None) -> None:
    """task_idがNoneなら新規作成、指定があれば編集としてモーダルを開く。

    default_project_idは新規作成時の初期プロジェクト（プロジェクト詳細画面からの追加用）。
    """
    # 前回と違うタスクを開いた場合は削除確認の状態をリセットする
    target = (task_id, default_project_id)
    if st.session_state.get("_task_modal_target", "_unset_") != target:
        st.session_state["_task_modal_target"] = target
        st.session_state["_task_modal_confirm_delete"] = False

    task = db.get_task(task_id) if task_id else None
    projects = db.list_projects(include_archived=False)
    project_options = _project_options(projects)
    project_labels = list(project_options.keys())

    initial_project_id = task.project_id if task else default_project_id
    initial_project_label = next(
        (label for label, pid in project_options.items() if pid == initial_project_id),
        NO_PROJECT_LABEL,
    )
    priority_labels = [PRIORITY_LABELS[p] for p in PRIORITY_ORDER]
    initial_priority_label = PRIORITY_LABELS[task.priority if task else "medium"]

    with st.form("task_form", border=False):
        title = st.text_input("タイトル（必須）", value=task.title if task else "")
        project_label = st.selectbox(
            "プロジェクト", project_labels, index=project_labels.index(initial_project_label)
        )
        priority_label = st.selectbox(
            "優先度", priority_labels, index=priority_labels.index(initial_priority_label)
        )
        due_date = st.date_input("期限", value=task.due_date if task else None)
        memo = st.text_area("メモ", value=task.memo if task else "")

        col_save, col_cancel = st.columns(2)
        save_clicked = col_save.form_submit_button("保存", type="primary", use_container_width=True)
        cancel_clicked = col_cancel.form_submit_button("キャンセル", use_container_width=True)

    if cancel_clicked:
        _close_modal()

    if save_clicked:
        title = title.strip()
        if not title:
            st.error("タイトルを入力してください")
        else:
            if task is None:
                db.create_task(
                    title=title,
                    project_id=project_options[project_label],
                    memo=memo,
                    priority=PRIORITY_LABEL_TO_VALUE[priority_label],
                    due_date=due_date,
                )
            else:
                task.title = title
                task.project_id = project_options[project_label]
                task.memo = memo
                task.priority = PRIORITY_LABEL_TO_VALUE[priority_label]
                task.due_date = due_date
                db.update_task(task)
            _close_modal()

    if task is not None:
        if st.session_state["_task_modal_confirm_delete"]:
            st.warning("このタスクを削除しますか？元に戻せません。")
            col_delete, col_keep = st.columns(2)
            with col_delete:
                if st.button("削除する", type="primary"):
                    db.delete_task(task.id)
                    _close_modal()
            with col_keep:
                if st.button("キャンセル", key="task_delete_cancel"):
                    st.session_state["_task_modal_confirm_delete"] = False
                    st.rerun(scope="fragment")
        else:
            if st.button("このタスクを削除"):
                st.session_state["_task_modal_confirm_delete"] = True
                st.rerun(scope="fragment")
