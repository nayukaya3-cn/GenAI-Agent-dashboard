"""「X 売る」ページの ⑥ 支援先の声を読む（作業日誌・お客さんの感想の困りごと分析）の画面部分

計算は diary_core.py（Streamlit 非依存）。ブラウザ1枚で動くフル版は static/diary_analysis.html。
"""
from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import diary_core as dc
import ui

HTML_PATH = Path(__file__).resolve().parent / "static" / "diary_analysis.html"
S3 = "#1baf7a"   # 3つめの系列（S1・S2 と合わせて色覚の違いを含め検証済み。文字の色には使わない）
SEQ = ["#e6effa", "#104281"]   # 量（件数・割合）は青の濃さ1色で
JUDGE = {"未確認": None, "該当": 1, "該当せず": 0}


def _colors(groups) -> alt.Scale:
    return alt.Scale(domain=[g[1] for g in groups], range=[ui.S1, ui.S2, S3][:len(groups)])


def _settings(preset_name: str, p: dict) -> dict:
    """読み込みの設定（データ・辞書・前処理・数え方）。キーは型ごとに分けて、切りかえても混ざらないようにする"""
    k = f"dy_{list(dc.PRESETS).index(preset_name)}"
    with st.expander("データと数え方を変える（自分のデータを貼る・辞書・否定のルール）"):
        st.warning("公開版（Streamlit Community Cloud）に貼った文は、アプリのサーバーで処理されます（保存はしません）。"
                   "実際の日誌や感想は、下の **ブラウザだけで動くフル版（HTML）** か、手元で `streamlit run app.py` して使ってください。", icon="⚠️")
        text = st.text_area("データ（1行目に 日付・作業・記入者・本文。タブかカンマ区切り）", p["text"], height=160, key=f"{k}_text")
        c1, c2 = st.columns(2)
        names = c1.text_area("氏名の辞書（1行に1つ）", "\n".join(p["names"]), height=90, key=f"{k}_names").split("\n")
        orgs = c2.text_area("取引先の辞書（1行に1つ）", "\n".join(p["orgs"]), height=90, key=f"{k}_orgs").split("\n")
        c3, c4, c5 = st.columns(3)
        auto = c3.checkbox("辞書にない「〇〇さん」「〇〇青果」・電話・メール・URLも置換", True, key=f"{k}_auto")
        nfkc = c4.checkbox("表記をそろえる（NFKC：全角英数→半角など）", True, key=f"{k}_nfkc")
        use_syn = c5.checkbox("言い換え（同義語）も数える", False, key=f"{k}_syn",
                              help="、".join(f"{b}：{s}" for _, b, s in p["groups"]))
        neg = st.text_input("否定・解消を示す表現（語の直後12文字、句点まで）", dc.DEF_NEG, key=f"{k}_neg")
        c6, c7 = st.columns([1, 4])
        use_ex = c6.checkbox("例外を使う", True, key=f"{k}_useex")
        ex = c7.text_input("「ない」を含むが否定ではない表現（例外）", dc.DEF_EX, key=f"{k}_ex")
    return dict(text=text, names=names, orgs=orgs, auto=auto, nfkc=nfkc, use_syn=use_syn, neg=neg, ex=ex, use_ex=use_ex, key=k)


