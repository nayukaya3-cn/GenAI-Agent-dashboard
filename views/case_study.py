import altair as alt
import pandas as pd
import streamlit as st

import agri_case as ac
import ui

st.caption("研究（本人のみ）")
st.title("仮想研究事例：「使う」と「任せる」の境界設計")
if not ui.case_gate():
    st.stop()

st.write("小規模農業法人は、どの業務を「人がAIを使う」に留め、どの業務を「エージェントに任せる」と、ショックからの回復力が高まるか。"
         "A→B→C→D を一本の流れとして、架空のデータで最後まで通します。")
st.warning("データはすべて架空です（乱数から生成）。辞書・境目・係数は仮置きで、ここに出る数字は研究結果ではありません。"
           "分析の手順と、手順どうしのつなぎ方を確かめるための練習台です。")


@st.cache_data(show_spinner="計算しています…")
def run():
    data = ac.load()
    out = ac.pipeline(data)
    return data, out, ac.assignment(data["skills"], data["tasks"]), ac.rain_sweep(out["prm"])


@st.cache_data(show_spinner=False)
def dsweep(guard: float, saving: float, share: float, shock: tuple) -> pd.DataFrame:
    return ac.delegation_sweep(guard, saving, share, shock)


data, r, asg, sweep = run()
use, agent = r["shares"]
hb, hb0 = r["effect"]["hb_adjusted"], r["effect"]["hb_naive"]
res = r["week"]["results"]
PCT = alt.Axis(format="%")
GREY = "#50545d"

t0, ta, tb, tc, td, te = st.tabs(["全体の流れ", "A どこが困っているか", "B どう割り当てるか", "C 本当に効いたか", "D ショックに耐えるか", "データ"])

# ------------------------------------------------------------ 全体
with t0:
    st.subheader("一本の流れと、受け渡すもの")
    best_now = {k: ac.best_level(v) for k, v in r["sweeps"].items()}
    st.dataframe(pd.DataFrame([
        ("A どこが困っているか", "作業日誌（5法人・26週）", "辞書＋否定の除外、3類型、共起", f"事務のうち AIを使える作業 {use:.0%}、エージェントに任せられる作業 {agent:.0%}", "→ B の前提（AIの効く範囲）"),
        ("B どう割り当てるか", "作業表・技能マップ、A の割合", "全探索・貪欲法、動的計画法、Q学習", f"週の損失：固定計画 {res['固定計画（晴れ前提）']['loss']:.1f} → 動的計画法 {res['動的計画法（確率が既知の上限）']['loss']:.1f}", "→ C の「導入期」に入れる割当"),
        ("C 本当に効いたか", "ABAB 記録（5法人・16週）", "重なりのない割合・NAP、交絡の調整、階層ベイズ", f"事務作業の時短 {hb['saving']:.0%}（95%の幅 {hb['saving_lo']:.0%}〜{hb['saving_hi']:.0%}）", "→ D の係数（時短率）"),
        ("D ショックに耐えるか", "ショックの想定、C の時短率", "モンテカルロ・シミュレーション", "損失が最小の委任水準（ガードレール整備度0.5）：" + "、".join(f"{k} {v:.1f}" for k, v in best_now.items()), "→ 経営指標・設計シート（06 任せる）"),
    ], columns=["段階", "入れるデータ", "手法", "この事例で出た値", "次へ渡すもの"]), hide_index=True, use_container_width=True)
    st.caption("B→C のつなぎは、この仮想事例では概念上のものです（ABAB のダミーデータは B の結果と独立に生成しています）。"
               "実際の研究では、B で決めた割当を導入期（B期）の手立てとして現場に入れます。")
    st.subheader("7つの段との対応")
    st.dataframe(pd.DataFrame([
        ("A", "03 聞く・04 守る", "日誌を外部AIに入れず、辞書で読む。名前は仮名（W1 など）"),
        ("B", "05 組む・06 任せる", "合う度合いの点数と全探索・貪欲法をそのまま使い、天候の不確かさと承認の制約を足す"),
        ("C", "07 確かめる", "ABAB・重なりのない割合・NAP を複数法人に広げ、階層ベイズでまとめる"),
        ("D", "01 知る〜全体", "委任水準を一律に上げない、という方針を数で確かめる"),
    ], columns=["段階", "ダッシュボードの段", "使い方"]), hide_index=True, use_container_width=True)
    st.subheader("この仮想事例から読めること（仮定の下で）")
    st.markdown(
        f"- **語を数えるだけでは多く見積もる。**「遅れ」を含む日誌のうち、否定（遅れなし）を除くと残るのは一部です（A）。\n"
        f"- **事務は「使う／承認付きで任せる」に分かれ、収穫などの身体作業は任せる対象になりません**（A の委任マップ）。\n"
        f"- **天候を見ない固定計画がいちばん損をします。** その日だけを見る貪欲法は、週の途中の締めを落とします（B）。\n"
        f"- **素朴な前後比較は効果を小さく見せます。** 繁忙期と導入期が重なるためで、調整すると生成時の真値に近づきます（C）。\n"
        f"- **委任水準には「ちょうどよい所」があり、ガードレールを整えるほど右へ動きます。** 資材高騰には委任は効きません（D）。")

