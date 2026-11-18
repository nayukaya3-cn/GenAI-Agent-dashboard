import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import nox_core as nx
import ui

ui.header("nox_portfolio", "収入の柱を組み合わせ、天候の良い年・悪い年、契約がとれた年・とれなかった年を1万年分ためしに引きます。"
          "見るのは平均ではなく「悪い年（下位5%）」の手取りです。初期の数字はすべて架空・仮置きです。")

st.subheader("収入の柱")
st.write("数量・単価・原価率と、天候の効き（0＝受けない〜1＝そのまま受ける）、成り立つ確率（契約・集客がうまくいく見込み）を入れます。")
cols = ["名前", "区分", "数量", "単価（円）", "原価率", "天候の効き", "成り立つ確率"]
edited = st.data_editor(pd.DataFrame(nx.STREAMS, columns=cols), key="streams", num_rows="dynamic", hide_index=True,
                        use_container_width=True, column_config={
                            "区分": st.column_config.SelectboxColumn(options=nx.GROUPS, required=True),
                            "数量": st.column_config.NumberColumn(min_value=0, step=1),
                            "単価（円）": st.column_config.NumberColumn(min_value=0, step=100, format="%d"),
                            "原価率": st.column_config.NumberColumn(min_value=0.0, max_value=1.0, step=0.05),
                            "天候の効き": st.column_config.NumberColumn(min_value=0.0, max_value=1.0, step=0.1),
                            "成り立つ確率": st.column_config.NumberColumn(min_value=0.0, max_value=1.0, step=0.05)})
streams = [tuple(r) for r in edited.dropna(subset=["名前", "区分"]).fillna(0)[cols].itertuples(index=False)
           if str(r[0]).strip()]
st.caption("非常勤講師の単価・時間、マーケティング支援の月額は仮置きです。実際の条件は募集要項・契約で確かめてください。")

a, b, c, d = st.columns(4)
fixed = a.number_input("固定費（円／年）", 0, 3_000_000, 300_000, 50_000, key="fixed",
                       help="機械の共同利用料、電気柵、製粉の委託、資材、通信費など")
target = b.number_input("目標の手取り（円／年）", 0, 10_000_000, 1_500_000, 100_000, key="target")
sigma = c.slider("天候の荒れ具合", 0.0, 0.6, 0.25, 0.05, key="sigma", help="その年の共通の良し悪しのばらつき")
p_bad = d.slider("大きな不作の年の確率", 0.0, 0.4, 0.10, 0.05, key="pbad", help="その年は収量が4割になる")

sims = {name: nx.simulate_income([s for s in streams if s[1] in groups], fixed, sigma, p_bad) for name, groups in nx.PORTFOLIOS.items()}
summ = pd.DataFrame([{"組み合わせ": k, **nx.income_summary(v, target)} for k, v in sims.items()])

st.subheader("組み合わせごとの手取り")
left, right = st.columns([1, 1])
with left:
    q = pd.DataFrame([{"組み合わせ": k, **{f"q{p}": float(np.quantile(v, p / 100)) / 10_000 for p in (5, 25, 50, 75, 95)}}
                      for k, v in sims.items()])
    order = list(nx.PORTFOLIOS)
    y = alt.Y("組み合わせ:N", sort=order, title=None, axis=alt.Axis(labelLimit=220))
    whisker = alt.Chart(q).mark_rule(color="#84878f", strokeWidth=2).encode(
        y=y, x=alt.X("q5:Q", title="1年の手取り（万円）。箱は真ん中の半分、線は下位5%〜上位5%"), x2="q95:Q")
    body = alt.Chart(q).mark_bar(color=ui.S1, size=24, cornerRadius=3).encode(
        y=y, x="q25:Q", x2="q75:Q", tooltip=["組み合わせ", alt.Tooltip("q5:Q", title="下位5%（万円）", format=".0f"),
                                             alt.Tooltip("q50:Q", title="中央値（万円）", format=".0f"),
                                             alt.Tooltip("q95:Q", title="上位5%（万円）", format=".0f")])
    mid = alt.Chart(q).mark_tick(color="white", thickness=2, size=24).encode(y=y, x="q50:Q")
    box = whisker + body + mid
    goal = alt.Chart(pd.DataFrame({"x": [target / 10_000]})).mark_rule(color=ui.S2, strokeWidth=2, strokeDash=[5, 4]).encode(x="x:Q")
    zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#84878f").encode(x="x:Q")
    st.altair_chart((box + zero + goal).properties(height=240), use_container_width=True)
    st.caption("橙の点線が目標、灰色の線が0円（赤字との境目）。")
with right:
    show = summ.copy()
    for col in ["平均", "中央値", "悪い年（下位5%）"]:
        show[col] = (show[col] / 10_000).round(0).astype(int).astype(str) + " 万円"
    show["目標に届かない確率"] = (show["目標に届かない確率"] * 100).round(0).astype(int).astype(str) + "%"
    st.dataframe(show[["組み合わせ", "悪い年（下位5%）", "中央値", "目標に届かない確率"]], hide_index=True, use_container_width=True)

full = sims["農＋X（すべて）"]
farm = sims["農だけ"]
st.info(f"農だけ → 農＋X（すべて）で、悪い年の手取りは **{np.quantile(farm, .05) / 10_000:.0f} 万円 → {np.quantile(full, .05) / 10_000:.0f} 万円**。"
        "天候を受けない柱（教える・支える・便り）が、不作の年の底を支えます。")

st.subheader("平年なら、どの柱がどれだけ稼ぐか")
ex = pd.DataFrame(nx.expected_by_stream(streams), columns=["名前", "区分", "手取りの期待値"])
ex["万円"] = ex["手取りの期待値"] / 10_000
bar = alt.Chart(ex).mark_bar(cornerRadiusEnd=4, size=14).encode(
    y=alt.Y("名前:N", sort="-x", title=None, axis=alt.Axis(labelLimit=320)),
    x=alt.X("万円:Q", title="手取りの期待値（万円／年。成り立つ確率をかけた値）"),
    color=alt.Color("区分:N", scale=alt.Scale(domain=nx.GROUPS, range=["#a9c9f2", "#2a78d6", "#1c5cab", ui.S2]),
                    legend=alt.Legend(orient="bottom", title=None)),
    tooltip=["名前", "区分", alt.Tooltip("万円:Q", format=".1f")])
st.altair_chart(bar.properties(height=36 * len(ex) + 60), use_container_width=True)
st.caption("生のまま売る柱は、固定費を払うと残りにくい。同じ畑の産物でも、風景として包む（定期便・加工）・体験にすると手取りが変わります。")

with st.expander("計算のしくみ"):
    st.markdown("""
- 1年ごとに、その年の天候の良し悪し（標準正規分布 × 荒れ具合）を1つ引き、品目ごとの小さなぶれを足します。
- ある確率で大きな不作の年になり、天候の効きが1の品目は収量が4割になります。効きが0.5なら、その半分だけ下がります。
- 各柱は「成り立つ確率」で、その年まるごと成り立つかが決まります（講師の契約・支援先・集客）。
- 手取り＝Σ（数量×単価×収量の倍率×（1−原価率））−固定費。1万年分を引いて分布を見ます（モンテカルロ法）。
- 品目どうしの天候は同じ年の良し悪しを共有するので、農の柱を増やしても悪い年はいっしょに悪くなります。天候を受けない柱を足すと分布の左の裾が持ち上がる、というのが「農＋X」のレジリエンスです。
""")
st.caption("これは予測ではなく、組み合わせを考えるための道具です。税・社会保険・補助金は入れていません。")
ui.contact()
