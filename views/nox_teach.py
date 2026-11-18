import altair as alt
import pandas as pd
import streamlit as st

import genai_core as gc
import nox_core as nx
import ui

ui.header("nox_teach", "畑の一年は、そのまま教材になります。同じ工程を、支援学校では作業学習として、定時制・通信制では"
          "「科学と人間生活」の単元として扱います。教えた経験は、農業法人を支援するときの言葉にもなります。")

st.subheader("畑の工程と、教える単元の対応")
st.dataframe(pd.DataFrame([t[:4] + ("・".join(f"{m}月" for m in t[4]),) for t in nx.TEACH],
                          columns=["農の工程", "作業学習（支援学校）", "科学と人間生活の単元", "情報Ⅰ・道具箱", "扱える月"]),
             hide_index=True, use_container_width=True)
st.caption("「科学と人間生活」の単元名は、光や熱の科学／物質の科学（材料とその再利用・衣料と食品）／生命の科学（ヒトの生命現象・微生物とその利用）／宇宙や地球の科学（太陽と地球・自然景観と自然災害）にそろえています。")

st.subheader("月ごとの授業の並べ方")
aud = st.radio("対象", list(nx.AUDIENCE), horizontal=True, key="aud")
rows = nx.teach_months(aud)
heat = pd.DataFrame([{"月": r["月"], "工程": t[0], "扱える": (int(r["月"][:-1]) in t[4])} for r in rows for t in nx.TEACH])
chart = alt.Chart(heat).mark_rect(stroke="white", strokeWidth=2).encode(
    x=alt.X("月:N", sort=nx.MONTHS, title=None, axis=alt.Axis(orient="top", labelAngle=0)),
    y=alt.Y("工程:N", sort=[t[0] for t in nx.TEACH], title=None, axis=alt.Axis(labelLimit=220)),
    color=alt.condition("datum.扱える", alt.value(ui.S1), alt.value("#e9f1fc")), tooltip=["月", "工程", "扱える"])
weeks = alt.Chart(pd.DataFrame(rows)).mark_bar(color="#a9c9f2").encode(
    x=alt.X("月:N", sort=nx.MONTHS, title=None, axis=None), y=alt.Y("授業の週:Q", title="授業の週"))
st.altair_chart(alt.vconcat(chart.properties(height=26 * len(nx.TEACH)), weeks.properties(height=70)).resolve_scale(x="shared"),
                use_container_width=True)
st.caption("上：その月に畑で扱える工程（濃い色）。下：授業のある週の目安（全日制の学期で仮置き。定時制・通信制のスクーリングに合わせて直す）。"
           "6〜7月と11月は畑の山と授業が重なる、教材にしやすい月です。8月は授業がないので、農の山（枝豆・製粉）を寄せます。")
with st.expander("月ごとの中身"):
    st.dataframe(pd.DataFrame(rows).rename(columns={"中身": nx.AUDIENCE[aud][0]}), hide_index=True, use_container_width=True)
st.info(nx.AUDIENCE[aud][1])

st.subheader("1コマの流れ（4枚カード）")
st.write("道具箱 05 の4枚カード（みる・はかる・くらべる・つたえる）を、畑の授業の流れにそのまま使います。")
for col, ((step, body), (card, check)) in zip(st.columns(4), zip(nx.LESSON, gc.CARDS)):
    with col, st.container(border=True):
        st.markdown(f"**{card}**")
        st.caption(step)
        st.write(body)
st.caption("同じカードを、練習・事務作業・現場の3場面で記録すると、力が場面をまたいで保たれているかが見えます（道具箱 05 組む）。")

st.subheader("教える X と、農・売る X のつながり")
st.markdown("""
- **教材が増えるほど、物語も増える**：授業で生徒が記録した生育データ・発酵の観察は、個人が分からない形にして畑の便りの話題になります。
- **作業を分ける力が、支援の力になる**：作業学習で工程を分け、手順書をつくる経験は、農業法人の業務を工程に分ける（道具箱 06）ときにそのまま使えます。
- **販売実習は MVP の練習**：定期便1箱・体験1回のテスト販売（3 X 売る ④）を、生徒と一緒に小さく回せます。
""")
st.caption("生徒の名前・写真・成績・支援の記録は、発信にも生成AIにも出しません。学習の記録を研究に使う場合は、事前に本人・保護者の同意と学校の手続きをとります。")
ui.link("fit", "作業と人の組み合わせ・支援の量（道具箱 05 組む）", "🧩")
ui.link("measure", "手立ての効果を一人の記録で比べる（道具箱 07 確かめる・ABAB）", "📊")
ui.contact()
