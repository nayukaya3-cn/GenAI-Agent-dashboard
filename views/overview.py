import pandas as pd
import streamlit as st

import genai_core as gc
import ui

ui.header("overview", "生成AIの利活用と、AIエージェントの適用は同じものではありません。エージェントは、生成AIを頭脳として、"
          "計画する力と道具を操作する手足を足した、いちばん発展した使い方のひとつです。")

st.subheader("役割のちがい")
st.dataframe(pd.DataFrame(gc.COMPARE, columns=["比べる点", "生成AI（単体で使う）", "AIエージェント（適用する）"]),
             hide_index=True, use_container_width=True)
st.caption("単発の作業をこなすか、一連のプロセス（調整・実行）をやりきるか、が分かれ目です。")

st.subheader("この業務は、どこから着手するか")
st.write("すべての業務をエージェントにする必要はありません。業務を1つ思いうかべ、当てはまるものに印をつけます。")
preset = st.selectbox("例から選ぶ", list(gc.DIAG_PRESET), key="diag_preset")
if st.session_state.get("_diag_loaded") != preset:
    for k in gc.DIAG_Q:
        st.session_state[f"dq_{k}"] = k in gc.DIAG_PRESET[preset]
    st.session_state["_diag_loaded"] = preset
left, right = st.columns(2)
with left:
    flags = [k for k, q in gc.DIAG_Q.items() if st.checkbox(q, key=f"dq_{k}")]
stage, why = gc.diagnose(flags)
with right:
    with st.container(border=True):
        st.caption("目安")
        st.markdown(f"### {gc.STAGES[stage - 1][0]}：{gc.STAGES[stage - 1][1]}")
        for w in why:
            st.markdown(f"- {w}")
        st.caption("判定の境目は仮置きです。現場のルールと費用で決め直してください。")

st.subheader("利活用の3つの段階")
for col, (i, s) in zip(st.columns(3), enumerate(gc.STAGES, start=1)):
    with col, st.container(border=True):
        st.caption(s[0] + ("　◀ いまの目安" if i == stage else ""))
        st.markdown(f"**{s[1]}**")
        st.write(s[2])

st.subheader("この画面の歩き方")
st.dataframe(pd.DataFrame([
    ("02 学ぶ", "仕組みの要点と、使い方への効き方を結ぶ。6冊を読む順に並べる", "本棚メモ（LLM・生成モデル・拡散モデル・原論文）"),
    ("03 聞く", "質問の型を組み立て、足りない部品を見つける", "AI伴走ページ、福祉×生成AI ②"),
    ("04 守る", "貼る前の点検と伏せ字、AIの出力と元の文の照合", "福祉×生成AI ③⑤、AI伴走ページの信号機"),
    ("05 組む", "得意と作業を組み合わせ、支援の量と転移を見る", "福祉×生成AI ①、特支ページの4枚カードと5段階"),
    ("06 任せる", "業務を工程に分け、人・生成AI・エージェントに割りふる", "役割の整理メモ、AI駆動開発のセキュリティ本の三本柱"),
    ("07 確かめる", "次に試す使い方を選び、効果を一人ひとりの記録で比べる", "AI伴走ページの記録、福祉×生成AI ⑥"),
], columns=["段", "やること", "もとになった材料"]), hide_index=True, use_container_width=True)
