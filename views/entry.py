"""作業学習×生成AIで「働く入口」をつくる：特別支援学校／通信制高校・サポート校の校長への提案。
計算とデータは entry_core.py（Streamlit 非依存）。
"""
import altair as alt
import pandas as pd
import streamlit as st

import entry_core as ec
import ui

st.caption("作業学習×生成AIで「働く入口」をつくる ／ 対象：特別支援学校／通信制高校・サポート校")
st.title("働く入口をつくる：校長への提案")
st.write(ec.CORE)
st.write("PRで売り込むのは自分の経歴ではなく、**学校の課題を解決すること**です。学校種を選ぶと、困りごと・具体例・試行計画・PRトークがその学校向けに切りかわります。")
st.divider()

school = st.radio("提案する学校", ec.SCHOOLS, horizontal=True, key="entry_school")
other = ec.SCHOOLS[1 - ec.SCHOOLS.index(school)]

tabs = st.tabs(["① 型と全体像", "② 困りごと→解決", "③ 4分野の具体例", "④ 始めやすさと3か月計画",
                "⑤ PRトーク", "⑥ 生成AIで手順書", "⑦ 評価をベイズで見る", "⑧ 注意点"])

# ------------------------------------------------------------
with tabs[0]:
    st.image("static/entry_flow.svg", width="stretch")
    st.subheader("すべての分野に共通する「型」")
    for col, (step, body, hand) in zip(st.columns(len(ec.CYCLE)), ec.CYCLE):
        with col, st.container(border=True):
            st.markdown(f"**{step}**")
            st.write(body)
            st.caption(f"次へ渡すもの：{hand}")
    st.caption("③で見つかった課題を①②に戻して、何度も回します。4つの分野は、どれもこの型で進めます。")

    st.subheader("4分野は「育てる → 加工する → 届ける」でつながる")
    st.write(" → ".join(f"{ec.FIELD_ICON[f]} {f}（{ec.FIELD_VERB[f]}）〔{hand}〕" for f, hand in ec.CHAIN)
             + " → 学校祭・地域販売・企業実習")
    st.write(f"{ec.FIELD_ICON['ものづくり']} ものづくりは、3分野の作業を治具で改善する役。バラバラの4つの活動ではなく、"
             "校内で一通り体験できて、改善し続けられる仕組みです。")

    st.subheader("特別支援の視点を入れる共通の工夫")
    st.dataframe(pd.DataFrame(ec.COMMON_TIPS, columns=["工夫", "具体的なやり方"]), hide_index=True, width="stretch")

    st.subheader(f"段階：{school}")
    for col, (step, when, body) in zip(st.columns(len(ec.STAGES[school])), ec.STAGES[school]):
        with col, st.container(border=True):
            st.markdown(f"**{step}**")
            st.caption(when)
            st.write(body)

    st.subheader("2校種の比較：同じ型でも、強調する点が違う")
    st.dataframe(pd.DataFrame(ec.COMPARE, columns=["観点", *ec.SCHOOLS]), hide_index=True, width="stretch")
    if school == ec.SCHOOLS[1]:
        with st.expander("なぜ通信制・サポート校で特別支援の視点が活きるのか", expanded=True):
            st.write("通信制高校やサポート校には、全日制になじめなかった生徒、不登校を経験した生徒、診断の有無にかかわらず発達特性のある生徒が多く在籍しています。"
                     "一方で、特別支援学校のような専門の体制はないことが多く、支援の考え方を持つ職員の価値が高くなります。")
            st.dataframe(pd.DataFrame(ec.WHY_TSUSHIN, columns=["特別支援の視点", "通信制での使いどころ"]), hide_index=True, width="stretch")
            st.caption("サポート校は進学支援に強いところが多く、特性のある生徒の就労支援は手薄になりがちです。そこを補える人材としてアピールできます。")

