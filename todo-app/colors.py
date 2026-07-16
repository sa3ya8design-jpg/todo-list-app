"""プロジェクトカラーのプリセット定義。"""

# 表示ラベル（絵文字＋色名） → カラーコード
COLOR_PALETTE: dict[str, str] = {
    "🔴 レッド": "#EF4444",
    "🟠 オレンジ": "#F97316",
    "🟡 イエロー": "#EAB308",
    "🟢 グリーン": "#22C55E",
    "🔵 ブルー": "#3B82F6",
    "🟣 パープル": "#8B5CF6",
    "🟤 ブラウン": "#92400E",
    "⚫ グレー": "#6B7280",
}

DEFAULT_COLOR = "#3B82F6"


def color_label(color: str) -> str | None:
    """カラーコードに対応するラベルを返す（プリセット外ならNone）。"""
    for label, hex_code in COLOR_PALETTE.items():
        if hex_code.lower() == color.lower():
            return label
    return None


def color_emoji(color: str) -> str:
    """カラーコードに対応する絵文字を返す（プリセット外は⚪）。"""
    label = color_label(color)
    return label.split()[0] if label else "⚪"
