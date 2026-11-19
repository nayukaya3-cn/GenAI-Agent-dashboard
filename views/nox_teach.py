from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import genai_core as gc
import nox_core as nx
import ui

ui.header("nox_teach", "畑の一年は、そのまま作業学習の教材になります。収穫→選別→袋詰め→計量→片付けを、広島県の技能検定の手順書と"
          "同じ順番で練習すると、作業学習が検定の練習になり、級と評価表を持って職場体験実習へ、そして就職と定着へつながります。"
          "同じ工程の「なぜ」は、定時制・通信制の「科学と人間生活」の単元にもなります。")

# ------------------------------------------------------------
st.subheader("① 作業学習 → ② 技能検定 → ③ 実習 → ④ 就職・定着")
for col, (step, when, body, hand) in zip(st.columns(4), nx.PATHWAY):
    with col, st.container(border=True):
        st.markdown(f"**{step}**")
        st.caption(when)
        st.write(body)
        st.caption(f"次へ渡すもの：{hand}")
st.caption("①〜③は一度きりではありません。検定や実習で分かった課題を作業学習に戻して練習し直すことを、何度もくり返します。")

# ------------------------------------------------------------
st.subheader("畑の工程 ↔ 作業学習 ↔ 技能検定 ↔ 実習先")
st.dataframe(pd.DataFrame([(t[0], t[1], *nx.TEACH_LINK[t[0]][:2], nx.TEACH_LINK[t[0]][2], "・".join(f"{m}月" for m in t[4]))
                           for t in nx.TEACH],
                          columns=["農の工程", "作業学習の作業", "つながる技能検定", "実習先・就職先の例", "作業の中の「なぜ」（ひとこと）", "扱える月"]),
             hide_index=True, width="stretch")
st.caption("「なぜ」は作業中に一言で伝えるもの。くわしく扱うときは、下の「科学と人間生活」の単元になります。")

rows = nx.teach_months("支援学校の作業学習")
heat = pd.DataFrame([{"月": r["月"], "工程": t[0], "扱える": (int(r["月"][:-1]) in t[4]),
                      "検定": nx.TEACH_LINK[t[0]][0]} for r in rows for t in nx.TEACH])
chart = alt.Chart(heat).mark_rect(stroke="white", strokeWidth=2).encode(
    x=alt.X("月:N", sort=nx.MONTHS, title=None, axis=alt.Axis(orient="top", labelAngle=0)),
    y=alt.Y("工程:N", sort=[t[0] for t in nx.TEACH], title=None, axis=alt.Axis(labelLimit=220)),
    color=alt.condition("datum.扱える", alt.value(ui.S1), alt.value("#e9f1fc")), tooltip=["月", "工程", "検定", "扱える"])
st.altair_chart(chart.properties(height=26 * len(nx.TEACH)), width="stretch")
st.caption("濃い色：その月に畑・加工室で扱える作業。8月は授業がないので、検定第1回（〜8月末）の前の7月に計量・袋詰めを寄せます。")

# ------------------------------------------------------------
st.subheader("農＋X の一年と、検定・実習の時期")
st.dataframe(pd.DataFrame(nx.YEAR_PLAN, columns=["時期", "作業学習（農＋X の本物の材料で）", "検定・実習"]),
             hide_index=True, width="stretch")
st.caption("食品加工〈計量〉の期間は令和8年度の実施要項（各校で日を設定）。清掃の上位種目（モップ・ダスタークロス・スクイージー）は、"
           "年2回、会場を分けて実施されます。学年・実習の回数は、学校の教育課程と進路指導計画に合わせて直します。")

# ------------------------------------------------------------
st.subheader("1コマ90分の型")
for col, (step, body) in zip(st.columns(3), nx.WORK_LESSON):
    with col, st.container(border=True):
        st.markdown(f"**{step}**")
        st.write(body)

