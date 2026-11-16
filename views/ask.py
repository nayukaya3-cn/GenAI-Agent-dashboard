import streamlit as st

import genai_core as gc
import ui

ui.header("ask", "うまく聞けると、答えが変わります。5つの部品を埋めると、貼りつける文ができあがります。"
          "組み立てた文は、職場や学校で決めたサービスに自分で貼ります。")

left, right = st.columns(2)
with left:
    st.subheader("質問の型（5つの部品）")
    parts = {}
    for key, head, ask, example in gc.PARTS:
        parts[key] = st.text_input(f"{head}　{ask}", value=example if key in ("goal", "context", "rule") else "",
                                   placeholder=example or gc.DEFAULT_CHECK, key=f"pp_{key}")
with right:
    st.subheader("貼りつける文")
    n, missing = gc.prompt_score(parts)
    st.progress(n / 5, text=f"書けた部品 {n} / 5")
    st.code(gc.build_prompt(parts), language=None, wrap_lines=True)
    st.caption(f"まだ書いていない部品：{'・'.join(missing)}" if missing else "5つとも入りました。「確かめ」は空でも決まり文句が入ります。")
    for col, (name, url) in zip(st.columns(len(gc.SERVICES)), gc.SERVICES.items()):
        col.link_button(f"{name}を開く", url, use_container_width=True)
    st.caption("名前・連絡先・健康や障害に関する情報を書く欄は、わざと作っていません。貼る前に 04 守る で点検します。")

left, right = st.columns(2)
with left:
    st.subheader("「分からない」の5段階")
    i = st.radio("いまの自分に近い段", range(len(gc.LADDER)), index=2, format_func=lambda k: f"{k + 1}. {gc.LADDER[k][0]}", key="ladder")
    st.code(gc.LADDER[i][1], language=None, wrap_lines=True)
with right:
    st.subheader("質問に入っている部品を数える")
    q = st.text_area("自分の質問をそのまま書く", "メールってどう書くの", key="free_q")
    for k, ok in gc.question_parts(q).items():
        st.markdown(f"{'🟢' if ok else '🟡'} {k}：{'ある' if ok else '足すとよい'}")
    st.caption("ことばの形で見ているだけです。中身の良し悪しは人が読みます。")
    with st.expander("聞き直しのことば"):
        for r in gc.REASK:
            st.code(r, language=None, wrap_lines=True)
