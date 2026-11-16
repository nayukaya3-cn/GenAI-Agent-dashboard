"""画面の共通部品（見出し・色・注意書き・研究ページの鍵）"""
import hmac
import os

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


CASE_KEY = "CASE_STUDY_PASSWORD"


def case_password() -> str:
    """研究ページの合言葉。Secrets か環境変数に置いたときだけ、研究ページがメニューに現れる（置かなければ誰にも見えない）。
    合言葉そのものは、コードにもリポジトリにも書かない。"""
    try:
        v = st.secrets.get(CASE_KEY, "")
    except Exception:          # secrets.toml がない環境
        v = ""
    return str(v or os.environ.get(CASE_KEY, ""))


def case_gate() -> bool:
    """合言葉が合うまで、研究ページの中身を一切描かない"""
    pw = case_password()
    if not pw:
        st.info("このページは非公開です。合言葉が設定されていないので、表示しません。")
        return False
    if st.session_state.get("_case_ok"):
        return True
    entered = st.text_input("合言葉", type="password", key="case_pw")
    if entered and hmac.compare_digest(entered.encode(), pw.encode()):
        st.session_state["_case_ok"] = True
        st.rerun()
    if entered:
        st.error("合言葉が違います。")
    st.caption("本人だけが見るページです。")
    return False
