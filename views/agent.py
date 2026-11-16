import pandas as pd
import streamlit as st

import genai_core as gc
import ui

ui.header("agent", "エージェントは、目的を渡すと自分で計画し、道具を使って進めます。任せる前に、工程ごとの担当・権限・承認の場所を決めます。"
          "安全は人の注意力ではなく、設計で確保します。")

st.subheader("エージェントの動き方")
st.markdown("`目的を受け取る` → `計画を立てる` → `道具を使う` → `結果を見る` ↺ 足りなければ計画へ戻る → **`人が承認する`** → `完了を報告する`")
st.caption("生成AI単体は「計画を立てる」の中身だけを担います。道具を使う・結果を見る、の輪が回るところがエージェントです。")

st.subheader("設計シート")
name = st.selectbox("業務の例", list(gc.FLOWS), key="flow_name")
df = pd.DataFrame(gc.FLOWS[name], columns=["工程", "担当", "必要な権限", "取り消せる"])
edited = st.data_editor(df, key=f"flow_{name}", num_rows="dynamic", use_container_width=True, hide_index=True, column_config={
    "工程": st.column_config.TextColumn("工程", required=True),
    "担当": st.column_config.SelectboxColumn("担当", options=gc.WHO, required=True, default="人"),
    "必要な権限": st.column_config.SelectboxColumn("必要な権限", options=gc.PERM, required=True, default="読むだけ"),
    "取り消せる": st.column_config.CheckboxColumn("取り消せる", default=True)})
flow = [(str(r["工程"]), r["担当"] or "人", r["必要な権限"] or "読むだけ", bool(r["取り消せる"]))
        for r in edited.to_dict("records") if str(r["工程"] or "").strip() and str(r["工程"]) != "None"]
stats = gc.flow_stats(flow)
icon = {"手前で人が承認": "🔴", "任せてよい": "🟢", "人が確かめて次へ": "🔵", "人が行う": "⚪"}
for i, s in enumerate(flow, start=1):
    v = gc.step_verdict(s[1], s[2], s[3])
    st.markdown(f"{i}. {s[0]}　{icon[v]} {v}")
c1, c2, c3 = st.columns(3)
c1.metric("エージェントが担う工程", f"{stats['agent']} / {stats['total']}")
c2.metric("人の承認が要る場所", sum(stats["gates"]))
c3.metric("エージェントに与える権限", "・".join(stats["perms"]) or "なし")
st.caption({3: "第3段階（エージェントの適用）の設計です。", 1: "エージェントの工程がないので、第1〜2段階の設計です。", 0: "すべて人が行う設計です。"}[stats["stage"]]
           + "「外へ送る」または「取り消せない」工程をエージェントに任せるときは、その手前に人の承認を置きます。")

left, right = st.columns(2)
with left:
    st.subheader("ガードレールの確認")
    checked = [i for i, g in enumerate(gc.GUARDS) if st.checkbox(g, key=f"guard_{i}")]
    st.progress(len(checked) / len(gc.GUARDS), text=f"{len(checked)} / {len(gc.GUARDS)}")
    st.caption("AI駆動開発のセキュリティ本にある三本柱（AIの行動統制、認証情報の動的な供給、組織の監査と統制）を下敷きにしています。")
with right:
    st.subheader("シートを持ち出す")
    sheet = gc.design_sheet(name, flow, checked)
    st.code(sheet, language=None, wrap_lines=True)
    st.download_button("シートを保存（.txt）", sheet, file_name="agent_design_sheet.txt", mime="text/plain")
