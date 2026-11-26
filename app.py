"""
「農＋X」ライフスタイル × 生成AI ダッシュボード（Streamlit）
起動： streamlit run app.py
メイン：農＋X（views/nox_*.py、計算は nox_core.py）。後ろに生成AIの道具箱 01〜07（views/、計算は genai_core.py）。
どちらの計算部品も Streamlit 非依存で、`python nox_core.py`／`python genai_core.py` で自己チェックできる。
"""
import streamlit as st

import ui

st.set_page_config(page_title="農＋X ライフスタイル × 生成AI", page_icon="🌾", layout="wide")
SHORT = {"overview": "生成AIとエージェント", "agent": "エージェント設計"}   # サイドバーに収まる短い名前
NOX_SHORT = {"nox_home": "暮らしの風景を届ける", "nox_rotation": "輪作と時間", "nox_portfolio": "収入の組み合わせ",
             "nox_market": "風景パッケージ・支援", "nox_teach": "作業学習・検定・実習"}
pages = {
    "農＋X ライフスタイル": [st.Page(ui.page_path(k), title=f"{verb}｜{NOX_SHORT[k]}", url_path=k.removeprefix("nox_") if k != "nox_home" else "home",
                                  default=(k == "nox_home")) for k, no, verb, sub in ui.NOX],
    "作業学習×生成AIで「働く入口」をつくる": [st.Page("views/entry.py", title="校長への提案｜特別支援学校／通信制・サポート校", url_path="entry")],
    "特別支援学校 × 3Dプリンター": [st.Page("views/print3d.py", title="3Dプリンター業務推進ボード", url_path="print3d")],
    "生成AIの道具箱": [st.Page(f"views/{k}.py", title=f"{no} {verb}｜{SHORT.get(k, sub)}", url_path=k) for k, no, verb, sub in ui.STEPS],
}
nav = st.navigation(pages)
ui.sidebar_note()
nav.run()
