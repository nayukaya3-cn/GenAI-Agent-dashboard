"""
生成AI＆AIエージェント利活用ダッシュボード（Streamlit）
起動： streamlit run app.py
計算は genai_core.py（Streamlit 非依存、`python genai_core.py` で自己チェック）。画面は views/ の7ページ。
合言葉（CASE_STUDY_PASSWORD）を Secrets に置いたときだけ、仮想研究事例のページ（views/case_study.py、計算は agri_case.py）が加わる。
"""
import streamlit as st

import ui

st.set_page_config(page_title="生成AI＆AIエージェント利活用", page_icon="🧭", layout="wide")
SHORT = {"overview": "生成AIとエージェント", "agent": "エージェント設計"}   # サイドバーに収まる短い名前
pages = [st.Page(f"views/{k}.py", title=f"{no} {verb}｜{SHORT.get(k, sub)}", url_path=k, default=(k == "overview"))
         for k, no, verb, sub in ui.STEPS]
if ui.case_password():      # 合言葉を置いた環境でだけ、研究ページをメニューに足す
    pages = {"7つの段": pages, "研究（本人のみ）": [st.Page("views/case_study.py", title="仮想研究事例｜農業法人", url_path="case")]}
nav = st.navigation(pages)
ui.sidebar_note()
nav.run()
