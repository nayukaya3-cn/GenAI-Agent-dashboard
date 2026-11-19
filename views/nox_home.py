import pandas as pd
import streamlit as st

import nox_core as nx
import ui

ui.header("nox_home", ui.CORE)

with st.container(border=True):
    st.markdown("#### 届けるのは、たとえばこんな朝")
    st.markdown("**自家製小麦のパンと、畑の大豆でつくった豆のスープがある朝の食卓。**")
    st.write("小麦は秋に播き、冬に踏み、初夏に刈る。そのあとの畑に大豆を播く。"
             "この一年の物語ごと食卓に届けると、「小麦粉」は相場の品ではなく、待ってもらえる便りになります。")
    ui.link("nox_market", "この風景をパッケージにする（3 X 売る）", "🧺")

st.subheader("農 ＋ X の組み立て")
st.graphviz_chart("""
digraph G {
  rankdir=LR; bgcolor="transparent"; node [shape=box, style="rounded,filled", fontname="sans-serif", fontsize=11, color="#c9ced8"];
  edge [color="#84878f", fontname="sans-serif", fontsize=9];
  subgraph cluster_n { label="農"; fontname="sans-serif"; color="#2a78d6"; style=rounded;
    w [label="パン用小麦", fillcolor="#e9f1fc"]; s [label="枝豆・大豆", fillcolor="#e9f1fc"]; v [label="ハウスの野菜", fillcolor="#e9f1fc"];
    k [label="食品加工\\n製粉・パン生地・味噌", fillcolor="#e9f1fc"]; }
  scene [label="暮らしの風景\\n（朝の食卓・畑の週末）", fillcolor="#fde9df", color="#eb6834"];
  box [label="小さな定期便\\n体験イベント", fillcolor="#fde9df", color="#eb6834"];
  fan [label="ファン\\n（定期便・オーナー・援農）", fillcolor="#fde9df", color="#eb6834"];
  subgraph cluster_x { label="X"; fontname="sans-serif"; color="#2a78d6"; style=rounded;
    t [label="教える\\n支援学校の作業学習\\n定時制・通信制の科学と人間生活", fillcolor="#f3f5f8"];
    m [label="支える\\n農業法人・関連企業の\\nマーケティング支援", fillcolor="#f3f5f8"]; }
  ai [label="生成AIの道具箱\\n01〜07", fillcolor="#ffffff", style="rounded,dashed"];
  w -> s [label="輪作 🔁", dir=both]; s -> v [style=dotted, arrowhead=none];
  w -> k; s -> k; {w s v k} -> scene [style=invis];
  k -> scene; v -> scene; scene -> box [label="包む"]; box -> fan [label="直接つながる"];
  fan -> w [label="援農・麦踏み", style=dashed];
  w -> t [label="教材・FWの場"]; scene -> m [label="自分で試した型"]; m -> scene [label="支援先の風景", style=dashed];
  ai -> box [style=dashed, label="発信の下書き・点検"]; ai -> m [style=dashed];
}""", use_container_width=True)
st.caption("農は X の現場（教材・実践例）になり、X は農の収入を天候から切りはなします。両方を、生成AIの道具箱が下ごしらえで支えます。")

st.subheader("モノを売るから、暮らしを届けるへ")
st.dataframe(pd.DataFrame(nx.SHIFT, columns=["比べる点", "これまで（モノが主役）", "農＋X（暮らしの風景が主役）"]),
             hide_index=True, use_container_width=True)

st.subheader("なぜ、強くなるのか（レジリエンス）")
for col, (head, how, eff) in zip(st.columns(3), nx.RESILIENCE):
    with col, st.container(border=True):
        st.markdown(f"**{head}**")
        st.write(how)
        st.caption(eff)

st.subheader("3つの原則")
for head, body in nx.PRINCIPLES:
    st.markdown(f"- **{head}**：{body}")

st.subheader("はじめの一歩")
for col, (head, body, key) in zip(st.columns(4), nx.FIRST_STEPS):
    with col, st.container(border=True):
        st.markdown(f"**{head}**")
        st.write(body)

st.subheader("「農＋X」の3つの壁と、確かめるページ")
st.write("農＋X は、時間・収入・立ち上げの3つが大変になりがちです。それぞれを数で確かめるページを用意しました。")
for col, (wall, q, key) in zip(st.columns(3), nx.WALLS):
    with col, st.container(border=True):
        st.markdown(f"**{wall}の壁**")
        st.write(q)
        ui.link(key, next(f"{s[1]} {s[2]}：{s[3]}" for s in ui.NOX if s[0] == key))

st.subheader("人手と関係人口")
st.write("繁忙期の人手は、雇う・頼む・来てもらうの組み合わせで考えます。同じ仕組みは、X の側から自分が働く入口にもなります。")
for name, what, use, url in nx.LABOR:
    with st.container(border=True):
        st.markdown(f"**{name}**" + (f"　[開く]({url})" if url else ""))
        st.write(what)
        st.caption(f"使いどころ：{use}")
st.caption("制度・アプリの中身は変わることがあります。使う前に、リンク先の最新の情報を確かめてください。")

st.subheader("この画面の歩き方")
st.dataframe(pd.DataFrame([
    ("1 農", "輪作の区画と、月ごとの作業時間・X の勤務を重ね、余白が残るかを見る", "道具箱 05 組む（作業と人の組み合わせ）"),
    ("2 収入", "収入の柱を組み合わせ、不作の年・契約がとれない年の手取りを試しに引く", "道具箱 07 確かめる（ベイズ）"),
    ("3 X 売る", "風景をパッケージにし、発信カレンダー・ファンの育ち方・テスト販売の判定・支援メニューをつくる", "道具箱 03 聞く・04 守る・06 任せる"),
    ("4 X 教える", "畑の工程を作業学習→技能検定→職場体験実習→就職・定着につなぎ、同じ工程の「なぜ」を「科学と人間生活」の単元にする", "道具箱 05 組む・07 確かめる"),
], columns=["ページ", "やること", "あわせて使う道具箱"]), hide_index=True, use_container_width=True)

ui.contact()
