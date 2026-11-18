import altair as alt
import pandas as pd
import streamlit as st

import nox_core as nx
import ui

ui.header("nox_rotation", "パン用小麦と枝豆・大豆は、作業の山がきれいにずれます。そこに野菜と加工、X（教える・支える）の時間を重ね、"
          "毎月「余白」が残るかを確かめます。作業時間は仮置きです。自分の畑の記録で書きかえてください。")

st.subheader("ブロック輪作の一年")
st.dataframe(pd.DataFrame(nx.ROTATION, columns=["季節", "区画A（穀物→豆）", "区画B（豆→穀物）", "ハウス（夏野菜・葉物）"]),
             hide_index=True, use_container_width=True)
st.caption(nx.ROTATION_NOTE)

st.subheader("時間の予算")
left, right = st.columns([1, 2])
with left:
    with st.container(border=True):
        st.markdown("**農（面積・量）**")
        scale = {}
        for name, (unit, _) in nx.FARM.items():
            label = f"{name}（{'×10a' if unit == '10a' else '×1a' if unit == '1a' else '倍'}）"
            scale[name] = st.number_input(label, 0.0, 5.0, float(nx.FARM_DEFAULT_SCALE[name]), 0.5, key=f"sc_{name}")
    with st.container(border=True):
        st.markdown("**X と発信**")
        teach = st.slider("非常勤講師（授業と準備、週あたり時間）", 0, 30, 10, key="teach_w")
        support = st.slider("マーケティング支援（月あたり時間）", 0, 80, 20, key="support_m")
        media = st.slider("自分の発信（週あたり時間）", 0, 10, 3, key="media_w")
        ev = st.multiselect("体験イベントを開く月", list(nx.EVENTS), default=list(nx.EVENTS),
                            format_func=lambda m: f"{m}月 {nx.EVENTS[m]}", key="events")
    cap = st.slider("農と X に使える時間（週あたり）", 20, 70, 45, key="cap",
                    help="睡眠・家事・移動などを除いて、農と X に使える時間です。")
load = nx.month_load(scale, teach, support, media, {m: nx.EVENTS[m] for m in ev})
sl = nx.slack(load, cap)
with right:
    long = pd.DataFrame([{"月": nx.MONTHS[i], "活動": name, "区分": g, "時間": v[i]} for name, (g, v) in load.items() for i in range(12)])
    order = [n for n, (g, _) in load.items() if g == "農"] + [n for n, (g, _) in load.items() if g == "X"]
    palette = ["#1c5cab", "#2a78d6", "#6aa3e8", "#a9c9f2", "#d5e5f9", "#eb6834", "#f29a6e", "#f7c3a6", "#fbe0d1"]
    bars = alt.Chart(long).mark_bar().encode(
        x=alt.X("月:N", sort=nx.MONTHS, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("sum(時間):Q", title="時間（月）"),
        color=alt.Color("活動:N", sort=order, scale=alt.Scale(domain=order, range=palette[:len(order)]),
                        legend=alt.Legend(orient="bottom", columns=2, title=None, labelLimit=260)),
        order=alt.Order("区分:N"), tooltip=["月", "活動", alt.Tooltip("時間:Q", format=".0f")])
    capline = alt.Chart(pd.DataFrame({"使える時間": [cap * nx.WEEKS_PER_MONTH]})).mark_rule(
        strokeDash=[5, 4], strokeWidth=2, color="#14171d").encode(y="使える時間:Q")
    st.altair_chart((bars + capline).properties(height=380), use_container_width=True)
    st.caption("青が農、橙が X。点線が使える時間。点線と棒の頭のあいだが余白（発信・企画・休む時間）です。")

df = pd.DataFrame(sl)
tight = df[df["判定"] != "余白あり"]
c1, c2, c3 = st.columns(3)
c1.metric("1年の農の時間", f"{df['農'].sum():.0f} 時間")
c2.metric("1年の X の時間", f"{df['X'].sum():.0f} 時間")
c3.metric("余白がいちばん少ない月", f"{df.loc[df['余白'].idxmin(), '月']}（{df['余白'].min():.0f} 時間）")
if len(tight):
    st.warning("余白が使える時間の2割を切る月：" + "、".join(f"{r['月']}（{r['判定']}）" for _, r in tight.iterrows())
               + "。その月の作付け・イベント・X の量を減らすか、人手（1日農業バイト・援農）を入れます。")
else:
    st.success("どの月も、使える時間の2割以上の余白が残ります。")
with st.expander("月ごとの数字"):
    st.dataframe(df.round(0), hide_index=True, use_container_width=True)

st.subheader("余白をつくる打ち手")
st.markdown("""
- **夏野菜は「自家消費＋α」に絞る**：トマト・きゅうりは真夏に毎日手がかかり、7〜8月の X と重なります。
- **枝豆は早生にして、7月の収穫を授業の夏休みに寄せる**：授業のある週が少ない月に、農の山を置きます。
- **収穫・袋詰めは体験イベントにする**：作業そのものを商品にすると、人手と売上が同時に増えます。
- **小麦の乾燥・製粉は地域の製粉所や機械の共同利用を先に決める**：品質（パンのふくらみ）を左右し、6月の山を低くします。
- **鳥獣害の備えは播種の前に**：種まき直後の大豆、実った小麦はハト・カラス・イノシシに狙われます。
""")
ui.link("fit", "作業を人に割りふる（道具箱 05 組む）", "🧩")
ui.contact()
