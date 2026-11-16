"""
生成AI＆AIエージェント利活用ダッシュボード（Streamlit）
起動： streamlit run app.py
計算は genai_core.py（Streamlit 非依存、`python genai_core.py` で自己チェック）。画面は views/ の7ページ。
"""
import streamlit as st

import ui

st.set_page_config(page_title="生成AI＆AIエージェント利活用", page_icon="🧭", layout="wide")
SHORT = {"overview": "生成AIとエージェント", "agent": "エージェント設計"}   # サイドバーに収まる短い名前
pages = [st.Page(f"views/{k}.py", title=f"{no} {verb}｜{SHORT.get(k, sub)}", url_path=k, default=(k == "overview"))
         for k, no, verb, sub in ui.STEPS]
nav = st.navigation(pages)
ui.sidebar_note()
nav.run()
