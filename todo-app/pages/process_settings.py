"""工程設定画面（工程マスタと、案件の種類ごとのデフォルトON/OFFを編集する）。"""

import sys
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

import db
from models import KIND_LABELS, ProcessStep

_NAME_COLUMN = "工程名"
_ORDER_COLUMN = "表示順"


def _steps_to_dataframe(steps: list[ProcessStep]) -> pd.DataFrame:
    rows = []
    for step in steps:
        row = {_ORDER_COLUMN: step.sort_order + 1, _NAME_COLUMN: step.name}
        for kind, label in KIND_LABELS.items():
            row[label] = kind in step.default_kinds
        rows.append(row)
    columns = [_ORDER_COLUMN, _NAME_COLUMN, *KIND_LABELS.values()]
    return pd.DataFrame(rows, columns=columns)


def _dataframe_to_steps(df: pd.DataFrame) -> list[ProcessStep]:
    steps = []
    for _, row in df.iterrows():
        name = str(row[_NAME_COLUMN]).strip() if pd.notna(row[_NAME_COLUMN]) else ""
        if not name:
            continue  # 工程名が空の行（追加しかけの行など）は無視する
        order = int(row[_ORDER_COLUMN]) if pd.notna(row[_ORDER_COLUMN]) else 999
        steps.append(ProcessStep(
            id=str(uuid.uuid4()),
            name=name,
            sort_order=order,
            default_kinds={
                kind for kind, label in KIND_LABELS.items() if bool(row.get(label))
            },
        ))
    # 表示順→入力順で並べ、連番を振り直す
    steps.sort(key=lambda s: s.sort_order)
    for index, step in enumerate(steps):
        step.sort_order = index
    return steps


st.title("工程設定")
st.caption(
    "プロジェクト新規作成時に選択できる工程の一覧です。"
    "チェックを付けた種類では、その工程がデフォルトで選択されます。"
    "行の追加・削除、工程名の変更、表示順の入れ替えができます。"
)

edited_df = st.data_editor(
    _steps_to_dataframe(db.list_process_steps()),
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    column_config={
        _ORDER_COLUMN: st.column_config.NumberColumn(_ORDER_COLUMN, min_value=1, step=1, width="small"),
        _NAME_COLUMN: st.column_config.TextColumn(_NAME_COLUMN, required=True),
        **{
            label: st.column_config.CheckboxColumn(label, default=False)
            for label in KIND_LABELS.values()
        },
    },
)

if st.button("保存", type="primary"):
    steps = _dataframe_to_steps(edited_df)
    names = [s.name for s in steps]
    if len(names) != len(set(names)):
        st.error("同じ名前の工程が複数あります。工程名は重複しないようにしてください")
    else:
        db.save_process_steps(steps)
        st.toast("工程設定を保存しました")
        st.rerun()