# ------------------------------------------------------------
st.subheader("評価表で、いまの級と次のめあてを見る")
st.write("検定の評価項目に、今日できた項目の印をつけます。評価項目1・2に合格したときだけ、3以降が数えられます。")
name = st.radio("種目", list(nx.KENTEI), horizontal=True, key="kentei")
k = nx.KENTEI[name]
st.caption(f"{k['時間']}　／　評価のポイント：{k['ポイント']}　／　農＋X での練習：{k['農＋X']}")
c1, c2 = st.columns([3, 2])
with c1:
    passed = [i for i, item in enumerate(k["項目"], 1) if st.checkbox(f"{i}. {item}", key=f"k_{name}_{i}")]
with c2:
    g = nx.kentei_grade(name, passed)
    st.metric(f"○の数 {g['数']} 個 → 級の目安", g["級"])
    if not g["1・2に合格"]:
        st.warning("評価項目1・2がそろうまで、3以降は数えられません。まず準備と手洗い（開始の報告）から。")
    st.info(f"次に練習する項目：{g['次に練習']}")
st.caption("項目名は、広島県教育委員会の評価表（六訂版・十訂版）を短くしたものです。各項目の中の細かい評価内容がすべてそろって○になります。"
           "本番の評価は審査員が行います。最新の評価表・手順書は県教育委員会のページで確かめてください。")

with st.expander("どの検定を組み合わせるか（令和5年度の実施状況）"):
    df = pd.DataFrame(nx.KENTEI_CHOICE, columns=["分野", "受検者（人）", "認定率（％）", "協力している業界", "就活での強み"])
    st.dataframe(df, hide_index=True, width="stretch")
    st.write("**2分野以上を組み合わせる**と、手順を守る力・体力・正確さを別々の場面で示せます。"
             "農＋X とつなぐなら「食品加工〈計量〉＋流通・物流〈商品化〉」、求人の数を重く見るなら「清掃の上位種目＋流通・物流」。")
    st.caption("ほぼ全員が受けるので、差になるのは「受けたこと」より「どの種目で何級か」。級は「何ができるか」とセットで、評価表を実習先に見せて伝えます。"
               "広島県独自の資格なので、県外では説明が必要です。次の段はひろしまアビリンピック。")

# ------------------------------------------------------------
st.subheader("3つの場面で記録し、実習先と共有する")
st.write("同じ評価項目を、作業学習・検定の練習・職場体験実習の3場面で「できる／支援があればできる／まだ」で記録します。"
         "JEED の職務分析シートと同じ書き方なので、そのまま実習先・就職先と共有できます。")
default = [["できる"] * 3, ["できる", "支援があればできる", "できる"], ["できる", "できる", "支援があればできる"],
           ["支援があればできる"] * 3] + [["まだ"] * 3 for _ in range(len(k["項目"]) - 4)]   # 架空の例
rec = pd.DataFrame(default, columns=nx.WORK_SCENES)
rec.insert(0, "評価項目", [f"{i}. {x}" for i, x in enumerate(k["項目"], 1)])
rec["どんな支援が必要か"] = ""
edited = st.data_editor(rec, key=f"rec_{name}", hide_index=True, width="stretch", disabled=["評価項目"],
                        column_config={s: st.column_config.SelectboxColumn(s, options=nx.JEED_LEVELS, required=True)
                                       for s in nx.WORK_SCENES})
edited["次の手立て"] = [nx.scene_check(r) for r in edited[nx.WORK_SCENES].values.tolist()]
st.dataframe(edited[["評価項目", "次の手立て"]], hide_index=True, width="stretch")
st.download_button("記録をCSVで保存（実習先との共有用）", edited.to_csv(index=False).encode("utf-8-sig"),
                   file_name=f"作業学習の記録_{name}.csv", mime="text/csv")
st.caption("記録には名前・写真・障害の種類を書きません。共有するときは、学校の手続きにそって、仮名や番号で。"
           "手立ての効果を確かめるときは、一人の記録を 道具箱 07 の ABAB で比べます。")

