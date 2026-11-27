"""農＋X　X：ひとり情シス・コーポレートIT（生成AI＆AIエージェント活用編）。
計算とデータは corpit_core.py（Streamlit 非依存）。エージェントの判定は genai_core.py の部品を使う。
"""
import altair as alt
import pandas as pd
import streamlit as st

import corpit_core as cc
import genai_core as gc
import ui

st.caption("農＋X ／ X：ひとり情シス・コーポレートIT ／ 生成AI＆AIエージェント活用編")
st.title("ひとり情シス：小さな農業法人のコーポレートIT")
st.write(cc.CORE)
st.divider()

tabs = st.tabs(["① 5つの仕事", "② 棚卸しと任せる順", "③ ヘルプデスク", "④ ネットワーク・ロボット",
                "⑤ アカウント点検", "⑥ 不審メール", "⑦ エージェント設計", "⑧ 効果を因果で", "⑨ 注意点"])

# ------------------------------------------------------------
with tabs[0]:
    st.subheader("コーポレートITの5つの仕事 × 生成AI・エージェント")
    area = st.radio("仕事", cc.AREA_NAMES, horizontal=True, key="corpit_area",
                    format_func=lambda a: f"{next(x[1] for x in cc.AREAS if x[0] == a)} {a}")
    a = next(x for x in cc.AREAS if x[0] == area)
    rows = [("主な仕事", a[2]), ("小さな農業法人では", a[3]), ("生成AIの使いどころ", a[4]),
            ("エージェントに任せる候補", a[5]), ("人が持つ判断", a[6])]
    st.dataframe(pd.DataFrame(rows, columns=["項目", "内容"]), hide_index=True, width="stretch")
    st.subheader("一覧")
    st.dataframe(pd.DataFrame([(f"{x[1]} {x[0]}", x[4], x[5], x[6]) for x in cc.AREAS],
                              columns=["仕事", "生成AI", "エージェント", "人が持つ判断"]), hide_index=True, width="stretch")
    st.subheader("一年の段取り：農の繁忙期には変えない")
    st.dataframe(pd.DataFrame(cc.IT_YEAR, columns=["時期", "やること", "方針"]), hide_index=True, width="stretch")
    st.caption("畑の作業の山は「農：輪作と時間の予算」で見られます。IT の入れ替えは、その余白の月にまとめます。")
    ui.link("nox_rotation", "農：輪作と時間の予算で、余白の月を見る")
    with st.expander("仕事内容の整理の参考"):
        st.markdown("\n".join(f"- [{t}]({u})" for t, u in cc.SOURCES))

# ------------------------------------------------------------
with tabs[1]:
    st.subheader("業務の棚卸し → 手をつける順と任せ方")
    st.write("表を書きかえると、順と任せ方が変わります。点＝月に浮く時間 × 手順の決まり具合 ÷ 失敗の影響（仮置きの式）。")
    cols = ["業務", "分野", "月の回数", "1回の分", "手順の決まり具合", "失敗の影響", "外へ送る", "取り消せる"]
    edited = st.data_editor(pd.DataFrame(cc.INVENTORY, columns=cols), key="corpit_inv", num_rows="dynamic",
                            hide_index=True, width="stretch", column_config={
        "分野": st.column_config.SelectboxColumn("分野", options=cc.AREA_NAMES, required=True, default=cc.AREA_NAMES[0]),
        "月の回数": st.column_config.NumberColumn("月の回数", min_value=0, default=1),
        "1回の分": st.column_config.NumberColumn("1回の分", min_value=0, default=10),
        "手順の決まり具合": st.column_config.NumberColumn("手順の決まり具合（1〜3）", min_value=1, max_value=3, default=2),
        "失敗の影響": st.column_config.NumberColumn("失敗の影響（1〜3）", min_value=1, max_value=3, default=2),
        "外へ送る": st.column_config.CheckboxColumn("外へ送る", default=False),
        "取り消せる": st.column_config.CheckboxColumn("取り消せる", default=True)})
    recs = []
    for r in edited.to_dict("records"):
        if str(r["業務"] or "").strip() and str(r["業務"]) != "None":
            recs.append((r["業務"], r["分野"] or cc.AREA_NAMES[0], r["月の回数"] or 0, r["1回の分"] or 0,
                         int(r["手順の決まり具合"] or 2), int(r["失敗の影響"] or 2), bool(r["外へ送る"]), bool(r["取り消せる"])))
    rank = cc.automation_rank(recs)
    st.dataframe(pd.DataFrame(rank)[["順", "業務", "分野", "月の時間", "点", "任せ方"]] if rank else pd.DataFrame(),
                 hide_index=True, width="stretch")
    if rank:
        c1, c2 = st.columns(2)
        c1.metric("棚卸しした業務の時間（月）", f"{sum(d['月の時間'] for d in rank):.1f} 時間")
        c2.metric("エージェントの候補", f"{sum(d['任せ方'].startswith('エージェント') for d in rank)} 件")
    st.caption("手順の決まり具合 1＝毎回ちがう、3＝毎回同じ。失敗の影響 1＝やり直せば済む、3＝お金・信用・個人情報に関わる。"
               "外へ送る・取り消せない・影響が大きい業務は、エージェントに任せても手前で人が承認します。")

