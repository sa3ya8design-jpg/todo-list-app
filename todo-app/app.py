"""画面全体の入り口（Streamlit が起動するファイル）。"""

import streamlit as st

import db
from colors import color_emoji
from models import STATUS_LABELS

db.init_db()

# 工程・カラー・ステータスなどの選択式ウィジェット（pills/segmented_control）は、
# 既定のテーマ色だと「選択中＝赤」で分かりづらいため、選択中/未選択の見た目をはっきり分ける。
# 工程・カラー（pills）はホバーしても色を変えない（選択状態以外は常に同じ見た目にする）。
# サイドバーのプロジェクト名（st-key-sidebar_project_*）は14pxに統一する。
st.markdown(
    """
    <style>
    [data-testid^="stBaseButton-pills"],
    [data-testid^="stBaseButton-segmented_control"] {
        background-color: #F3F4F6;
        border: 1px solid #D1D5DB;
        color: #374151;
    }
    [data-testid="stBaseButton-pillsActive"],
    [data-testid="stBaseButton-segmented_controlActive"] {
        background-color: #3B82F6;
        border: 1px solid #3B82F6;
        color: #FFFFFF;
        font-weight: 600;
    }
    [data-testid="stBaseButton-pills"]:hover,
    [data-testid="stBaseButton-segmented_control"]:hover {
        background-color: #F3F4F6;
        border-color: #D1D5DB;
        color: #374151;
    }
    [data-testid="stBaseButton-pillsActive"]:hover,
    [data-testid="stBaseButton-segmented_controlActive"]:hover {
        background-color: #3B82F6;
        border-color: #3B82F6;
        color: #FFFFFF;
    }
    [class*="st-key-sidebar_project_"] button p {
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pg = st.navigation(
    [
        st.Page("pages/home.py", title="ホーム", icon="🏠"),
        st.Page("pages/projects.py", title="プロジェクト", icon="📁"),
        st.Page("pages/archive.py", title="完了プロジェクト", icon="✅"),
        st.Page("pages/process_settings.py", title="工程設定", icon="🛠️"),
    ]
)

# タスク完了時のトースト（st.rerunをまたぐためsession_state経由で受け取る）
toast_message = st.session_state.pop("_completed_toast", None)
if toast_message:
    st.toast(toast_message)

# サイドバー：進行中のプロジェクト一覧（ステータスバッジ付き。金額は表示しない）
with st.sidebar:
    projects = db.list_projects(include_completed=False)
    if projects:
        st.caption("進行中のプロジェクト")
        for project in projects:
            col_name, col_status = st.columns([0.62, 0.38], vertical_alignment="center")
            with col_name:
                if st.button(
                    f"{color_emoji(project.color)} {project.name}",
                    key=f"sidebar_project_{project.id}",
                    use_container_width=True,
                ):
                    st.session_state["selected_project_id"] = project.id
                    st.switch_page("pages/projects.py")
            with col_status:
                # プロジェクト名（既定の文字色）と区別するため、ステータスはグレーで表示する
                st.markdown(
                    f'<div style="font-size:14px;color:#6B7280;">'
                    f'{STATUS_LABELS[project.status]}</div>',
                    unsafe_allow_html=True,
                )

pg.run()