# ------------------------------------------------------------ A
with ta:
    d = r["diary"]
    st.subheader("語を数える：出現回数・日誌数・否定を除いた日誌数")
    kt = ac.keyword_table(data["diary"])
    c1, c2 = st.columns([2, 3])
    c1.dataframe(kt, hide_index=True, use_container_width=True)
    c1.caption(f"日誌は全部で {len(d):,} 件。「遅れなし」「故障はなかった」「人手は足りた」は困りごとではないので除きます。")
    long = kt.melt("語", ["含む日誌数", "否定を除いた日誌数"], var_name="数え方", value_name="日誌数")
    c2.altair_chart(alt.Chart(long).mark_bar(cornerRadiusEnd=3).encode(
        y=alt.Y("語:N", title=None, sort=ac.KEYWORDS), yOffset=alt.YOffset("数え方:N", sort=["含む日誌数", "否定を除いた日誌数"]),
        x=alt.X("日誌数:Q", title="日誌数"),
        color=alt.Color("数え方:N", scale=alt.Scale(domain=["含む日誌数", "否定を除いた日誌数"], range=[ui.S1, ui.S2]), legend=alt.Legend(orient="top", title=None)),
        tooltip=["語", "数え方", "日誌数"]).properties(height=200), use_container_width=True)

    st.subheader("困りごとを3つの類型に分ける")
    chk = ac.dictionary_check(d)
    m = st.columns(4)
    m[0].metric("困りごとのある日誌（生成時）", f"{chk['困りごとの日誌']:,}")
    m[1].metric("辞書が類型まで拾った", f"{chk['辞書が拾った']:,}", help=f"拾った中で生成時の類型と一致した割合 {chk['拾った中の一致率']:.0%}")
    m[2].metric("未分類（語はあるが手がかりなし）", chk["未分類"])
    m[3].metric("見落とし", chk["見落とし"])
    st.caption("ダミーなので、生成時の類型（正解）と突き合わせられます。一致率が高いのは、文例と辞書を同じ人が作ったからで、実際の日誌ではこうなりません。"
               "見落としは「いつもより時間がかかった」のように、辞書の語を使わない書き方です。該当した原文を読む工程は省けません。")
    mp = r["map"]
    heat = mp.melt(["作業"], ac.TYPES, var_name="類型", value_name="割合")
    base = alt.Chart(heat).encode(x=alt.X("類型:N", sort=ac.TYPES, title=None, axis=alt.Axis(orient="top", labelAngle=0, labelFontSize=13)),
                                  y=alt.Y("作業:N", sort=list(mp["作業"]), title=None, axis=alt.Axis(labelLimit=220, labelFontSize=12)))
    st.altair_chart((base.mark_rect(stroke="white", strokeWidth=2).encode(
        color=alt.Color("割合:Q", scale=alt.Scale(domain=[0, 1], range=["#e9f1fc", "#1c5cab"]), legend=alt.Legend(title="類型の割合", format="%")),
        tooltip=["作業", "類型", alt.Tooltip("割合:Q", format=".0%")])
        + base.mark_text(fontSize=12).encode(text=alt.Text("割合:Q", format=".0%"),
                                             color=alt.condition("datum.割合 >= 0.5", alt.value("white"), alt.value("#14171d")))
    ).properties(height=30 * len(mp) + 30), use_container_width=True)

    st.subheader("委任マップ")
    show = mp.copy()
    for k in ac.TYPES:
        show[k] = (show[k] * 100).round().astype(int).astype(str) + "%"
    st.dataframe(show, hide_index=True, use_container_width=True)
    st.caption("目安の決め方（仮置き）：身体作業型が半分以上なら「任せない」。そうでなければ、判断型が情報不足型より多いとき「承認付きで任せる」、少ないとき「生成AIを使う」。"
               "屋外・屋内の作業で「任せる」「使う」と出たときは、段取りや判断の部分だけが対象で、体を動かす部分は人のままです。")
    with st.expander("一緒に出る語（共起）と、月ごとの件数"):
        a, b = st.columns(2)
        a.dataframe(ac.cooccurrence(d), hide_index=True, use_container_width=True)
        month = d[d["類型"].isin(ac.TYPES)].groupby(["月", "類型"]).size().reset_index(name="日誌数")
        b.altair_chart(alt.Chart(month).mark_bar().encode(
            x=alt.X("月:O", title="月"), y=alt.Y("日誌数:Q", title="困りごとの日誌数"),
            color=alt.Color("類型:N", sort=ac.TYPES, scale=alt.Scale(domain=ac.TYPES, range=[ui.S1, ui.S2, "#84878f"]), legend=alt.Legend(orient="top", title=None)),
            order=alt.Order("類型:N"), tooltip=["月", "類型", "日誌数"]).properties(height=240), use_container_width=True)
    st.info(f"**B へ渡す値**　事務作業5つのうち、AIを使える作業 {use:.0%}・エージェントに任せられる作業 {agent:.0%}")