# ------------------------------------------------------------
with tabs[2]:
    st.subheader("一次回答の質問文をつくる")
    st.write("この画面は生成AIを呼び出しません。組み立てた文を、法人で使ってよい生成AIに自分で貼ります。")
    c1, c2 = st.columns(2)
    with c1:
        key = st.selectbox("社内FAQ", list(cc.FAQ), key="corpit_faq")
        q = st.text_area("問い合わせ（名前・電話番号などは消してから）", "ハウスのタブレットで、朝から作業記録アプリが開けません", key="corpit_q")
        furi = st.checkbox("ふりがなをつける（実習生・はじめての人向け）", key="corpit_furi")
    with c2:
        try:
            st.code(cc.helpdesk_prompt(q, key, furigana=furi), language=None, wrap_lines=True)
        except ValueError as e:
            st.warning(str(e))
    chk = gc.scan(q)
    if chk["found"] or chk["injection"]:
        st.warning(f"貼る前の点検：{ui.LIGHT_ICON[chk['level']]} " + "／".join(sorted({f[1] for f in chk["found"]} | set(chk["injection"]))), icon="⚠️")

    st.subheader("どの回答の型が「自分で解決できた」につながるか（強化学習：トンプソン抽出）")
    st.write("回答の型ごとに「自分で解決できた／担当が出向いた」を数えます。見込みをベータ分布から引いて一番よいものを選ぶ、を繰り返すと、"
             "よさそうな型を多めに使いながら、まだ数の少ない型も試せます（探索と活用）。")
    tdf = st.data_editor(pd.DataFrame(cc.ANSWER_TYPES, columns=["回答の型", "自分で解決できた", "担当が出向いた"]),
                         key="corpit_bandit", num_rows="dynamic", hide_index=True, width="stretch")
    rows = [(r["回答の型"], r["自分で解決できた"] or 0, r["担当が出向いた"] or 0) for r in tdf.to_dict("records")
            if str(r["回答の型"] or "").strip() and str(r["回答の型"]) != "None"]
    probs = gc.pick_probs(rows)
    if probs:
        view = pd.DataFrame([{"回答の型": n, "次に選ばれる割合": probs[n], "自己解決の見込み": gc.beta_stats(g, b)[0],
                              "80%の幅": "{:.0%}〜{:.0%}".format(*gc.beta_stats(g, b)[1:])} for n, g, b in rows])
        st.dataframe(view, hide_index=True, width="stretch", column_config={
            "次に選ばれる割合": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
            "自己解決の見込み": st.column_config.NumberColumn(format="percent")})
        st.caption("数が少ない型は幅が広く、ときどき選ばれます。数が増えると、よい型に寄っていきます。")

# ------------------------------------------------------------
with tabs[3]:
    st.subheader("ネットワークの区画分け")
    st.write("事務・現場の端末・ハウスのIoTとロボット・直売所と来客・防犯カメラを、同じ回線でも区画（VLAN・別SSID）に分けます。"
             "1か所が破られても、ほかへ広がりにくくするためです。")
    st.dataframe(pd.DataFrame(cc.SEGMENTS, columns=["区画", "つながるもの", "守り方"]), hide_index=True, width="stretch")
    st.subheader("ROS 2 のロボットをつなぐときの4点")
    st.dataframe(pd.DataFrame(cc.ROS2_TIPS, columns=["やること", "中身"]), hide_index=True, width="stretch")
    st.code("# 例：ハウスの搬送ロボット用（値は法人で決める）\nexport ROS_DOMAIN_ID=42\nexport ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET\n"
            "# SROS2：鍵の置き場を作り、ノードごとに鍵を発行して、暗号化を必須にする\n"
            "ros2 security create_keystore ~/sros2_keystore\nros2 security create_enclave ~/sros2_keystore /farm/transport_robot\n"
            "export ROS_SECURITY_KEYSTORE=~/sros2_keystore\nexport ROS_SECURITY_ENABLE=true\nexport ROS_SECURITY_STRATEGY=Enforce\n"
            "# 起動時に鍵を指定：ros2 run <パッケージ> <ノード> --ros-args --enclave /farm/transport_robot",
            language="bash")
    st.caption("ROS_AUTOMATIC_DISCOVERY_RANGE は ROS 2 Iron 以降の設定です。使う版の公式ドキュメントで確かめてください。"
               "設定変更は「② 棚卸し」で人が行う業務に置いています。生成AIは手順の下書きと、ログの要約まで。")

