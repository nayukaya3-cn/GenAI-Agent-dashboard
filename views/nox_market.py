import altair as alt
import pandas as pd
import streamlit as st

import diary_ui
import genai_core as gc
import insta_ui
import nox_core as nx
import ui

ui.header("nox_market", image="static/nox_market_scene.svg", lead="売るのは農産物ではなく、農産物が生まれる風景と価値観です。まず自分の畑で、風景を小さな定期便と体験に包み、"
          "ファンと直接つながる。その型を、農業法人・農業関連企業へのマーケティング支援（X）にも使います。")

st.subheader("① 風景をパッケージにする")
left, right = st.columns([1, 1])
with left:
    scene = st.radio("届けたい風景", list(nx.SCENES), key="scene")
    farm_name = st.text_input("農園・ブランドの呼び名", "○○の畑", key="farm_name")
    who, value, box, when, event, story = nx.SCENES[scene]
    with st.container(border=True):
        st.markdown(f"**だれに**：{who}")
        st.markdown(f"**届ける価値観**：{value}")
        st.markdown("**定期便の中身**")
        for item in box:
            st.markdown(f"- {item}")
        st.markdown(f"**届ける時期**：{when}　／　**体験**：{event}")
        st.markdown(f"**物語の柱**：{story}")
with right:
    st.markdown("**パッケージの設計メモ（コピーして使う）**")
    st.code(nx.package_card(scene, farm_name), language=None, wrap_lines=True)
    st.caption("中身は例です。自分の畑で、いちばん人に見せたい場面を1文にするところから書きかえてください。")

st.subheader("② 物語を毎月とどける（発信カレンダー）")
st.write("完成品ではなくプロセスを売ります。畑の作業カレンダーが、そのまま発信の話題になります。")
st.dataframe(pd.DataFrame(nx.STORY, columns=["月", "畑で起きること", "発信の話題", "売る・誘うもの", "教室とつなぐ"]),
             hide_index=True, use_container_width=True)
month = st.select_slider("今月", nx.MONTHS, value="11月", key="story_month")
prompt = gc.build_prompt(nx.sns_parts(scene, month))
st.markdown("**生成AIに貼る質問文**（道具箱 03 聞く の5部品で組み立てています）")
st.code(prompt, language=None, wrap_lines=True)
chk = gc.scan(prompt)
st.caption(f"貼る前の点検：{ui.LIGHT_ICON[chk['level']]} {gc.LIGHT_MESSAGE[chk['level']]}")
st.caption("この画面は生成AIを呼び出しません。出てきた文の数字・日付・名前は、元の記録と照らしてから投稿します（道具箱 04 守る）。")

st.subheader("③ ファンの育ち方")
st.write("1万人の浅いお客さんより、毎年かかわってくれる100人。投稿を見た人が、定期便・オーナーになるまでの流れを数で見ます。")
c1, c2 = st.columns(2)
with c1:
    reach = st.number_input("1年で投稿を見てくれる人", 100, 200_000, 5_000, 500, key="reach")
    rates = [st.slider(f"{nx.FUNNEL[i][0]}（前の段からの割合）", 0.0, 1.0, nx.FUNNEL[i][1], 0.01, key=f"fr{i}")
             for i in range(1, len(nx.FUNNEL))]
    f = nx.funnel(reach, rates)
    fd = pd.DataFrame({"段": [s[0] for s in nx.FUNNEL], "人": f})
    st.altair_chart(alt.Chart(fd).mark_bar(color=ui.S1, cornerRadiusEnd=4, size=18).encode(
        y=alt.Y("段:N", sort=None, title=None, axis=alt.Axis(labelLimit=260)), x=alt.X("人:Q", scale=alt.Scale(type="symlog"), title="人（目盛りは圧縮）"),
        tooltip=["段", alt.Tooltip("人:Q", format=",.0f")]).properties(height=170), use_container_width=True)
