"""画面の共通部品（見出し・色・注意書き）"""
import streamlit as st

S1, S2 = "#2a78d6", "#eb6834"   # 系列の色（色覚の違いでも見分けられる組として検証済みの2色）
STEPS = [("overview", "01", "知る", "生成AIとエージェントの関係"), ("learn", "02", "学ぶ", "仕組みと本棚の読む順"),
         ("ask", "03", "聞く", "質問の型をつくる"), ("guard", "04", "守る", "入れる前・出てきた後"),
         ("fit", "05", "組む", "得意×AIの道筋"), ("agent", "06", "任せる", "エージェントの設計シート"),
         ("measure", "07", "確かめる", "効いたかを数で見る")]
LIGHT_ICON = {"赤": "🔴", "黄": "🟡", "緑": "🟢"}


def header(key: str, lead: str) -> None:
    _, no, verb, sub = next(s for s in STEPS if s[0] == key)
    st.caption(f"{no} ／ 07")
    st.title(f"{verb}：{sub}")
    st.write(lead)
    st.divider()


def sidebar_note() -> None:
    with st.sidebar:
        st.caption("この画面は生成AIを呼び出さず、入力を外へ送りません。初期表示の人・数字はすべて架空です。")
        st.caption("もとのページ："
                   "[スマートパン屋農家](https://smart-bakery-farm.streamlit.app/)・"
                   "[科学と人間生活](https://science-and-our-daily-life-20261106.streamlit.app/)・"
                   "[IoTフィールドワーク](https://iot-fieldwork-dashboard-20261115.streamlit.app/)")