# ------------------------------------------------------------
st.subheader("特別編：生成AIでPOPをつくる・貼る・直す（全6回）")
st.write("流通・物流、パソコンの作業学習を経験した生徒向け。生成AIに任せるのは「一言の案」だけで、価格・産地・期限は必ず人が指示書から写し、"
         "確認チェックリストで点検して上司役に報告します。題材は自家製小麦粉・朝どり枝豆・季節の野菜で、直売所に実際に貼ります。")
st.dataframe(pd.DataFrame(nx.POP_UNIT, columns=["回", "生成AIの役割", "評価項目"]), hide_index=True, width="stretch")
st.caption("よりどころ：JEED「作業に必要な主な知識、技能・技術」百貨店・総合スーパー／売場管理（補助）L1 の 1-2「POP広告の作成、取り付け」、"
           "4-3「POP等の汚れ、破損、欠落のチェック及び簡単な補正」。生成AIを使えない日は、第3回を「一言の見本から選ぶ」に置きかえます。")
pop = Path(__file__).resolve().parents[1] / "static" / "pop_card.html"
if pop.exists():
    with st.expander("POPづくりカード（選ぶだけで質問文になる・確認チェック・印刷用画像）"):
        st.iframe(pop, height=1500)
        st.caption("このカードも外へ何も送りません。コピーできないときは、質問文を選んでコピーしてください。")

# ------------------------------------------------------------
st.subheader("卒業後：職場への定着を支える")
st.dataframe(pd.DataFrame(nx.ALUMNI, columns=["", "中身"]), hide_index=True, width="stretch")
st.caption("品出しだけの担当から「売場づくりに参加している」へ役割が広がると、定着でつまずきやすい「仕事が単調」「認められている感じがない」に効きます。")

# ------------------------------------------------------------
st.divider()
st.subheader("同じ工程を「なぜ」で教える：科学と人間生活（定時制・通信制）")
st.write("作業学習で「ひとこと」だった「なぜ」を、1つの問いとして記録をとって確かめると、「科学と人間生活」の単元になります。")
st.dataframe(pd.DataFrame([(t[0], t[2], t[3]) for t in nx.TEACH], columns=["農の工程", "科学と人間生活の単元", "情報Ⅰ・道具箱"]),
             hide_index=True, width="stretch")
st.caption("単元名は、光や熱の科学／物質の科学（材料とその再利用・衣料と食品）／生命の科学（ヒトの生命現象・微生物とその利用）／宇宙や地球の科学（太陽と地球・自然景観と自然災害）にそろえています。")
with st.expander("月ごとの中身と、1コマの流れ（4枚カード）"):
    aud = "定時制・通信制の「科学と人間生活」"
    st.dataframe(pd.DataFrame(nx.teach_months(aud)).rename(columns={"中身": nx.AUDIENCE[aud][0]}), hide_index=True, width="stretch")
    st.info(nx.AUDIENCE[aud][1])
    for col, ((step, body), (card, check)) in zip(st.columns(4), zip(nx.LESSON, gc.CARDS)):
        with col, st.container(border=True):
            st.markdown(f"**{card}**")
            st.caption(step)
            st.write(body)

st.subheader("教える X と、農・売る X のつながり")
st.markdown("""
- **作業を分ける力が、支援の力になる**：作業学習で工程を分け、検定の手順書にそろえた経験は、農業法人の業務を工程に分ける（道具箱 06）ときにそのまま使えます。
- **検定の評価表は、職場の言葉**：評価表・JEED のシートと同じ書き方で記録すると、実習先・就職先と同じ言葉で話せます。
- **販売実習は MVP の練習**：定期便1箱・体験1回のテスト販売（3 X 売る）を、袋詰め・値付け・POPまで生徒と一緒に小さく回せます。
""")
st.caption("生徒の名前・写真・成績・支援の記録は、発信にも生成AIにも出しません。学習の記録を研究に使う場合は、事前に本人・保護者の同意と学校の手続きをとります。")
ui.link("fit", "作業と人の組み合わせ・支援の量（道具箱 05 組む）", "🧩")
ui.link("measure", "手立ての効果を一人の記録で比べる（道具箱 07 確かめる・ABAB）", "📊")
ui.contact()
