import altair as alt
import pandas as pd
import streamlit as st

import genai_core as gc
import ui

ui.header("fit", "決まった教材をなぞるのではなく、一人ひとりの得意から、その人の武器になる使い方を探します。"
          "AIが下ごしらえをし、本人が確かめて仕上げます。")

st.subheader("得意から道筋をつくる")
names = [s[0] for s in gc.STRENGTHS]
sel = st.multiselect("本人の言葉で、得意や好きなこと（障害の種類や診断名は扱いません）", names, default=names[1:3], key="strengths")
cols = st.columns(2)
for i, s in enumerate(x for x in gc.STRENGTHS if x[0] in sel):
    with cols[i % 2], st.container(border=True):
        st.markdown(f"**{s[0]}**")
        st.markdown(f"- AIに任せる下ごしらえ：{s[1]}\n- 自分がやる仕上げ（武器）：{s[2]}\n- はじめの一歩：{s[3]}")
st.caption("AIに全部まかせると、本人の得意が出番を失います。決めるのは本人です。")

st.subheader("作業と人の組み合わせ")
st.write("作業の負担が、その人のできる範囲を超えた分だけ減点します（1段あたり25点）。支援を入れると、負担そのものが下がります。")
sup = [gc.SUPPORT[k] for k in st.multiselect("入れる支援", list(gc.SUPPORT), key="support")]
M = gc.fit_matrix(sup)
best, best_s = gc.best_assignment(M)
greedy, greedy_s = gc.greedy_assignment(M)
long = pd.DataFrame([{"人": p[0], "作業": t[0], "点": M[i][j], "割り当て": best[i] == j}
                     for i, p in enumerate(gc.PEOPLE) for j, t in enumerate(gc.TASKS)])
base = alt.Chart(long).encode(
    x=alt.X("人:N", sort=[p[0] for p in gc.PEOPLE], title=None, axis=alt.Axis(orient="top", labelAngle=0, labelFontSize=13)),
    y=alt.Y("作業:N", sort=[t[0] for t in gc.TASKS], title=None, axis=alt.Axis(labelLimit=280, labelFontSize=12)))
heat = base.mark_rect(stroke="white", strokeWidth=2).encode(
    color=alt.Color("点:Q", scale=alt.Scale(domain=[0, 100], range=["#e9f1fc", "#1c5cab"]), legend=alt.Legend(title="合う度合い（点）")),
    tooltip=["人", "作業", "点"])
txt = base.mark_text(fontSize=12).encode(text="点:Q", color=alt.condition("datum.点 >= 60", alt.value("white"), alt.value("#14171d")))
pick = base.transform_filter("datum.割り当て").mark_rect(fillOpacity=0, stroke="#14171d", strokeWidth=3)
st.altair_chart((heat + txt + pick).properties(height=30 * len(gc.TASKS) + 30), use_container_width=True)
a, b = st.columns(2)
with a:
    st.markdown("**全部の組み合わせを調べた結果（太枠）**")
    for i, p in enumerate(gc.PEOPLE):
        st.markdown(f"- {p[0]}：{gc.TASKS[best[i]][0]}（{M[i][best[i]]}点）")
    st.caption(f"合計 {best_s} 点")
with b:
    st.markdown("**上の人から順に選んだ結果（貪欲法）**")
    for i, p in enumerate(gc.PEOPLE):
        st.markdown(f"- {p[0]}：{gc.TASKS[greedy[i]][0]}（{M[i][greedy[i]]}点）")
    st.caption(f"合計 {greedy_s} 点。" + ("速いが、最適とは限らない例になっています。" if greedy_s < best_s else "この条件では同じ合計になりました。"))
st.caption("点数は 0〜100。負担と得意の数字、支援の効き方は仮置きです。現場の支援者が書きかえます。")

st.subheader("AIの答えを読む4枚カードと、支援の量")
st.write("特別支援学校版の4枚カード（みる・はかる・くらべる・つたえる）を、AIの答えを確かめる場面に読みかえました。"
         "同じカードを3つの場面で記録し、場面をまたいで力が保たれているかを見ます。")
rec = pd.DataFrame(gc.RECORD_DEFAULT, columns=gc.SCENES, index=[c[0] for c in gc.CARDS])
rec.insert(0, "AIの答えで確かめること", [c[1] for c in gc.CARDS])
edited = st.data_editor(rec, key="record", use_container_width=True, disabled=["AIの答えで確かめること"],
                        column_config={s: st.column_config.NumberColumn(s, min_value=1, max_value=5, step=1) for s in gc.SCENES})
for (card, _), verdict in zip(gc.CARDS, gc.transfer_check(edited[gc.SCENES].fillna(1).astype(int).values.tolist())):
    st.markdown(f"{'🟢' if verdict == '保たれている' else '🟡'} **{card}**：{verdict}")
with st.expander("支援の量の5段階"):
    st.dataframe(pd.DataFrame(gc.LEVELS.items(), columns=["段階", "支援の量"]), hide_index=True, use_container_width=True)
st.caption("場面間の差が1以内なら「保たれている」とします。記録するのは カード×場面×支援の量 だけで、名前や写真は扱いません。")