# ------------------------------------------------------------
with tabs[4]:
    st.subheader("アカウントと権限の点検（棚卸し）")
    st.write("在籍名簿と各サービスのアカウントを突き合わせます。季節雇用・職場体験実習の「終了」を見落とさないことが要点です。人は仮名・記号で入れてください。")
    acols = ["人", "状態", "サービス", "権限", "二段階認証", "共有アカウント", "使っていない日数"]
    adf = st.data_editor(pd.DataFrame(cc.ACCOUNTS, columns=acols), key="corpit_acc", num_rows="dynamic", hide_index=True,
                         width="stretch", column_config={
        "状態": st.column_config.SelectboxColumn("状態", options=cc.STATUS, required=True, default="在籍"),
        "権限": st.column_config.SelectboxColumn("権限", options=cc.ROLES, required=True, default="一般"),
        "二段階認証": st.column_config.CheckboxColumn(default=False),
        "共有アカウント": st.column_config.CheckboxColumn(default=False),
        "使っていない日数": st.column_config.NumberColumn(min_value=0, default=0)})
    c1, c2 = st.columns(2)
    idle = c1.slider("使っていないとみなす日数", 30, 180, 90, step=10, key="corpit_idle")
    max_admin = c2.slider("1サービスの管理者の目安（人）", 1, 4, 2, key="corpit_admin")
    arows = [(r["人"], r["状態"] or "在籍", r["サービス"], r["権限"] or "一般", bool(r["二段階認証"]), bool(r["共有アカウント"]),
              r["使っていない日数"] or 0) for r in adf.to_dict("records") if str(r["人"] or "").strip() and str(r["人"]) != "None"]
    finds = cc.account_findings(arows, idle_days=idle, max_admin=max_admin)
    m1, m2 = st.columns(2)
    m1.metric("🔴 すぐ止める・直す", sum(f["重さ"] == "赤" for f in finds))
    m2.metric("🟡 確かめて決める", sum(f["重さ"] == "黄" for f in finds))
    if finds:
        st.dataframe(pd.DataFrame([{**f, "重さ": cc.SEVERITY[f["重さ"]]} for f in finds]), hide_index=True, width="stretch")
    else:
        st.success("この表の範囲では、指摘はありません。表にないサービス・アカウントは点検できていません。")
    st.caption("突き合わせはエージェントに任せられます（読むだけ）。停止・権限の変更は、⑦ の設計どおり人の承認のあとに行います。")