# ------------------------------------------------------------ B
with tb:
    st.subheader("作業と人の組み合わせ（法人アの技能マップ）")
    M = asg["matrix"]
    long = pd.DataFrame([{"人": p, "作業": t, "点": M[i][j], "割り当て": asg["best"][i] == j}
                         for i, p in enumerate(asg["people"]) for j, t in enumerate(asg["tasks"])])
    base = alt.Chart(long).encode(x=alt.X("人:N", sort=asg["people"], title=None, axis=alt.Axis(orient="top", labelAngle=0, labelFontSize=13)),
                                  y=alt.Y("作業:N", sort=asg["tasks"], title=None, axis=alt.Axis(labelLimit=220, labelFontSize=12)))
    st.altair_chart((base.mark_rect(stroke="white", strokeWidth=2).encode(
        color=alt.Color("点:Q", scale=alt.Scale(domain=[0, 100], range=["#e9f1fc", "#1c5cab"]), legend=alt.Legend(title="合う度合い（点）")), tooltip=["人", "作業", "点"])
        + base.mark_text(fontSize=12).encode(text="点:Q", color=alt.condition("datum.点 >= 60", alt.value("white"), alt.value("#14171d")))
        + base.transform_filter("datum.割り当て").mark_rect(fillOpacity=0, stroke="#14171d", strokeWidth=3)
    ).properties(height=30 * len(asg["tasks"]) + 30), use_container_width=True)
    st.caption(f"全部の組み合わせを調べた合計 {asg['best_score']} 点（太枠）、上の人から順に選ぶ貪欲法 {asg['greedy_score']} 点。"
               "6人×10作業なら全探索が一瞬で終わるので、この規模では強化学習は要りません。")

    st.subheader("天候が変わる1週間の計画")
    st.write(f"6日間で、屋外 {ac.DEMAND[0]}・屋内 {ac.DEMAND[1]}・事務 {ac.DEMAND[2]} 単位（1単位＝2人時）を片づけます。1日に使えるのは {ac.CAP} 単位。"
             f"雨の日は屋外が進みません（雨の確率30%）。3日目の終わりが出荷伝票の締めです。事務は「人のみ／生成AIを使う／エージェント（承認付き）」から選びます。")
    bar = pd.DataFrame([{"方法": k, "損失": v["loss"], "下": v["loss"] - 2 * v["se"], "上": v["loss"] + 2 * v["se"]} for k, v in res.items()])
    order = list(res)
    ch = alt.Chart(bar).encode(y=alt.Y("方法:N", sort=order, title=None, axis=alt.Axis(labelLimit=260, labelFontSize=12)))
    st.altair_chart((ch.mark_bar(color=ui.S1, cornerRadiusEnd=4, size=18).encode(x=alt.X("損失:Q", title="週の損失（小さいほど良い。線は平均±2標準誤差）"),
                                                                           tooltip=["方法", alt.Tooltip("損失:Q", format=".2f")])
                     + ch.mark_rule(color="#14171d", strokeWidth=2).encode(x="下:Q", x2="上:Q")).properties(height=190), use_container_width=True)
    a, b = st.columns(2)
    with a:
        st.markdown("**Q学習の学び方**")
        cv = pd.DataFrame(r["week"]["curve"], columns=["週の数", "損失"])
        st.altair_chart((alt.Chart(cv).mark_line(color=ui.S1, strokeWidth=2).encode(
            x=alt.X("週の数:Q", title="試した週の数"), y=alt.Y("損失:Q", title="その区間の平均の損失"), tooltip=["週の数", alt.Tooltip("損失:Q", format=".1f")])
            + alt.Chart(pd.DataFrame({"y": [r["week"]["dp_expected"]]})).mark_rule(color=ui.S2, strokeDash=[4, 3]).encode(y="y:Q")).properties(height=240),
            use_container_width=True)
        st.caption("破線は動的計画法の期待損失（上限）。学習中は試し打ちを混ぜるので、線は学習後の成績（上の棒）より高めに出ます。")
    with b:
        st.markdown("**雨の確率を変える**")
        st.altair_chart(alt.Chart(sweep).mark_line(strokeWidth=2, point=True).encode(
            x=alt.X("雨の確率:Q", axis=PCT, title="雨の確率"), y=alt.Y("損失:Q", title="週の損失"),
            color=alt.Color("方法:N", sort=order, scale=alt.Scale(range=[ui.S1, ui.S2, GREY]), legend=alt.Legend(orient="bottom", title=None, labelLimit=260, columns=1)),
            tooltip=["方法", alt.Tooltip("雨の確率:Q", format=".0%"), alt.Tooltip("損失:Q", format=".1f")]).properties(height=300), use_container_width=True)
        st.caption("晴れ続きなら固定計画で足ります。雨が増えるほど、天候を見て組み直す価値が出ます。")
    q, g, dpv = res["Q学習（強化学習）"]["loss"], res["貪欲法（その日いちばん進む）"]["loss"], res["動的計画法（確率が既知の上限）"]["loss"]
    st.markdown(f"- 動的計画法は、雨の確率が分かっている前提の上限です。現場では確率が分からないので、試行錯誤で学ぶQ学習と比べます。\n"
                f"- この設定のQ学習（6万週ぶんの試行）は {q:.1f}。貪欲法 {g:.1f} と上限 {dpv:.1f} のあいだです。"
                "状態の数が多く、表形式では学びきれていません。規模が上がるほど、関数近似やモデルを使う方法が必要になる、という見通しが立ちます。")
    un = r["week"]["unconstrained"]
    with st.container(border=True):
        st.markdown("**承認の制約を外すと**")
        st.write(f"効率だけを最適化すると、承認を省く行動が週に平均 {un['violations_per_week']:.1f} 回選ばれます"
                 f"（損失は {un['loss']:.2f}。制約ありの {dpv:.2f} との差は誤差の範囲）。"
                 "誤送信や誤発注の害は、この損失に入っていません。だから承認は、最適化に任せず、選べない行動として外から決めます（06 任せる の設計シート）。")
    st.info("**C へ渡すもの**　事務は「生成AIを使う」を基本にし、任せられる作業だけ承認付きでエージェントへ、という割当を導入期（B期）の手立てにします。")

