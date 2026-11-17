import altair as alt
import pandas as pd
import streamlit as st

import genai_core as gc
import ui

ui.header("measure", "「AIを使ったら良くなった」と言えるかを、数で確かめます。記録が少ないうちは幅が広い、という前提で読みます。初期表示の数字は架空です。")

st.subheader("次に一緒に試す使い方")
st.write("役に立った回数と、立たなかった回数を入れます。よく効くと分かっている使い方（活用）と、まだ分からない使い方（探索）の両方が候補に残ります。")
trials = st.data_editor(pd.DataFrame(gc.TRIAL_DEFAULT, columns=["使い方", "役に立った", "立たなかった"]), key="trials", num_rows="dynamic",
                        hide_index=True, use_container_width=True, column_config={
                            "役に立った": st.column_config.NumberColumn(min_value=0, max_value=99, step=1, default=0),
                            "立たなかった": st.column_config.NumberColumn(min_value=0, max_value=99, step=1, default=0)})
rows = [(str(r["使い方"]), int(r["役に立った"] or 0), int(r["立たなかった"] or 0)) for r in trials.fillna(0).to_dict("records")
        if str(r["使い方"]).strip() and str(r["使い方"]) != "0"]
if rows:
    probs = gc.pick_probs(rows)
    stat = pd.DataFrame([{"使い方": n, "平均": m, "下": lo, "上": hi, "選ばれる割合": probs[n]}
                         for n, g, b in rows for m, lo, hi in [gc.beta_stats(g, b)]])
    order = [r[0] for r in rows]
    st.info(f"次の候補：**{max(probs, key=probs.get)}**（選ばれる割合 {max(probs.values()):.0%}）")
    y = alt.Y("使い方:N", sort=order, title=None, axis=alt.Axis(labelLimit=200))
    pct = alt.Axis(format="%", values=[0, .25, .5, .75, 1])
    a, b = st.columns(2)
    rule = alt.Chart(stat).mark_rule(strokeWidth=2, color="#84878f").encode(
        y=y, x=alt.X("下:Q", scale=alt.Scale(domain=[0, 1]), axis=pct, title="役に立つ見込み（点は平均、線は80%の幅）"), x2="上:Q")
    dot = alt.Chart(stat).mark_circle(size=90, color=ui.S1, opacity=1).encode(
        y=y, x="平均:Q", tooltip=["使い方", alt.Tooltip("平均:Q", format=".0%"), alt.Tooltip("下:Q", format=".0%"), alt.Tooltip("上:Q", format=".0%")])
    a.altair_chart((rule + dot).properties(height=36 * len(rows) + 40), use_container_width=True)
    bar = alt.Chart(stat).mark_bar(color=ui.S1, cornerRadiusEnd=4, size=14).encode(
        y=y, x=alt.X("選ばれる割合:Q", scale=alt.Scale(domain=[0, 1]), axis=pct, title="次に選ばれる割合"),
        tooltip=["使い方", alt.Tooltip("選ばれる割合:Q", format=".0%")])
    b.altair_chart(bar.properties(height=36 * len(rows) + 40), use_container_width=True)
st.caption("はじめの見込みは 0〜1 のどこも同じ（ベータ分布 Beta(1,1)）とし、見込みを1つずつ引いて最大のものを選ぶ操作を3,000回くり返しています"
           "（トンプソン抽出。強化学習の探索と活用の考え方）。")

st.subheader("一人の記録で、手立ての効果を比べる（ABAB）")
st.write("A＝いつもの説明、B＝AIと作ったやさしい手順書。入れて、外して、もう一度入れます。数は「10工程のうち、声かけなしでできた数」です。")
P = {k: gc.parse_series(c.text_input(k, ",".join(map(str, v)), key=f"ab_{k}"))
     for c, (k, v) in zip(st.columns(4), gc.ABAB_DEFAULT.items())}
A, B = P["A1"] + P["A2"], P["B1"] + P["B2"]
if A and B:
    pts, n = [], 0
    for k in P:
        for v in P[k]:
            n += 1
            pts.append({"回": n, "期": k, "条件": "A いつもの説明" if k[0] == "A" else "B やさしい手順書", "できた工程": v})
    d = pd.DataFrame(pts)
    line = alt.Chart(d).mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=70, filled=True)).encode(
        x=alt.X("回:Q", title="回（左から順）", axis=alt.Axis(tickMinStep=1, grid=False)),
        y=alt.Y("できた工程:Q", scale=alt.Scale(domain=[0, 10]), title="声かけなしでできた工程（10のうち）"),
        color=alt.Color("条件:N", scale=alt.Scale(range=[ui.S1, ui.S2]), legend=alt.Legend(orient="top", title=None)),
        detail="期:N", tooltip=["期", "回", "できた工程"])
    starts = d.groupby("期", sort=False)["回"].agg(["min", "max"]).reset_index()
    starts["中"] = (starts["min"] + starts["max"]) / 2
    sep = alt.Chart(starts.iloc[1:]).transform_calculate(x="datum.min - 0.5").mark_rule(strokeDash=[3, 3], color="#84878f").encode(x="x:Q")
    lab = alt.Chart(starts).mark_text(dy=-4, fontWeight="bold", color="#50545d").encode(x="中:Q", y=alt.value(10), text="期:N")
    st.altair_chart((sep + line + lab).properties(height=280), use_container_width=True)
    bc = gc.beta_compare(sum(A), 10 * len(A), sum(B), 10 * len(B))
    c1, c2, c3, c4 = st.columns(4)
    f = lambda a, b: f"{gc.pnd(a, b):.0%}" if a and b else "―"
    c1.metric("重なりのない割合（A1→B1／A2→B2）", f"{f(P['A1'], P['B1'])} ／ {f(P['A2'], P['B2'])}")
    c2.metric("NAP（0.5なら差なし）", f"{gc.nap(A, B):.2f}")
    c3.metric("Bのほうができる確率が高い確率", f"{bc['P(B>A)']:.0%}")
    c4.metric("できる確率の差（中央値）", f"{bc['差の中央値'] * 100:+.0f}pt", help=f"95%の幅 {bc['差の下限'] * 100:.0f}〜{bc['差の上限'] * 100:.0f}pt")
    st.caption(f"Aの平均 {sum(A) / len(A):.2f}、Bの平均 {sum(B) / len(B):.2f}。ベイズの計算は、工程を1つずつ独立な「できた／できない」とみなす粗い仮定です。"
               "外したときに下がり、戻したときに上がるかを、まず図で見ます。")
else:
    st.warning("A と B に、0〜10 の数を「,」で区切って入れてください。")

st.subheader("公平に比べるための4つの問い")
st.dataframe(pd.DataFrame(gc.FAIR, columns=["問い", "中身"]), hide_index=True, use_container_width=True)
st.caption("「AIを使った日のほうが速かった」は、まぎれこむものを消すまで、AIのおかげとは言えません。因果を考えるときの基本の形です。")

ui.contact()