def _judge_table(d: dict, key: str) -> dict:
    """③ 原文を読む：一致した（ID×語）ごとに、人が判定する。サンプルには判定例が入っている。返り値は判定の辞書"""
    rows, p = d["rows"], d["preset"]
    kw = {(x["ID"], x["key"]): x for x in dc.kwic(rows, p["groups"]) if x["回目"].startswith("1/")}
    inv = {v: k for k, v in JUDGE.items()}
    lab = dict(st.session_state.get(f"{key}_lab", d["labels"]))
    base = pd.DataFrame([{"ID": i, "語": x["語"], "作業": x["作業"], "前": x["前"], "一致": x["一致"], "後": x["後"],
                          "回数": int(x["回目"].split("/")[1]), "ルール": x["ルール"], "人の判定": inv[lab.get((i, k))],
                          "_k": k} for (i, k), x in kw.items()])
    if base.empty:
        st.info("一致した文がありません。キーワードや言い換えの設定を見直してください。")
        return {}
    shown = st.selectbox("表示", ["すべて", "否定の可能性あり", "未確認のみ"], key=f"{key}_flt")
    view = base if shown == "すべて" else base[base["ルール"].str.startswith("否定")] if shown == "否定の可能性あり" else base[base["人の判定"] == "未確認"]
    order = ["ID", "語", "人の判定", "ルール", "前", "一致", "後", "回数", "作業"]
    ed = st.data_editor(view[order], hide_index=True, width="stretch", height=360, key=f"{key}_ed_{shown}",
                        disabled=["ID", "語", "作業", "前", "一致", "後", "回数", "ルール"],
                        column_config={"人の判定": st.column_config.SelectboxColumn(options=list(JUDGE), required=True,
                                                                                    help=f"原文を読んで、{p['target']}かどうかを決める"),
                                       "前": st.column_config.TextColumn(width="medium"), "後": st.column_config.TextColumn(width="medium")})
    for (_, r), (_, e) in zip(view.iterrows(), ed.iterrows()):
        v = JUDGE[e["人の判定"]]
        if v is None:
            lab.pop((r["ID"], r["_k"]), None)
        else:
            lab[(r["ID"], r["_k"])] = v
    st.session_state[f"{key}_lab"] = lab
    st.caption(f"機械は「一致」まで。{p['target']}かどうかは原文を読んで人が決めます。判定はこの画面を開いている間だけ残ります"
               f"{'（サンプルには判定例が入っています）' if d['sample'] else ''}。")
    return lab


