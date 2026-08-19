"""プロジェクト作成・編集モーダル（「保存」で確定して閉じる）。

種類を切り替えると工程チェックリストのデフォルト選択が変わるため、
st.formは使わず通常ウィジェット＋「保存」ボタンで構成する。
"""

import streamlit as st

import db
from colors import COLOR_PALETTE, DEFAULT_COLOR, color_label
from models import KIND_LABELS, Kind

KIND_LABEL_TO_VALUE: dict[str, Kind] = {v: k for k, v in KIND_LABELS.items()}


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

    name = st.text_input("プロジェクト名（必須）", value=project.name if project else "")

    kind_labels = list(KIND_LABELS.values())
    initial_kind: Kind = project.kind if project else "design"
    default_kind_label = KIND_LABELS[initial_kind]
    # segmented_controlは選択中の項目を再クリックすると選択解除(None)されるため、
    # その場合は元の種類にフォールバックし、常にいずれか1つが選ばれた状態を保つ
    kind_label = st.segmented_control("種類", kind_labels, default=default_kind_label) or default_kind_label
    kind = KIND_LABEL_TO_VALUE[kind_label]

    # 工程チェックリストは新規作成時のみ（投入後の調整はタスク追加・削除で行う）
    selected_step_names: list[str] = []
    if project is None:
        steps = db.list_process_steps()
        if steps:
            # 種類を切り替えるとdefaultが変わり、選択状態もリセットされる（意図した挙動）
            selected = st.pills(
                "工程（選択した工程をタスクとして追加）",
                [s.name for s in steps],
                selection_mode="multi",
                default=[s.name for s in steps if kind in s.default_kinds],
            ) or []
            selected_step_names = [s.name for s in steps if s.name in set(selected)]

    color_choice = st.pills(
        "カラー",
        list(COLOR_PALETTE),
        default=color_label(project.color if project else DEFAULT_COLOR),
    )

    amount_text = st.text_input(
        "受注金額（税込・円）",
        value=str(project.amount) if project and project.amount is not None else "",
        placeholder="未入力",
    )

    col_save, col_cancel = st.columns(2)
    save_clicked = col_save.button("保存", type="primary", use_container_width=True)
    cancel_clicked = col_cancel.button("キャンセル", use_container_width=True)

    if cancel_clicked:
        _close_modal()

    if save_clicked:
        name = name.strip()
        amount_input = amount_text.strip().replace(",", "")
        amount_value: int | None = None
        amount_error = False
        if amount_input:
            if amount_input.isdigit():
                amount_value = int(amount_input)
            else:
                amount_error = True

        if not name:
            st.error("プロジェクト名を入力してください")
        elif amount_error:
            st.error("受注金額は半角数字で入力してください")
        else:
            color = COLOR_PALETTE.get(color_choice, DEFAULT_COLOR)
            if project is None:
                created = db.create_project(name=name, color=color, kind=kind, amount=amount_value)
                if selected_step_names:
                    db.create_tasks(selected_step_names, project_id=created.id)
            else:
                project.name = name
                project.color = color
                project.kind = kind
                project.amount = amount_value
                db.update_project(project)
            _close_modal()

    if project is not None:
        if project.is_completed:
            if st.button("進行中に戻す"):
                db.set_project_status(project.id, "invoiced")
                _close_modal()
        else:
            if st.button("完了プロジェクトへ移動"):
                db.set_project_status(project.id, "completed")
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
