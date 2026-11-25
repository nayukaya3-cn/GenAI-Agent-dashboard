"""3Dプリンター業務推進ボード：特別支援学校 × 障害者雇用で、3Dプリンター・3Dモデリングを使う業務を見える化する。
本体はブラウザ1枚で動く 3d-print-board/index.html（Streamlit 非依存）。このページはそれを埋め込んで見せるだけ。
"""
from pathlib import Path

import streamlit as st

import ui

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "3d-print-board" / "index.html"
SRC = "https://github.com/nayukaya3-cn/GenAI-Agent-dashboard/tree/main/3d-print-board"

st.caption("特別支援学校 × 3Dプリンター")
st.title("3Dプリンター業務推進ボード")
st.write("仕上げ作業（サポート除去・研磨）・治具・自助具・3Dモデリングの業務を、①作業学習 → ②校内評価 → ③職場体験実習 → ④就職・定着 の流れで見える化します。"
         "完了した業務が「積層の塔」に1層ずつ積み上がります。")

c1, c2, c3 = st.columns(3)
c1.markdown("**推進業務**  \nかんばんで未着手→完了へ")
c2.markdown("**仕上げ評価**  \n評価表（試案）10項目で級とベイズ推定")
c3.markdown("**造形ライブラリ**  \n寸法から治具のOpenSCADコードを生成")
st.info("この画面の記録は、開いている端末（ブラウザ）だけに保存されます。ほかの人や端末には共有されません。"
        "生成AIの下書きは、この画面では使えません。生徒は氏名ではなく記号で登録してください。初期の業務・連携先・予定は試案（仮の値）です。", icon="ℹ️")

if BOARD.exists():
    st.iframe(BOARD, height=1600)
    st.download_button("ボードをダウンロード（.html・ブラウザで開くだけで動く）", BOARD.read_bytes(),
                       file_name="3d-print-board.html", mime="text/html")
else:
    st.warning("3d-print-board/index.html が見つかりません。")

st.caption(f"ソース・初期データ・拡張のしかた：[GitHub の 3d-print-board]({SRC})。"
           "記録を残したいときは、ボードの「データとGitHub」タブからJSONで書き出してください。")
ui.contact()