def section(farm_name: str = "") -> None:
    st.subheader("⑥ 支援先の声を読む（作業日誌・お客さんの感想の困りごと分析）")
    st.write("⑤の「1 診る」で使う道具です。支援先の作業日誌から困りごとを、定期便の感想から不満の芽を拾い、"
             "**どの作業（便）・どの時期に・どんな言葉で**書かれているかを、数えてから原文で確かめます。"
             "見つかった困りごとは、エージェントに任せられそうな仕事の候補に結びつけます（道具箱 06 任せる）。")
    preset_name = st.radio("読む文", list(dc.PRESETS), horizontal=True, key="dy_preset")
    p = dc.PRESETS[preset_name]
    cfg = _settings(preset_name, p)
    key = cfg.pop("key")
    d = dc.load(preset_name, **cfg)
    rows, groups, unit, target = d["rows"], p["groups"], p["unit"], p["target"]
    if not rows:
        st.info("データを読めませんでした。1行目に見出し（日付・作業・記入者・本文）があるか確かめてください。")
        return
    if not d["sample"] and st.session_state.get(f"{key}_src") != cfg["text"]:
        st.session_state[f"{key}_lab"] = {}          # 別のデータに貼りかえたら、判定は白紙から
    st.session_state[f"{key}_src"] = cfg["text"]
    st.caption(f"問い：{p['question']}")

    t1, t2, t3, t4, t5 = st.tabs(["1 匿名化", "2 数える", "3 原文を読む", "4 示唆", "5 確かめて報告"])
    with t3:   # 人の判定は 2・4・5 でも使うので、先に組み立てる
        labels = _judge_table(d, key)
        acc = dc.rule_accuracy(rows, groups, labels)
        if acc["n"]:
            a1, a2 = st.columns(2)
            a1.metric("例外なしのルールが人の判定と合う割合", f"{acc['例外なし'] / acc['n']:.0%}", help=f"{acc['例外なし']}/{acc['n']}")
            a2.metric("例外ありのルール", f"{acc['例外あり'] / acc['n']:.0%}", help=f"{acc['例外あり']}/{acc['n']}")
            if acc["ずれ"]:
                st.markdown("**ルールと人の判定がずれた文**（ルールの直し方と限界を考える材料）")
                st.dataframe(pd.DataFrame(acc["ずれ"]), hide_index=True, width="stretch")
            if d["sample"]:
                st.caption("例外は、この判定例を見てから作ったものです。同じデータで良く見えるのは当然なので、新しい文でも確かめるまで「改善した」とは書きません。")

    with t1:
        st.write(f"分析に使うのは、置きかえたあとの文（右の列）だけです。元の文と置換の記録（対応表）は共有しません。")
        show_raw = st.toggle("元の文も表示（共有しない列）", False, key=f"{key}_raw")
        cols = ["id", "date", "task", "writer_code"] + (["raw"] if show_raw else []) + ["anon"]
        st.dataframe(pd.DataFrame(rows)[cols].rename(columns={"id": "ID", "date": "日付", "task": p["group_col"], "writer_code": p["writer"],
                                                              "raw": "元の文", "anon": "匿名化後の文"}),
                     hide_index=True, width="stretch", height=260)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**置換の記録**（「自動」は機械が見つけた候補。誤りと取りこぼしを目で確かめる）")
            st.dataframe(pd.DataFrame(d["log"]), hide_index=True, width="stretch")
        with c2:
            res = dc.residual(rows)
            st.markdown("**まだ残っているかもしれないもの**")
            if res:
                st.dataframe(pd.DataFrame(res), hide_index=True, width="stretch")
            else:
                st.caption("機械の点検では見つかりませんでした（敬称・長い数字・郵便番号・住所・@）。見つからない＝残っていない、ではありません。")
            ch = sum(r["nfkc_changed"] for r in rows)
            st.caption(f"NFKC で変わった行：{ch}件。" + ("NFKC は丸数字や単位記号も変えます。消してよい違いかを確かめます。" if ch else ""))
        csv = pd.DataFrame(rows)[["id", "date", "task", "writer_code", "anon"]].rename(
            columns={"id": "ID", "date": "日付", "task": "作業", "writer_code": "記入者", "anon": "本文"}).to_csv(index=False)
        st.download_button("匿名化済みCSV（分析・共有に使うのはこちら）", csv.encode("utf-8-sig"), "diary_anon.csv", "text/csv", key=f"{key}_csv")

    with t2:
        basis = st.segmented_control("何を数えるか", list(dc.BASIS), default="human", format_func=lambda b: f"{dc.BASIS[b]}{unit}",
                                     key=f"{key}_basis") or "human"
        s = dc.summary(rows, groups, basis, labels)
        for col, x in zip(st.columns(len(s)), s):
            col.metric(f"「{x['語']}」", f"{x['件数']} 件 / {x['全件']}件",
                       help=f"一致 {x['一致']}件・出現 {x['出現回数']}回・否定の可能性 {x['否定の可能性']}件")
            col.caption(f"{x['割合']:.0%}　一致 {x['一致']}件・出現 {x['出現回数']}回・否定の可能性 {x['否定の可能性']}件")
        st.caption(f"1件の{unit}に2回出ても件数は1件。出現回数は別に数えます。")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**月ごとの件数（どの時期に）**")
            mo = pd.DataFrame(dc.by_month(rows, groups, basis, labels))
            long = mo.melt(id_vars=["月", "日誌数"], var_name="語", value_name="件数")
            st.altair_chart(alt.Chart(long).mark_bar(cornerRadiusEnd=4, size=12).encode(
                x=alt.X("月:N", title=None, axis=alt.Axis(labelAngle=0)), xOffset=alt.XOffset("語:N", sort=[g[1] for g in groups]),
                y=alt.Y("件数:Q", title=f"{unit}の件数", axis=alt.Axis(tickMinStep=1)),
                color=alt.Color("語:N", scale=_colors(groups), legend=alt.Legend(orient="top", title=None)),
                tooltip=["月", "語", "件数", alt.Tooltip("日誌数:Q", title=f"その月の{unit}")]).properties(height=230),
                width="stretch")
            st.caption("各月の件数：" + "・".join(f"{int(m[5:]) if m != '不明' else m}月 {n}件" for m, n in zip(mo["月"], mo["日誌数"])))
        with c2:
            rate = st.toggle("割合で見る（÷その作業の件数）", True, key=f"{key}_rate")
            st.markdown(f"**{p['group_col']} × 語（どの{p['group_col']}で）**")
            tk = pd.DataFrame(dc.by_task(rows, groups, basis, labels))
            hl = tk.melt(id_vars=["作業", "日誌数"], var_name="語", value_name="件数")
            hl["割合"] = hl["件数"] / hl["日誌数"]
            hl["表示"] = [f"{r:.0%}" if rate else str(c) if c else "·" for r, c in zip(hl["割合"], hl["件数"])]
            v = "割合:Q" if rate else "件数:Q"
            base = alt.Chart(hl).encode(y=alt.Y("作業:N", sort=list(tk["作業"]), title=None), x=alt.X("語:N", title=None, sort=[g[1] for g in groups], axis=alt.Axis(orient="top", labelAngle=0)))
            st.altair_chart((base.mark_rect(stroke="white", strokeWidth=2).encode(
                color=alt.Color(v, scale=alt.Scale(range=SEQ), legend=None),
                tooltip=["作業", "語", "件数", alt.Tooltip("日誌数:Q", title=f"その{p['group_col']}の{unit}"), alt.Tooltip("割合:Q", format=".0%")])
                + base.mark_text(fontSize=12).encode(text="表示:N", color=alt.condition(f"datum.{'割合' if rate else '件数'} > {0.55 * (hl['割合'].max() if rate else max(1, hl['件数'].max()))}",
                                                                                         alt.value("white"), alt.value("#1a1c18")))).properties(height=34 * len(tk) + 20),
                width="stretch")
        st.info(f"**件数は重要度の順位ではありません。** よく書かれる{p['group_col']}ほど件数が増えます。分母（その{p['group_col']}の{unit}の数）で割った割合と、原文の中身をあわせて読みます。")
        st.markdown(f"**1件は1人ではない**（{p['writer']}ごとの件数。偏りを確かめるためだけに使い、個人の評価には使わない）")
        st.dataframe(pd.DataFrame(dc.by_writer(rows, groups, basis, labels)), hide_index=True, width="stretch",
                     column_config={"割合": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1)})

    with t4:
        basis4 = st.session_state.get(f"{key}_basis") or "human"
        st.markdown(f"**どの{p['group_col']}で多いか（ベイズ推定）**　基準：{dc.BASIS[basis4]}{unit}")
        tb = pd.DataFrame(dc.task_bayes(rows, groups, basis4, labels))
        overall = sum(any(dc.counted(r, g[0], basis4, labels) for g in groups) for r in rows) / len(rows)
        fb = alt.Chart(tb).encode(y=alt.Y("作業:N", sort=list(tb["作業"]), title=None))
        tip = ["作業", "該当", "日誌数", alt.Tooltip("推定:Q", format=".0%"), alt.Tooltip("下:Q", format=".0%", title="90%の幅（下）"),
               alt.Tooltip("上:Q", format=".0%", title="90%の幅（上）"), alt.Tooltip("ほかより高い確率:Q", format=".0%")]
        st.altair_chart((fb.mark_rule(strokeWidth=2, color=ui.S1).encode(x=alt.X("下:Q", title=f"{target}を含む割合の推定（90%の幅）",
                                                                                 axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])), x2="上:Q", tooltip=tip)
                         + fb.mark_point(filled=True, size=90, color=ui.S1, stroke="white", strokeWidth=2, opacity=1).encode(x="推定:Q", tooltip=tip)
                         + alt.Chart(pd.DataFrame({"x": [overall]})).mark_rule(strokeDash=[4, 3], color="#52554d").encode(x="x:Q"))
                        .properties(height=30 * len(tb) + 30), width="stretch")
        st.caption(f"事前分布 Beta(1,1)。点線は全体の割合（{overall:.0%}）。件数が少ない{p['group_col']}ほど幅が広くなります。"
                   "「ほかより高い確率」は、その割合がほかの作業をまとめた割合を上回る事後確率です。")
        shown_tb = tb.copy()
        for c in ["推定", "下", "上", "ほかより高い確率"]:
            shown_tb[c] = (shown_tb[c] * 100).round().astype(int).astype(str) + "%"
        st.dataframe(shown_tb.rename(columns={"下": "90%の幅（下）", "上": "90%の幅（上）"}), hide_index=True, width="stretch")
        st.markdown("**AIエージェントに任せられそうな仕事の候補**（送信・発注・シフトの確定は人が承認。扱うのは匿名化済み・社内のデータだけ）")
        st.table(pd.DataFrame(dc.agent_ideas(rows, groups, basis4, labels)).set_index("任せられそうな仕事"))
        st.caption("どれも仮説です。表の根拠になったIDの原文を読んでから、支援先と一緒に決めます。")
        ui.link("agent", "候補の仕事を工程に分け、人の承認を置く（道具箱 06 任せる）", "🛠️")

    with t5:
        st.markdown("**生成AIの答えを確かめる（任意）**：同じ文・同じ数え方で行ごとの回数を頼み、**合計より先に内訳**を照らします。")
        word = st.selectbox("数える語", [g[1] for g in groups], key=f"{key}_aiw")
        scope = dc.ai_scope(rows, word)
        c1, c2 = st.columns(2)
        with c1:
            if d["sample"]:
                st.code(dc.ai_prompt(scope, word), language=None, wrap_lines=True)
            else:
                st.info("実際の文が読み込まれています。外部の生成AIには入力しない方針のため、依頼文は作りません（練習は架空のサンプルで）。")
            if st.button("教員作成の模擬回答を入れる", key=f"{key}_mock"):
                st.session_state[f"{key}_ans"] = dc.ai_mock(scope, word)
            ans = st.text_area("AIの最初の回答を貼る（「D002 2」のように ID と回数が1行ずつ）", key=f"{key}_ans", height=150)
        with c2:
            if ans.strip():
                c = dc.ai_compare(scope, word, ans)
                (st.success if c["一致した行"] == c["行数"] else st.error)(c["判定"])
                m1, m2, m3 = st.columns(3)
                m1.metric("行ごとの一致", f"{c['一致した行']} / {c['行数']}行")
                m2.metric("合計の回数", f"{c['合計（AI）']} / {c['合計（ページ）']}", help="AI / この画面")
                m3.metric("現れた件数", f"{c['件数（AI）']} / {c['件数（ページ）']}", help="AI / この画面")
                st.dataframe(pd.DataFrame(c["table"]), hide_index=True, width="stretch", height=220)
                st.caption("最初の回答は消さずに残し、ずれた行・直した内容・確かめた原文を追記します。サービス名・表示モデル名（なければ「不明」）・日時も記録します。")
            else:
                st.caption(f"回答を貼ると、行ごとに照らします。最初に確かめる行：{c_first(scope, word)}")
        st.markdown("**小さな分析報告（方法｜結果｜限界）の下書き**")
        st.text_area("下書き（解釈は自分で書き足す）", dc.report(rows, groups, labels, p, cfg["nfkc"], cfg["use_syn"], d["sample"]),
                     height=260, key=f"{key}_memo_{len(labels)}_{cfg['use_syn']}")
        st.markdown("**提出・共有の前に、自分で確認**")
        for i, t in enumerate(dc.REPORT_CHECKS):
            st.checkbox(t, key=f"{key}_chk{i}")

    st.markdown("**ブラウザだけで動くフル版（HTML）**：同じ手順に、語の区切り方の比較・となりの語（N-gram）・困りごとの連鎖・判定モデル（ナイーブベイズ）を加えたものです。"
                "ダウンロードしてブラウザで開くと、貼った文は外へ送られません。")
    if HTML_PATH.exists():
        st.download_button("作業日誌 困りごと分析（HTML版）をダウンロード", HTML_PATH.read_bytes(), "diary_analysis.html", "text/html", key="dy_html")


def c_first(scope, word: str) -> str:
    if not scope:
        return "—"
    r = max(scope, key=lambda r: dc.count_sub(r["anon"], word))
    return f"{r['id']}（「{word}」{dc.count_sub(r['anon'], word)}回・1件）"