with c2:
    retention = st.slider("定期便を翌年も続ける割合", 0.0, 0.95, 0.75, 0.05, key="ret")
    spend = st.number_input("1人が1年に使う額（円）", 1_000, 200_000, 25_000, 1_000, key="spend")
    curve = nx.fan_curve(f[-1], retention, years=5)
    cd = pd.DataFrame({"年": [f"{i + 1}年目" for i in range(5)], "会員": curve})
    st.altair_chart(alt.Chart(cd).mark_line(point=True, color=ui.S2, strokeWidth=2).encode(
        x=alt.X("年:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)), y=alt.Y("会員:Q", title="定期便・オーナーの人数"),
        tooltip=["年", alt.Tooltip("会員:Q", format=".0f")]).properties(height=170), use_container_width=True)
m1, m2, m3 = st.columns(3)
m1.metric("毎年あたらしく会員になる人", f"{f[-1]:.0f} 人")
m2.metric("5年目の会員", f"{curve[-1]:.0f} 人", help=f"続ける割合が変わらなければ、いずれ {f[-1] / max(1e-9, 1 - retention):.0f} 人に近づきます")
m3.metric("1人の生涯の支出（LTV）", f"{nx.ltv(spend, retention) / 10_000:.1f} 万円")
st.caption("続ける割合を5ポイント上げることは、新しい人を増やすことと同じくらい効きます。体験イベントと畑の便りは、続ける割合を上げるための手立てです。")

st.subheader("④ 小さく試す（MVP）の判定")
st.write("最初は定期便1箱・体験1回の大きさで、知り合いや便りの登録者に案内します。少ない人数でも、言えることと言えないことを分けます。")
k1, k2, k3 = st.columns(3)
invited = k1.number_input("案内した人", 1, 2000, 30, 1, key="inv")
bought = k2.number_input("買った人", 0, 2000, 6, 1, key="bought")
need = k3.slider("続けるのに必要な買う割合（損益分岐）", 0.01, 0.6, 0.10, 0.01, key="need")
j = nx.mvp_judge(invited, min(bought, invited), need)
st.metric("買う割合が損益分岐を超えている確率", f"{j['分岐を超える確率']:.0%}",
          help=f"買う割合の見込み：平均 {j['平均']:.0%}、80%の幅 {j['下']:.0%}〜{j['上']:.0%}（ベータ分布）")
st.caption(f"買う割合の見込みは 平均 {j['平均']:.0%}（80%の幅 {j['下']:.0%}〜{j['上']:.0%}）。"
           + ("9割以上の確率で分岐を超えています。量を少し増やして次を試します。" if j["分岐を超える確率"] >= 0.9
              else "まだ決められません。案内の相手や中身を変えて、もう一度小さく試します。" if j["分岐を超える確率"] >= 0.5
              else "分岐を下回る見込みが高い。風景（だれに・何を）から見直します。"))

st.subheader("⑤ X：農業法人・農業関連企業へのマーケティング支援")
st.write("自分の畑で試した①〜④の型を、支援先の法人に持ちこみます。支援先の風景は、支援先の人と一緒に言葉にします。")
st.dataframe(pd.DataFrame(nx.SERVICE, columns=["段", "支援の中身", "使う道具", "成果物", "目安の時間"]),
             hide_index=True, use_container_width=True)
st.caption("支援先の顧客名簿・売上・従業員の情報は、生成AIに貼りません（道具箱 04 守る）。定期便の受付〜発送は、道具箱 06 任せる に「定期便（農＋X）」の流れを入れてあります。")
st.caption("「1 診る」で支援先の作業日誌や、お客さんの感想を読むときは、下の ⑥ を使います（困りごと・不満の芽を数えてから、原文で確かめる）。")
ui.link("agent", "定期便の流れを工程に分ける（道具箱 06 任せる）", "🛠️")
ui.link("measure", "効いた発信・商品を数で比べる（道具箱 07 確かめる）", "📊")

diary_ui.section(farm_name)
insta_ui.section(scene, farm_name, month)
ui.contact()