# ------------------------------------------------------------
with tabs[1]:
    st.subheader(f"校長の困りごと → 提案する解決策（{school}）")
    st.write("校長が抱えている困りごとに印をつけます。印をつけたものは ⑤ PRトーク に使われます。")
    pains = ec.PAINS[school]
    chosen = []
    for k, (issue, fix) in pains.items():
        c1, c2 = st.columns([2, 3])
        with c1:
            if st.checkbox(issue, key=f"pain_{school}_{k}", value=k == next(iter(pains))):
                chosen.append(k)
        with c2:
            st.markdown(f"→ {fix}")
    st.session_state["entry_pains"] = chosen
    if len(chosen) > 2:
        st.caption("PRトークでは、最初の2つだけを使います。30秒で伝えられるのは課題2つまでです。")

# ------------------------------------------------------------
with tabs[2]:
    st.subheader("分野別の具体例")
    field = st.radio("分野", ec.FIELDS, horizontal=True, key="entry_field",
                     format_func=lambda f: f"{ec.FIELD_ICON[f]} {f}")
    d = ec.FIELD_DETAIL[field]
    rows = [(k, d[k]) for k in ["活動", "手順書の例", "特別支援の工夫", "生成AI・AIの使いどころ", "つなぐ先"]]
    rows.insert(3, (f"{school}では", d[school]))
    st.dataframe(pd.DataFrame(rows, columns=["項目", "内容"]), hide_index=True, width="stretch")
    st.success(f"校長への一言：「{d['校長への一言']}」", icon="💬")
    with st.expander(f"{other}では"):
        st.write(d[other])
    if field == "食品加工":
        st.warning("販売する場合は保健所の許可や届出が必要なことがあります。技能検定は特別支援学校の生徒向けなので、"
                   "通信制・サポート校では評価表の基準を校内評価に使います。", icon="⚠️")
    if field == "ものづくり":
        st.warning("ノズルが高温になるため、やけど防止の手順と換気が必要です。", icon="⚠️")
        ui.link("print3d", "3Dプリンター業務推進ボード（仕上げ評価・治具のOpenSCAD生成）を開く")
    if school == ec.SCHOOLS[0] and field in ("食品加工", "流通・物流"):
        ui.link("nox_teach", "X 教える：技能検定の評価表で級の目安と次のめあてを見る")

# ------------------------------------------------------------
with tabs[3]:
    st.subheader("いま学校にあるもので、始めやすい順を出す")
    have = st.multiselect("いま学校にあるもの・人", ec.RESOURCES, default=["備品庫・教材室", "PC・タブレット"], key="entry_have")
    order = ec.start_order(have, school)
    st.dataframe(pd.DataFrame([{"順": r["順"], "分野": f"{ec.FIELD_ICON[r['分野']]} {r['分野']}",
                                "足りないもの": "・".join(r["足りないもの"]) or "なし",
                                "費用の目安（円）": r["費用の目安"], "メモ": "／".join(r["メモ"])} for r in order]),
                 hide_index=True, width="stretch")
    st.caption("並べ方：足りないものが少ない → 費用が安い → 学校種の定番の順（通信制は物流から、特別支援は食品加工から）。"
               "費用は仮置きです。学校の見積もりで entry_core.py の COST を書きかえてください。")

    st.subheader("3か月の試行計画（校長が判断しやすい形）")
    col = 1 if school == ec.SCHOOLS[0] else 2
    st.dataframe(pd.DataFrame([(p[0], p[col], p[3]) for p in ec.PILOT], columns=["期間", "内容", "費用"]),
                 hide_index=True, width="stretch")
    st.markdown("**成果指標（KPI）**")
    st.dataframe(pd.DataFrame([(k[0], k[col]) for k in ec.KPI], columns=["指標", "測るもの"]), hide_index=True, width="stretch")
    st.caption("いきなり全分野を提案すると負担に見えます。費用のかからないものから始め、3か月目に数字で報告して続けるかを判断してもらいます。")

