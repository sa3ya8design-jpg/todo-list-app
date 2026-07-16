"""画面全体の入り口（Streamlit が起動するファイル）。"""

import streamlit as st

import db
from colors import color_emoji

db.init_db()

pg = st.navigation(
    [
        st.Page("pages/home.py", title="ホーム", icon="🏠"),
        st.Page("pages/projects.py", title="プロジェクト", icon="📁"),
        st.Page("pages/archive.py", title="完了プロジェクト", icon="✅"),
    ]
)

# タスク完了時のトースト（st.rerunをまたぐためsession_state経由で受け取る）
toast_message = st.session_state.pop("_completed_toast", None)
if toast_message:
    st.toast(toast_message)

# サイドバー：進行中のプロジェクト一覧
with st.sidebar:
    projects = db.list_projects(include_archived=False)
    if projects:
        st.caption("進行中のプロジェクト")
        for project in projects:
            if st.button(
                f"{color_emoji(project.color)} {project.name}",
                key=f"sidebar_project_{project.id}",
                use_container_width=True,
            ):
                st.session_state["selected_project_id"] = project.id
                st.switch_page("pages/projects.py")

pg.run()
