"""画面の共通部品（見出し・色・注意書き）"""
import streamlit as st

import social as sn

S1, S2 = "#2a78d6", "#eb6834"   # 系列の色（色覚の違いでも見分けられる組として検証済みの2色）
STEPS = [("overview", "01", "知る", "生成AIとエージェントの関係"), ("learn", "02", "学ぶ", "仕組みと本棚の読む順"),
         ("ask", "03", "聞く", "質問の型をつくる"), ("guard", "04", "守る", "入れる前・出てきた後"),
         ("fit", "05", "組む", "得意×AIの道筋"), ("agent", "06", "任せる", "エージェントの設計シート"),
         ("measure", "07", "確かめる", "効いたかを数で見る")]
# 農＋X（メイン）：(キー, 番号, 見出し, 副題)
NOX = [("nox_home", "0", "農＋X", "モノではなく、暮らしの風景を届ける"), ("nox_rotation", "1", "農", "輪作と時間の予算"),
       ("nox_portfolio", "2", "収入", "組み合わせと悪い年への強さ"), ("nox_market", "3", "X 売る", "風景パッケージとマーケティング支援"),
       ("nox_teach", "4", "X 教える", "作業学習と「科学と人間生活」")]
LIGHT_ICON = {"赤": "🔴", "黄": "🟡", "緑": "🟢"}
CORE = ("農産物そのもの（モノ）を主役にせず、その農産物が生まれる背景にある「心地よい暮らし方や価値観」を商品にする。"
        "第一歩は、畑の風景・食卓の風景をパッケージにし、小さな定期便や体験イベントからファンと直接つながること。")


def header(key: str, lead: str) -> None:
    nox = next((s for s in NOX if s[0] == key), None)
    if nox:
        _, no, verb, sub = nox
        st.caption(f"農＋X ライフスタイル ／ {no}")
    else:
        _, no, verb, sub = next(s for s in STEPS if s[0] == key)
        st.caption(f"生成AIの道具箱 ／ {no} ／ 07")
    st.title(f"{verb}：{sub}")
    st.write(lead)
    st.divider()


def page_path(key: str) -> str:
    return f"views/{key}.py"


def sidebar_note() -> None:
    with st.sidebar:
        st.caption("農＋X の考え方")
        st.markdown("<small>モノではなく、暮らしの風景を届ける。小さな定期便と体験から、ファンと直接つながる。</small>", unsafe_allow_html=True)
        st.divider()
        st.caption("つくった人の活動")
        sn.buttons("で活動内容を見る", stacked=True)
        st.divider()
        st.caption("この画面は生成AIを呼び出さず、入力を外へ送りません。初期表示の人・数字はすべて架空です。")
        st.caption("もとのページ："
                   "[スマートパン屋農家](https://smart-bakery-farm.streamlit.app/)・"
                   "[科学と人間生活](https://science-and-our-daily-life-20261106.streamlit.app/)・"
                   "[IoTフィールドワーク](https://iot-fieldwork-dashboard-20261115.streamlit.app/)")
        st.caption("[GitHub（ソースコード）](https://github.com/nayukaya3-cn/GenAI-Agent-dashboard)")


def contact() -> None:
    """ページの最後に置く「声をかける」欄"""
    st.divider()
    with st.container(border=True):
        st.markdown("**この画面について**")
        st.write(f"現場で使ってみた感想、直してほしい点、一緒に試したい業務（農＋X の立ち上げ、農業法人の発信、授業づくり）があれば、{sn.NAMES}から気軽に声をかけてください。"
                 "支援の記録や個人が分かる情報は、メッセージに書かないでください。")
        sn.buttons("で声をかける")


def link(key: str, label: str, icon: str = "➡️") -> None:
    """ページへのリンク。ページ単体で動かしたとき（テストなど）はリンク先が無いので、文字だけ出す"""
    try:
        st.page_link(page_path(key), label=label, icon=icon)
    except Exception:  # noqa: BLE001  ナビゲーションの外では page_link が使えない
        st.markdown(f"{icon} {label}")