# ------------------------------------------------------------ C
with tc:
    abab = data["abab"]
    st.subheader("5法人の ABAB 記録（事務作業時間、分／週）")
    ab = abab.assign(条件=abab["期"].str[0].map({"A": "A 導入なし", "B": "B 導入あり"}))
    st.altair_chart(alt.Chart(ab).mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=40, filled=True)).encode(
        x=alt.X("週:Q", title="週", axis=alt.Axis(tickMinStep=1, grid=False)), y=alt.Y("事務作業時間_分:Q", title="分／週", scale=alt.Scale(zero=False)),
        color=alt.Color("条件:N", scale=alt.Scale(range=[ui.S1, ui.S2]), legend=alt.Legend(orient="top", title=None)), detail="期:N",
        tooltip=["法人", "週", "期", "繁忙期", "雨の日数", "事務作業時間_分"]).properties(height=140, width=235).facet(
        facet=alt.Facet("法人:N", title=None, sort=list(abab["法人"].unique())), columns=3).resolve_scale(y="independent"))
    ov = ac.overlap_table(abab)
    st.dataframe(ov.assign(**{"Aの平均": ov["Aの平均"].round(0), "Bの平均": ov["Bの平均"].round(0),
                              "重なりのない割合": (ov["重なりのない割合"] * 100).round().astype(int).astype(str) + "%", "NAP": ov["NAP"].round(2)}),
                 hide_index=True, use_container_width=True)
    st.caption("図と重なりの指標だけを見ると、効果がはっきりしない法人が多く見えます。導入期が繁忙期と重なっているためです。")

    st.subheader("まぎれこむものを図にする")
    a, b = st.columns([2, 3])
    a.graphviz_chart('digraph { rankdir=LR; node [shape=box, style=rounded, fontname="sans-serif", fontsize=11]; '
                     '繁忙期 -> 事務作業時間; 繁忙期 -> 導入の時期 [style=dashed]; 天候 -> 事務作業時間; 導入の時期 -> 事務作業時間 [penwidth=2]; }')
    b.write("知りたいのは太い矢印（導入 → 事務作業時間）です。繁忙期は事務作業時間を増やし、しかも導入の時期と重なりやすい（破線）ので、"
            "調整しないと、導入の効果と繁忙期の影響が混ざります。繁忙期と雨の日数を回帰に入れて、矢印を切り分けます。")
    b.caption("この図は、このダミーデータの生成の仕方そのものです。実際の研究では、図に入れるべき要因を現場と一緒に洗い出します。")

    st.subheader("法人ごとの効果と、階層ベイズでまとめた効果")
    rows = []
    for name, tbl, h in [("素朴な比較（調整なし）", r["effect"]["naive"], hb0), ("繁忙期・雨を調整", r["effect"]["adjusted"], hb)]:
        for i, f in enumerate(tbl["法人"]):
            rows.append({"対象": f, "方法": name, "効果": h["theta"][i], "下": h["theta_lo"][i], "上": h["theta_hi"][i]})
        rows.append({"対象": "全体（μ）", "方法": name, "効果": h["mu"], "下": h["mu_lo"], "上": h["mu_hi"]})
    fp = pd.DataFrame(rows)
    targets = list(abab["法人"].unique()) + ["全体（μ）"]
    methods = ["素朴な比較（調整なし）", "繁忙期・雨を調整"]
    enc = dict(y=alt.Y("対象:N", sort=targets, title=None), yOffset=alt.YOffset("方法:N", sort=methods),
               color=alt.Color("方法:N", sort=methods, scale=alt.Scale(domain=methods, range=[GREY, ui.S1]), legend=alt.Legend(orient="top", title=None)))
    st.altair_chart((alt.Chart(fp).mark_rule(strokeWidth=2).encode(x=alt.X("下:Q", title="導入の効果（対数尺度。0より左なら時間が減った。線は95%の幅）"), x2="上:Q", **enc)
                     + alt.Chart(fp).mark_circle(size=80, opacity=1).encode(x="効果:Q", tooltip=["対象", "方法", alt.Tooltip("効果:Q", format=".3f"),
                                                                                           alt.Tooltip("下:Q", format=".3f"), alt.Tooltip("上:Q", format=".3f")], **enc)
                     + alt.Chart(pd.DataFrame({"x": [0.0]})).mark_rule(color="#14171d").encode(x="x:Q")
                     + alt.Chart(pd.DataFrame({"x": [ac.TRUE["mu"]]})).mark_rule(color=ui.S2, strokeDash=[4, 3]).encode(x="x:Q")
                     ).properties(height=300), use_container_width=True)
    st.caption(f"橙の破線は、ダミーデータを作るときに置いた真値（{ac.TRUE['mu']}）。実際の研究では真値は分かりません。")
    m = st.columns(4)
    m[0].metric("全体の効果 μ（調整後）", f"{hb['mu']:+.3f}", help=f"95%の幅 {hb['mu_lo']:+.3f}〜{hb['mu_hi']:+.3f}")
    m[1].metric("事務作業の時短", f"{hb['saving']:.0%}", help=f"95%の幅 {hb['saving_lo']:.0%}〜{hb['saving_hi']:.0%}")
    m[2].metric("時間が減った確率", f"{hb['p_neg']:.1%}")
    m[3].metric("全体の効果 μ（調整なし）", f"{hb0['mu']:+.3f}", help=f"95%の幅 {hb0['mu_lo']:+.3f}〜{hb0['mu_hi']:+.3f}")
    st.caption("法人ごとの効果は、全体の平均に少し引き寄せて推定しています（階層ベイズ。法人が5つしかないので、幅は広く出ます）。"
               "調整なしでは幅が0をまたぎ、「効いたとは言えない」という結論になります。")
    st.info(f"**D へ渡す値**　事務作業の時短率 {hb['saving']:.0%}（調整後の平均）")