# ------------------------------------------------------------
with tabs[5]:
    st.subheader("不審メールの一次点検（ベイズ）")
    st.write("「外から届くメールのうち詐欺の割合」の見込みから始め、手がかりが1つ見つかるたびに、その尤度比（詐欺メールで見られやすい倍率）を掛けて見込みを更新します。"
             "農業法人では、資材・飼料の取引先をかたる「振込先の変更」が特に危険です。")
    mail = st.text_area("メールの本文（件名も）", cc.SAMPLE_MAIL, height=170, key="corpit_mail")
    auto = cc.mail_clues(mail)
    manual_labels = [c[0] for c in cc.CLUES if c[2] is None]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**本文から見つかった手がかり**")
        st.write("\n".join(f"- {x}" for x in auto) or "なし")
        st.markdown("**人が見て印をつける手がかり**")
        manual = [lab for i, lab in enumerate(manual_labels) if st.checkbox(lab, key=f"corpit_clue_{i}")]
        prior = st.slider("事前の見込み（詐欺の割合）", 0.01, 0.30, cc.PRIOR_DEFAULT, step=0.01, key="corpit_prior", format="%.2f")
    res = cc.phishing_posterior(auto + manual, prior=prior)
    with c2, st.container(border=True):
        st.metric("詐欺の見込み（事後）", f"{res['確率']:.0%}")
        st.markdown(f"{ui.LIGHT_ICON[res['色']]} {cc.MAIL_ACTION[res['色']]}")
        steps = [("はじめ", prior)]
        o = prior / (1 - prior)
        for lab, lr in res["手がかり"]:
            o *= lr
            steps.append((lab, o / (1 + o)))
        chart = alt.Chart(pd.DataFrame([{"段": i, "手がかり": s[0], "見込み": s[1]} for i, s in enumerate(steps)])).mark_line(
            point=True, color=ui.S2).encode(x=alt.X("段:O", title="手がかりを足した順"),
                                            y=alt.Y("見込み:Q", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
                                            tooltip=["手がかり", alt.Tooltip("見込み:Q", format=".0%")])
        st.altair_chart(chart.properties(height=200), width="stretch")
    st.caption("尤度比は仮置きで、手がかりどうしは独立と仮定しています（実際は重なるので、見込みは高めに出ます）。判定は人が行います。")

    st.subheader("生成AIに貼る一次点検の質問文（伏せ字ずみ）")
    sc = gc.scan(mail)
    if sc["injection"]:
        st.error("本文の中に、AIへの指示がまぎれこんでいます：" + "／".join(sc["injection"])
                 + "。エージェントにメールを読ませるときは、この文に従わない設計にします。", icon="🚨")
    st.code(cc.triage_prompt(sc["masked"], auto + manual), language=None, wrap_lines=True)

# ------------------------------------------------------------
with tabs[6]:
    st.subheader("エージェントの設計シート（ひとり情シス版）")
    st.write("工程ごとに担当・権限・取り消せるかを決めます。判定のしかたは「06 任せる」と同じです。")
    name = st.selectbox("業務の例", list(cc.FLOWS), key="corpit_flow_name")
    fdf = st.data_editor(pd.DataFrame(cc.FLOWS[name], columns=["工程", "担当", "必要な権限", "取り消せる"]), key=f"corpit_flow_{name}",
                         num_rows="dynamic", hide_index=True, width="stretch", column_config={
        "担当": st.column_config.SelectboxColumn("担当", options=gc.WHO, required=True, default="人"),
        "必要な権限": st.column_config.SelectboxColumn("必要な権限", options=gc.PERM, required=True, default="読むだけ"),
        "取り消せる": st.column_config.CheckboxColumn("取り消せる", default=True)})
    flow = [(str(r["工程"]), r["担当"] or "人", r["必要な権限"] or "読むだけ", bool(r["取り消せる"]))
            for r in fdf.to_dict("records") if str(r["工程"] or "").strip() and str(r["工程"]) != "None"]
    icon = {"手前で人が承認": "🔴", "任せてよい": "🟢", "人が確かめて次へ": "🔵", "人が行う": "⚪"}
    for i, s in enumerate(flow, start=1):
        v = gc.step_verdict(s[1], s[2], s[3])
        st.markdown(f"{i}. {s[0]}　{icon[v]} {v}")
    stats = gc.flow_stats(flow)
    c1, c2 = st.columns(2)
    c1.metric("エージェントが担う工程", f"{stats['agent']} / {stats['total']}")
    c2.metric("人の承認が要る場所", sum(stats["gates"]))
    checked = [i for i, g in enumerate(gc.GUARDS) if st.checkbox(g, key=f"corpit_guard_{i}")]
    sheet = gc.design_sheet(name, flow, checked)
    st.download_button("シートを保存（.txt）", sheet, file_name="corpit_agent_sheet.txt", mime="text/plain")
    ui.link("agent", "06 任せる：エージェントの設計シートの考え方を見る")

# ------------------------------------------------------------
with tabs[7]:
    st.subheader("生成AIの導入は効いたか：差の差（因果推論）")
    st.write("「導入前より速くなった」だけでは、繁忙期が終わった・慣れた、などの影響と区別できません。"
             "導入した側（事務所）の変化から、導入していない側（直売所）の同じ時期の変化を引きます。")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**導入した側：問い合わせ1件の対応時間（分）**")
        tb = st.number_input("導入前", 0.0, 120.0, 12.0, key="corpit_tb")
        ta = st.number_input("導入後", 0.0, 120.0, 7.0, key="corpit_ta")
    with c2:
        st.markdown("**導入していない側（同じ時期）**")
        cb = st.number_input("前", 0.0, 120.0, 11.0, key="corpit_cb")
        ca = st.number_input("後", 0.0, 120.0, 9.0, key="corpit_ca")
    d = cc.did(tb, ta, cb, ca)
    m1, m2, m3 = st.columns(3)
    m1.metric("前後の差（見かけ）", f"{d['前後の差']:+.1f} 分")
    m2.metric("共通の動き", f"{d['共通の動き']:+.1f} 分")
    m3.metric("効果（差の差）", f"{d['効果（差の差）']:+.1f} 分")
    st.caption("前提：導入しなかったら、両方は同じように動いていた（平行トレンド）。導入前の何か月かで、両方が同じように動いていたかを先に確かめます。")
    st.subheader("まぎれこむもの（交絡）と手立て")
    st.dataframe(pd.DataFrame(cc.CONFOUNDERS, columns=["まぎれこむもの", "どう効くか", "手立て"]), hide_index=True, width="stretch")
    ui.link("measure", "07 確かめる：ベイズ・ABAB・公平な比較を見る")

# ------------------------------------------------------------
with tabs[8]:
    st.subheader("注意点")
    st.dataframe(pd.DataFrame(cc.CAUTIONS, columns=["項目", "注意すること"]), hide_index=True, width="stretch")
    ui.link("guard", "04 守る：AIに貼る前の点検と伏せ字")

ui.contact()
