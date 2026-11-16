import pandas as pd
import streamlit as st

import genai_core as gc
import ui

ui.header("learn", "仕組みを知ると、使い方の理由が分かります。言葉を1つ選ぶと、要点、使い方への効き方、読む場所が出ます。")

left, right = st.columns(2)
with left:
    st.subheader("仕組みの地図")
    layers = list(dict.fromkeys(c[1] for c in gc.CONCEPTS))
    layer = st.radio("層", layers, index=1, horizontal=True, key="learn_layer")
    names = [c[2] for c in gc.CONCEPTS if c[1] == layer]
    name = st.radio("言葉", names, key=f"learn_name_{layer}")
c = next(x for x in gc.CONCEPTS if x[2] == name)
with right, st.container(border=True):
    st.caption(c[1])
    st.markdown(f"### {c[2]}")
    st.markdown(f"**要点**　{c[3]}")
    st.markdown(f"**使い方への効き方**　{c[4]}")
    st.markdown("**読む場所**")
    if c[5]:
        for book, where in c[5]:
            st.markdown(f"- {gc.BOOKS[book][0]}（{where}）")
    else:
        st.markdown("- 本棚の外。06 任せる へ")

st.subheader("読む順を決める")
goal = st.selectbox("目的", list(gc.ROUTES), key="learn_goal")
rows = [(i + 1, gc.BOOKS[b][0], gc.BOOKS[b][1], gc.BOOKS[b][2], where) for i, (b, where) in enumerate(gc.ROUTES[goal])]
if goal == next(iter(gc.ROUTES)):
    rows.append((len(rows) + 1, "この画面の 03〜07", "―", "手を動かす", "聞く・守る・組む・任せる・確かめる"))
st.dataframe(pd.DataFrame(rows, columns=["順", "本", "著者", "進め方", "ここを読む"]), hide_index=True, use_container_width=True)
st.caption("章の番号は、本棚メモ（目次）に書かれている範囲で示しています。")