# ------------------------------------------------------------ D
with td:
    st.subheader("ショックを与えて、回復を測る")
    st.write("1つの法人を「日々の作業能力と、積み残し」で表します。委任水準を上げると、事務から人手が浮いて回復が早まります。"
             "一方、エージェントの誤作動や情報漏えいが起きる確率は、委任水準の2乗に比例して上がるとします。ガードレールはその確率を下げます。")
    c1, c2 = st.columns(2)
    scen = c1.selectbox("ショック", list(data["shocks"]["シナリオ"]), key="case_shock")
    guard = c2.slider("ガードレールの整備度（06 任せる の確認項目が埋まるほど高い）", 0.0, 1.0, 0.5, 0.1, key="case_guard")
    shock = next(tuple(s) for s in data["shocks"].itertuples(index=False) if s[0] == scen)
    sw = dsweep(guard, r["saving"], r["adm_share"], shock)
    best = ac.best_level(sw)
    m = st.columns(4)
    m[0].metric("損失が最小の委任水準", f"{best:.1f}")
    m[1].metric("そのときの累積損失", f"{sw['loss'].min():.1f}", delta=f"{sw['loss'].min() - sw['loss'].iloc[0]:+.1f}（委任なしとの差）", delta_color="inverse")
    m[2].metric("回復までの日数", f"{sw.loc[sw['委任水準'] == best, 'recovery'].iloc[0]:.0f}日", help=f"委任なしでは {sw['recovery'].iloc[0]:.0f}日")
    m[3].metric("誤作動・漏えいの回数（150日）", f"{sw.loc[sw['委任水準'] == best, 'incidents'].iloc[0]:.1f}")
    a, b = st.columns(2)
    xs = alt.X("委任水準:Q", title="委任水準（任せられる事務のうち、エージェントに渡す割合）", axis=PCT)
    mark = alt.Chart(pd.DataFrame({"x": [best]})).mark_rule(color=ui.S2, strokeDash=[4, 3]).encode(x="x:Q")
    a.altair_chart((alt.Chart(sw).mark_line(color=ui.S1, strokeWidth=2, point=True).encode(
        x=xs, y=alt.Y("loss:Q", title="累積損失（小さいほど良い）", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("委任水準:Q", format=".0%"), alt.Tooltip("loss:Q", format=".1f", title="累積損失")]) + mark).properties(height=260), use_container_width=True)
    b.altair_chart((alt.Chart(sw).mark_line(color=ui.S1, strokeWidth=2, point=True).encode(
        x=xs, y=alt.Y("recovery:Q", title="ショックが終わってから回復までの日数"),
        tooltip=[alt.Tooltip("委任水準:Q", format=".0%"), alt.Tooltip("recovery:Q", format=".0f", title="回復日数")]) + mark).properties(height=260), use_container_width=True)
    st.caption("橙の破線が、損失が最小の委任水準。回復は委任を増やすほど早まりますが、事故の損失が増えるので、損失の合計には底ができます。300回の試行の平均です。")

    st.subheader("ショック × ガードレールごとの、損失が最小の委任水準")
    grid = pd.DataFrame([{"ショック": s[0], **{f"整備度 {g:.1f}": ac.best_level(dsweep(g, r["saving"], r["adm_share"], tuple(s))) for g in (0.0, 0.5, 1.0)}}
                         for s in data["shocks"].itertuples(index=False)])
    st.dataframe(grid, hide_index=True, use_container_width=True)
    st.markdown("- ガードレールを整えるほど、任せてよい範囲が広がります。順番は「先に守りを固め、あとから委任を広げる」です。\n"
                "- 資材高騰は作業能力を下げないので、このモデルでは委任を増やしても効きません。値上がりには、仕入れや価格の側の手立てが要ります。\n"
                "- H_score につなぐなら、ガードレールの整備度が境界設計スコアに、回復日数と累積損失がレジリエンスの指標に当たります。他の因子との対応は未設定です。")
    with st.expander("このシミュレーションの仮定（すべて仮置き）"):
        st.dataframe(pd.DataFrame([
            ("1日の作業の需要", ac.SIM["demand"], "平時の作業能力を1としたとき"), ("全作業に占める事務の割合", round(r["adm_share"], 2), "B の週の作業量から"),
            ("事務の時短率", round(r["saving"], 3), "C の推定値"), ("エージェントに全部渡したときの追加の時短", ac.SIM["agent_extra"], "仮置き"),
            ("事故の確率（委任水準1、ガードレール0）", ac.SIM["p0"], "1日あたり"), ("ガードレールで下がる割合（整備度1）", ac.SIM["guard_cut"], ""),
            ("事故のあとの能力低下", ac.SIM["incident_drop"], f"{ac.SIM['incident_days']}日間"), ("事故1回の損失", ac.SIM["incident_cost"], "後始末・信用"),
            ("積み残し1単位・1日あたりの損失", ac.SIM["delay_cost"], ""),
        ], columns=["仮定", "値", "メモ"]), hide_index=True, use_container_width=True)
        st.caption("値を変えれば結論も変わります。`agri_case.py` の SIM を書きかえて確かめてください。実際の研究では、気象・市況の公開データと現場の記録から決めます。")

# ------------------------------------------------------------ データ
with te:
    st.subheader("ダミーデータ（data/agri_case/）")
    st.write(f"`python agri_case.py --make-data` で作り直せます（乱数の種 {ac.SEED}。同じ種なら毎回同じ中身）。実在の法人・人・日誌とは無関係です。")
    names = {"farms": "法人（5つ）", "tasks": "作業と負担", "skills": "技能マップ（法人ア）", "diary": "作業日誌", "abab": "ABAB 記録", "shocks": "ショックの想定"}
    pick = st.selectbox("表", list(names), format_func=lambda k: f"{names[k]}　{len(data[k]):,}行", key="case_table")
    st.dataframe(data[pick].head(300), hide_index=True, use_container_width=True)
    st.caption("先頭の300行までを表示しています。「生成時の類型」は正解ラベルで、実際の日誌にはありません。")