# ------------------------------------------------------------
with tabs[4]:
    st.subheader("校長へのPRトーク")
    f2 = st.selectbox("話の中心にする分野", ec.FIELDS, key="entry_talk_field",
                      index=ec.FIELDS.index(ec.start_order(st.session_state.get("entry_have", []), school)[0]["分野"]))
    long = st.toggle("2分版（具体例・型・ひとことを足す）", key="entry_long")
    talk = ec.pr_talk(school, st.session_state.get("entry_pains", []), f2, long=long)
    st.text_area("トーク（そのまま読める形）", talk, height=260 if long else 140, key=f"talk_{school}_{f2}_{long}")
    st.caption("困りごとは ② で選んだもの（最大2つ）を使います。学校名・地域の企業名を入れて言いかえてください。")
    st.subheader("想定される質問と答え方")
    st.dataframe(pd.DataFrame(ec.FAQ, columns=["質問", "答え方"]), hide_index=True, width="stretch")

# ------------------------------------------------------------
with tabs[5]:
    st.subheader("生成AIに貼る「手順書づくり」の質問文")
    st.write("この画面は生成AIを呼び出しません。組み立てた文をコピーして、学校で使ってよい生成AIに自分で貼ります。")
    c1, c2 = st.columns(2)
    with c1:
        f3 = st.selectbox("分野", ec.FIELDS, key="entry_prompt_field")
        task = st.text_input("作業名", "強力粉の計量", key="entry_task")
        furi = st.checkbox("ふりがなをつける", value=True, key="entry_furi")
    with c2:
        steps = st.text_area("いまの工程（1行に1つ）", "手を洗う\nはかりの0を確認する\n容器を乗せて0に戻す\n150gまで入れる\n許容範囲内か確認する",
                             height=170, key="entry_steps")
    try:
        st.code(ec.manual_prompt(f3, task, steps.splitlines(), school, furigana=furi), language=None)
    except ValueError as e:
        st.warning(str(e))
    st.caption("生徒の氏名・診断名・支援記録は入れないでください。出てきた手順書は、工程が増減していないかを必ず人が確かめます。")

# ------------------------------------------------------------
with tabs[6]:
    st.subheader("「この工程ができる確率」をベイズで見る")
    st.write("評価表の記録（何回中何回できたか）から、その工程が次もできる確率を推定します。回数が少ないうちは幅が広く出ます。")
    c1, c2 = st.columns(2)
    with c1:
        att = st.number_input("記録した回数", 0, 100, 10, key="entry_att")
        suc = st.number_input("できた回数", 0, 100, 7, key="entry_suc")
    if suc > att:
        st.warning("できた回数は、記録した回数以下にしてください。")
    else:
        r = ec.step_probability(int(suc), int(att))
        with c2, st.container(border=True):
            st.metric("できる確率（平均）", f"{r['平均']:.0%}")
            st.write(f"80%の確からしさで {r['下']:.0%}〜{r['上']:.0%} の間")
            st.write(f"「8割を超える」確率：{r['8割を超える確率']:.0%}")
        band = pd.DataFrame([{"回": n, "下": ec.step_probability(min(round(suc / max(att, 1) * n), n), n)["下"],
                              "上": ec.step_probability(min(round(suc / max(att, 1) * n), n), n)["上"]} for n in range(0, 31, 2)])
        chart = alt.Chart(band).mark_area(opacity=0.35, color=ui.S1).encode(
            x=alt.X("回:Q", title="記録の回数（同じ割合でできたとき）"), y=alt.Y("下:Q", title="できる確率", axis=alt.Axis(format="%"),
                                                                    scale=alt.Scale(domain=[0, 1])), y2="上:Q")
        st.altair_chart(chart.properties(height=220), width="stretch")
        st.caption("記録が増えるほど幅が狭くなります。目安であって合否ではありません。級は技能検定の評価で決まります。")

# ------------------------------------------------------------
with tabs[7]:
    st.subheader("注意点")
    st.dataframe(pd.DataFrame(ec.CAUTIONS, columns=["項目", "注意すること"]), hide_index=True, width="stretch")

ui.contact()
