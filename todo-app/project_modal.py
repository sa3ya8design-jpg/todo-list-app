"""プロジェクト作成・編集モーダル（「保存」で確定して閉じる）。"""

import streamlit as st

import db
from colors import COLOR_PALETTE, DEFAULT_COLOR, color_label


def _close_modal() -> None:
    st.session_state.pop("_project_modal_target", None)
    st.rerun()


@st.dialog("プロジェクト")
def open_project_modal(project_id: str | None) -> None:
    """project_idがNoneなら新規作成、指定があれば編集としてモーダルを開く。"""
    # 前回と違うプロジェクトを開いた場合は削除確認の状態をリセットする
    if st.session_state.get("_project_modal_target", "_unset_") != project_id:
        st.session_state["_project_modal_target"] = project_id
        st.session_state["_project_modal_confirm_delete"] = False

    project = db.get_project(project_id) if project_id else None

    with st.form("project_form", border=False):
        name = st.text_input("プロジェクト名（必須）", value=project.name if project else "")
        color_choice = st.pills(
            "カラー",
            list(COLOR_PALETTE),
            default=color_label(project.color if project else DEFAULT_COLOR),
        )

        col_save, col_cancel = st.columns(2)
        save_clicked = col_save.form_submit_button("保存", type="primary", use_container_width=True)
        cancel_clicked = col_cancel.form_submit_button("キャンセル", use_container_width=True)

    if cancel_clicked:
        _close_modal()

    if save_clicked:
        name = name.strip()
        if not name:
            st.error("プロジェクト名を入力してください")
        else:
            color = COLOR_PALETTE.get(color_choice, DEFAULT_COLOR)
            if project is None:
                db.create_project(name=name, color=color)
            else:
                project.name = name
                project.color = color
                db.update_project(project)
            _close_modal()

    if project is not None:
        archive_label = "進行中に戻す" if project.is_archived else "完了プロジェクトへ移動"
        if st.button(archive_label):
            db.set_project_archived(project.id, not project.is_archived)
            _close_modal()

        if st.session_state["_project_modal_confirm_delete"]:
            task_count = len(db.list_tasks(project_id=project.id))
            st.warning(
                f"このプロジェクトを削除しますか？中のタスク{task_count}件も削除されます。元に戻せません。"
            )
            col_delete, col_keep = st.columns(2)
            with col_delete:
                if st.button("削除する", type="primary"):
                    db.delete_project(project.id)
                    _close_modal()
            with col_keep:
                if st.button("キャンセル", key="project_delete_cancel"):
                    st.session_state["_project_modal_confirm_delete"] = False
                    st.rerun(scope="fragment")
        else:
            if st.button("このプロジェクトを削除"):
                st.session_state["_project_modal_confirm_delete"] = True
                st.rerun(scope="fragment")
