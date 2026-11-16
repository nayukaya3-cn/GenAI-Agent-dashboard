"""
仮想研究事例：「使う」と「任せる」の境界設計による小規模農業法人のレジリエンス経営

一本の流れ：A どこが困っているか → B どう割り当てるか → C 本当に効いたか → D ショックに耐えるか
  A 作業日誌の辞書ベース分析（否定の除外、3類型、共起、委任マップ）
  B 作業×人の割当（全探索・貪欲法）と、天候が確率的に変わる週次計画（固定計画・貪欲法・動的計画法・Q学習）
  C 複数法人の ABAB 記録（重なりのない割合・NAP、交絡の調整、階層ベイズ）
  D ショック下のシミュレーション（委任水準 × ガードレール → 回復日数・累積損失）

方針
  - データはすべて架空（このファイルの make_data() が乱数から生成）。実在の法人・人・日誌とは無関係。
  - 辞書・境目・係数はすべて仮置き。結論は仮定に依存する。現場ヒアリングで決め直す。
  - 生成AIを呼び出さない。外へ何も送らない。
  - ダミーなので「生成時の正解」が分かる。分析手順が正解をどこまで取り戻せるかを確かめる練習台として使う。

Streamlit に依存しない。`python agri_case.py` で自己チェック、`python agri_case.py --make-data` でCSVを作り直す。
"""
from __future__ import annotations

import itertools
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

import genai_core as gc

DATA = Path(__file__).resolve().parent / "data" / "agri_case"
SEED = 20261117
FILES = ["farms", "tasks", "skills", "diary", "abab", "shocks"]

# ============================================================
# ダミーデータの設計（すべて架空）
# ============================================================
# (法人, 主な作目, 人数, 繁忙月)
FARMS = [("法人ア", "露地野菜", 6, (6, 7)), ("法人イ", "果樹（柿）", 4, (9,)), ("法人ウ", "水稲＋麦", 5, (5, 6)),
         ("法人エ", "施設トマト", 7, (7, 8)), ("法人オ", "露地野菜＋直売", 3, (6, 9))]
# (作業, 区分, 場所, 外へ出る操作を含む, 負担[体力, 細かさ, 手順の数, 判断, 危険], 生成時の類型の割合[情報不足, 判断, 身体作業])
TASKS = [
    ("耕うん・うね立て", "屋外作業", "屋外", False, (3, 1, 2, 1, 2), (.10, .15, .75)),
    ("定植・播種", "屋外作業", "屋外", False, (2, 2, 3, 1, 0), (.20, .20, .60)),
    ("防除（薬剤散布）", "屋外作業", "屋外", False, (2, 2, 3, 3, 3), (.25, .40, .35)),
    ("収穫", "屋外作業", "屋外", False, (3, 2, 2, 2, 1), (.10, .25, .65)),
    ("選果・調製", "屋内作業", "屋内", False, (1, 3, 3, 2, 0), (.20, .35, .45)),
    ("出荷伝票の作成", "事務作業", "屋内", True, (0, 3, 3, 1, 0), (.70, .25, .05)),
    ("受注確認と返信", "事務作業", "屋内", True, (0, 2, 3, 2, 0), (.50, .45, .05)),
    ("作業日誌の週報づくり", "事務作業", "屋内", False, (0, 2, 3, 1, 0), (.75, .20, .05)),
    ("資材の在庫確認と発注", "事務作業", "屋内", True, (0, 2, 4, 2, 0), (.40, .55, .05)),
    ("栽培計画の見直し", "事務作業", "屋内", False, (0, 2, 3, 3, 0), (.25, .70, .05)),
]
# 法人アの技能マップ (仮名, できる範囲[同じ並び], 好きな場所)
SKILLS = [("W1", (3, 2, 3, 2, 3), "屋外"), ("W2", (3, 1, 2, 1, 2), "屋外"), ("W3", (2, 3, 3, 2, 1), "屋内"),
          ("W4", (1, 3, 4, 2, 0), "屋内"), ("W5", (0, 2, 4, 3, 0), "屋内"), ("W6", (2, 2, 3, 3, 1), "どちらも")]
TYPES = ["情報不足型", "判断型", "身体作業型"]
TEMPLATES = {
    "情報不足型": ["出荷先の数量が分からず、確認待ちで作業が遅れた。", "希釈倍率を調べ直すのに時間がかかった。",
              "前日の引き継ぎがなく、手順が分からなかった。", "資材の置き場所が分からず探した。",
              "注文の内容を聞き直した。伝票の作成に遅れ。", "記録が見つからず、前回の散布日を確認できなかった。"],
    "判断型": ["雨予報で収穫を前倒しするか迷った。", "等級の判断に時間がかかり、選果が遅れた。",
            "人手が足りない中で、どの作業を優先するか決め直した。", "防除のタイミングの判断が難しかった。",
            "発注量を決めきれず、相談した。", "出荷を明日に回すか判断がつかなかった。"],
    "身体作業型": ["トラクターが故障し、作業を中断した。", "選果機のベルトが故障。修理待ち。", "収穫の人手が足りず、残業になった。",
              "暑さで午後の作業を止めた。作業に遅れ。", "腰に負担がかかり、ペースが落ちた。", "運搬車の故障で搬出が遅れた。"],
}
VAGUE = ["段取りが悪く遅れた。", "いつもより時間がかかった。", "思ったより進まなかった。"]   # 辞書に手がかりのない書き方（見落としの練習）
NORMAL = ["予定どおり終了。", "特になし。", "遅れなし。順調。", "機械の故障はなかった。", "人手は足りた。", "天気がよく作業が進んだ。", "午前で終了。"]
# ABAB の生成時の真値（対数尺度。−0.22 は事務作業時間が約20%減ることに当たる）
TRUE = {"mu": -0.22, "tau": 0.06, "busy": 0.30, "rain": 0.04, "noise": 0.08}
ABAB_BASE = [420, 300, 360, 480, 240]   # 法人ごとの事務作業時間（分／週）の基準
ABAB_BUSY = [(5, 6, 7, 8, 13, 14), (13, 14, 15, 16), (6, 7, 8, 9), (1, 2, 3, 4), (7, 8, 15, 16)]   # 繁忙期の週（導入期Bと重なる法人が多い＝交絡）
PHASES = ["A1"] * 4 + ["B1"] * 4 + ["A2"] * 4 + ["B2"] * 4
# (シナリオ, 開始日, 期間[日], 作業能力の低下率, 追加費用／日)
SHOCKS = [("豪雨", 30, 10, 0.50, 0.0), ("人手不足（欠員）", 30, 21, 0.30, 0.0), ("機械故障", 30, 7, 0.60, 0.0), ("資材高騰", 30, 45, 0.0, 0.15)]


def make_data(out: Path | None = None, seed: int = SEED) -> dict[str, pd.DataFrame]:
    """ダミーデータを乱数から作る。out を渡すと CSV に書き出す。seed が同じなら毎回同じ中身。"""
    rng = np.random.default_rng(seed)
    farms = pd.DataFrame([(f, c, n, "・".join(f"{m}月" for m in b)) for f, c, n, b in FARMS], columns=["法人", "主な作目", "人数", "繁忙月"])
    tasks = pd.DataFrame([(t, k, p, x, *ld) for t, k, p, x, ld, _ in TASKS], columns=["作業", "区分", "場所", "外へ出る操作", *gc.LOAD])
    skills = pd.DataFrame([(n, *lv, p) for n, lv, p in SKILLS], columns=["人", *gc.LOAD, "好きな場所"])

    rows = []
    days = [d for d in pd.date_range("2026-04-06", periods=26 * 7) if d.dayofweek < 6]   # 26週、月〜土
    task_p = np.array([.10, .08, .08, .16, .14, .10, .10, .08, .08, .08])
    for farm, _, n, busy in FARMS:
        for d in days:
            for w in range(1, n + 1):
                if rng.random() > 0.6:
                    continue
                j = int(rng.choice(len(TASKS), p=task_p))
                if rng.random() < 0.20 * (1.8 if d.month in busy else 1.0):
                    kind = TYPES[int(rng.choice(3, p=TASKS[j][5]))]
                    text = str(rng.choice(VAGUE)) if rng.random() < 0.15 else str(rng.choice(TEMPLATES[kind]))
                else:
                    kind, text = "", str(rng.choice(NORMAL))
                rows.append((farm, d.date().isoformat(), f"W{w}", TASKS[j][0], text, kind))
    diary = pd.DataFrame(rows, columns=["法人", "日付", "記入者", "作業", "本文", "生成時の類型"])

    rows = []
    for i, (farm, *_ ) in enumerate(FARMS):
        beta = rng.normal(TRUE["mu"], TRUE["tau"])
        for wk, ph in enumerate(PHASES, start=1):
            b, busy, rain = float(ph[0] == "B"), float(wk in ABAB_BUSY[i]), int(rng.binomial(6, 0.3))
            minutes = np.exp(np.log(ABAB_BASE[i]) + beta * b + TRUE["busy"] * busy + TRUE["rain"] * rain + rng.normal(0, TRUE["noise"]))
            delays = rng.poisson(np.exp(np.log(3) + 0.5 * busy + 0.1 * rain - 0.35 * b))
            rows.append((farm, wk, ph, int(busy), rain, int(round(minutes)), int(delays)))
    abab = pd.DataFrame(rows, columns=["法人", "週", "期", "繁忙期", "雨の日数", "事務作業時間_分", "遅延件数"])
    shocks = pd.DataFrame(SHOCKS, columns=["シナリオ", "開始日", "期間_日", "能力の低下率", "追加費用_日"])

    data = {"farms": farms, "tasks": tasks, "skills": skills, "diary": diary, "abab": abab, "shocks": shocks}
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        for k, df in data.items():
            df.to_csv(out / f"{k}.csv", index=False, encoding="utf-8")
    return data


def load(path: Path = DATA) -> dict[str, pd.DataFrame]:
    """data/agri_case/ の CSV を読みこむ（空欄は空文字のまま）"""
    return {k: pd.read_csv(path / f"{k}.csv", keep_default_na=False) for k in FILES}


# ============================================================
# A どこが困っているか：作業日誌の辞書ベース分析
# ============================================================
KEYWORDS = ["遅れ", "故障", "人手"]
NEG = re.compile(r"(遅れ|故障|人手)(?:は|も|が)?(?:なし|なかった|ない|足りた|足りている|十分)")   # 「遅れなし」「人手は足りた」
CUES = {
    "情報不足型": ["分から", "調べ直", "聞き直", "確認待ち", "見つからず", "引き継ぎ", "探した", "確認できなかった"],
    "判断型": ["迷った", "判断", "優先", "決め直", "決めきれず", "相談"],
    "身体作業型": ["故障", "修理", "残業", "暑さ", "腰", "負担", "中断"],
}
RECS = ["生成AIを使う（人が仕上げる）", "承認付きでエージェントに任せる", "任せない（人・機械の対策）", "データ不足"]


def strip_neg(text: str) -> str:
    return NEG.sub("", gc._nf(text))


def keyword_table(diary: pd.DataFrame) -> pd.DataFrame:
    """語ごとに、出現回数／その語を含む日誌数／否定を除いた日誌数。回数と日誌数は別のもの。"""
    raw, clean = diary["本文"].map(gc._nf), diary["本文"].map(strip_neg)
    return pd.DataFrame([{"語": k, "出現回数": int(raw.str.count(k).sum()), "含む日誌数": int(raw.str.contains(k).sum()),
                          "否定を除いた日誌数": int(clean.str.contains(k).sum())} for k in KEYWORDS])


def classify(text: str) -> str:
    """日誌1件を 3類型／未分類（困りごとの語はあるが手がかりなし）／""（困りごとなし）に分ける。同点は先の類型。"""
    t = strip_neg(text)
    score = [sum(c in t for c in CUES[k]) for k in TYPES]
    if max(score) > 0:
        return TYPES[int(np.argmax(score))]
    return "未分類" if any(k in t for k in KEYWORDS) else ""


def classified(diary: pd.DataFrame) -> pd.DataFrame:
    d = diary.copy()
    d["類型"] = d["本文"].map(classify)
    d["月"] = pd.to_datetime(d["日付"]).dt.month
    return d


def dictionary_check(d: pd.DataFrame) -> dict:
    """ダミーだから出来る確認：生成時の類型と、辞書の判定を突き合わせる"""
    trouble = d[d["生成時の類型"] != ""]
    hit = trouble[trouble["類型"].isin(TYPES)]
    return {"困りごとの日誌": len(trouble), "辞書が拾った": len(hit), "未分類": int((trouble["類型"] == "未分類").sum()),
            "見落とし": int((trouble["類型"] == "").sum()), "拾った中の一致率": float((hit["類型"] == hit["生成時の類型"]).mean()),
            "誤って拾った": int(((d["生成時の類型"] == "") & (d["類型"] != "")).sum())}


def cooccurrence(d: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """同じ日誌に一緒に出た語の組（否定を除いた後）"""
    terms = sorted({c for v in CUES.values() for c in v} | set(KEYWORDS))
    cnt: Counter = Counter()
    for t in d["本文"].map(strip_neg):
        cnt.update(itertools.combinations([w for w in terms if w in t], 2))
    return pd.DataFrame([{"語の組": f"{a} × {b}", "日誌数": n} for (a, b), n in cnt.most_common(top)])


def delegation_map(d: pd.DataFrame, tasks: pd.DataFrame, min_n: int = 5) -> pd.DataFrame:
    """作業ごとの類型の割合から、使う／承認付きで任せる／任せない の目安を出す（境目は仮置き）"""
    rows = []
    for _, t in tasks.iterrows():
        c = d[(d["作業"] == t["作業"]) & d["類型"].isin(TYPES)]["類型"].value_counts()
        n = int(c.sum())
        share = [float(c.get(k, 0) / n) if n else 0.0 for k in TYPES]
        if n < min_n:
            rec = RECS[3]
        elif share[2] >= 0.5:
            rec = RECS[2]
        else:
            rec = RECS[1] if share[1] > share[0] else RECS[0]
        gate = "送信・発注の手前で人が承認" if (rec == RECS[1] and bool(t["外へ出る操作"])) else ""
        rows.append({"作業": t["作業"], "区分": t["区分"], "困りごと": n, **dict(zip(TYPES, share)), "目安": rec, "承認の場所": gate})
    return pd.DataFrame(rows)


def admin_shares(dmap: pd.DataFrame) -> tuple[float, float]:
    """事務作業のうち、AIを使える作業の割合／エージェントに任せられる作業の割合（作業数で数える粗い目安）"""
    adm = dmap[dmap["区分"] == "事務作業"]
    return float(adm["目安"].isin(RECS[:2]).mean()), float((adm["目安"] == RECS[1]).mean())


# ============================================================
# B どう割り当てるか：作業×人、天候が変わる1週間の計画
# ============================================================
def assignment(skills: pd.DataFrame, tasks: pd.DataFrame) -> dict:
    """作業×人の合う度合い（genai_core の点数）と、全探索・貪欲法の割当"""
    people = [(r["人"], tuple(int(r[k]) for k in gc.LOAD), r["好きな場所"]) for _, r in skills.iterrows()]
    tk = [(r["作業"], r["場所"], tuple(int(r[k]) for k in gc.LOAD)) for _, r in tasks.iterrows()]
    m = gc.fit_matrix((), people, tk)
    best, best_s = gc.best_assignment(m)
    greedy, greedy_s = gc.greedy_assignment(m)
    return {"people": [p[0] for p in people], "tasks": [t[0] for t in tk], "matrix": m,
            "best": best, "best_score": best_s, "greedy": greedy, "greedy_score": greedy_s}


DAYS, CAP = 6, 12                 # 6日、1日の作業量は12単位（1単位＝2人時）
DEMAND = (36, 20, 14)             # 週のはじめの残り（屋外・屋内・事務）
WEIGHT = (3, 2, 1)                # 週末に残った1単位あたりの損失（屋外は収穫の遅れなので重い）
A_MAX = DEMAND[2] + 6             # 手戻りで事務が増える上限
MID_DAY, MID_LEFT, MID_PEN = 2, 7, 2   # 3日目の終わりが出荷伝票の締め：事務の残りが7単位を超えた分に、1単位あたり2の損失
PATTERNS = [(12, 0, 0), (8, 4, 0), (8, 2, 2), (6, 4, 2), (4, 4, 4), (0, 8, 4), (0, 6, 6)]   # 1日の配分（屋外, 屋内, 事務）
MODES = ["人のみ", "生成AIを使う", "エージェント（承認付き）", "エージェント（承認なし）"]


def week_params(share_use: float, share_agent: float) -> dict:
    """A の結果を B の前提にする。係数は仮置き：生成AIで事務が最大1.5倍、エージェントは1日最大6単位"""
    return {"gen": 1 + 0.5 * share_use, "agent": int(round(6 * share_agent))}


def _actions(constrained: bool = True) -> list[tuple[int, int]]:
    return [(p, m) for p in range(len(PATTERNS)) for m in range(3 if constrained else 4)]


def _effect(action: tuple[int, int], prm: dict) -> tuple[int, int, int, float, int]:
    """行動 → (屋外の進み, 屋内の進み, 事務の進み, 手戻りの確率, 手戻りの量)"""
    (po, pi, pa), mode = PATTERNS[action[0]], action[1]
    if mode == 0:
        return po, pi, pa, 0.0, 0
    if mode == 1:
        return po, pi, int(round(pa * prm["gen"])), 0.0, 0
    if mode == 2:                 # 承認に人の1単位を使う（いちばん多い配分から引く）
        v = [po, pi, pa]
        v[int(np.argmax(v))] -= 1
        return v[0], v[1], int(round(v[2] * prm["gen"])) + prm["agent"], 0.03, 2
    return po, pi, int(round(pa * prm["gen"])) + prm["agent"], 0.10, 2   # 承認を省くと人手は浮くが、手戻りが増える。外への誤送信の害はこの損失に入っていない


def _step(s: tuple[int, int, int], eff: tuple, rain: bool, err: bool) -> tuple[int, int, int]:
    o, i, a = s
    return (max(o - (0 if rain else eff[0]), 0), max(i - eff[1], 0), min(max(a - eff[2], 0) + (eff[4] if err else 0), A_MAX))


def _loss(s: tuple[int, int, int]) -> int:
    return sum(w * x for w, x in zip(WEIGHT, s))


def _mid(d: int, s: tuple[int, int, int]) -> int:
    """週の途中の締めに間に合わなかった分の損失"""
    return MID_PEN * max(s[2] - MID_LEFT, 0) if d == MID_DAY else 0


def solve_week(rain_p: float, prm: dict, constrained: bool = True) -> dict:
    """動的計画法（後ろ向き）。天候の確率が分かっているときの、期待損失が最小の方策と、その期待損失。"""
    acts = _actions(constrained)
    effs = [_effect(a, prm) for a in acts]
    og, ig, ag = np.arange(DEMAND[0] + 1), np.arange(DEMAND[1] + 1), np.arange(A_MAX + 1)
    v_next = -(WEIGHT[0] * og[:, None, None] + WEIGHT[1] * ig[None, :, None] + WEIGHT[2] * ag[None, None, :]).astype(float)
    v_next = np.stack([v_next, v_next])                  # [天候]
    policy = np.zeros((DAYS, 2, len(og), len(ig), len(ag)), dtype=np.int16)
    for d in reversed(range(DAYS)):
        ev = (1 - rain_p) * v_next[0] + rain_p * v_next[1]   # 翌朝の天候についての期待値
        v_now = np.empty_like(v_next)
        for w in (0, 1):
            q = np.empty((len(acts),) + ev.shape)
            for k, (po, pi, pa, pe, rw) in enumerate(effs):
                o2, i2, a2 = np.maximum(og - (0 if w else po), 0), np.maximum(ig - pi, 0), np.maximum(ag - pa, 0)
                a3 = np.minimum(a2 + rw, A_MAX)
                mid = (lambda a: MID_PEN * np.maximum(a - MID_LEFT, 0)[None, None, :]) if d == MID_DAY else (lambda a: 0.0)
                q[k] = (1 - pe) * (ev[np.ix_(o2, i2, a2)] - mid(a2)) + pe * (ev[np.ix_(o2, i2, a3)] - mid(a3))
            policy[d, w] = q.argmax(axis=0)
            v_now[w] = q.max(axis=0)
        v_next = v_now
    start = ((1 - rain_p) * v_next[0] + rain_p * v_next[1])[DEMAND]
    return {"policy": policy, "acts": acts, "effs": effs, "expected_loss": float(-start)}


def simulate_week(choose, acts: list, effs: list, rain_p: float, n: int = 2000, seed: int = 0) -> dict:
    """choose(日, 雨か, 残り) → 行動の番号。n 週ぶん回して、損失の平均・事務での担当の割合・承認なしの回数を返す"""
    rng = np.random.default_rng(seed)
    u = rng.random((n, DAYS, 2))
    losses, modes, viol = np.empty(n), np.zeros(4), 0
    for e in range(n):
        s, mid = DEMAND, 0
        for d in range(DAYS):
            rain = bool(u[e, d, 0] < rain_p)
            k = choose(d, rain, s)
            modes[acts[k][1]] += 1
            viol += acts[k][1] == 3
            s = _step(s, effs[k], rain, bool(u[e, d, 1] < effs[k][3]))
            mid += _mid(d, s)
        losses[e] = _loss(s) + mid
    return {"loss": float(losses.mean()), "se": float(losses.std(ddof=1) / np.sqrt(n)), "modes": (modes / modes.sum()).tolist(),
            "violations_per_week": float(viol / n)}


def greedy_chooser(effs: list):
    """その日の進み（重みつき）がいちばん大きい行動を選ぶ。先のことは考えない。"""
    def choose(d, rain, s):
        def gain(e):
            return (WEIGHT[0] * (0 if rain else min(s[0], e[0])) + WEIGHT[1] * min(s[1], e[1]) + WEIGHT[2] * min(s[2], e[2])
                    - WEIGHT[2] * e[3] * e[4])
        return max(range(len(effs)), key=lambda k: gain(effs[k]))
    return choose


def static_plan(prm: dict) -> list[int]:
    """晴れが続く前提で最適な1週間の計画を作り、天候を見ずにそのまま実行する（比べる用）"""
    sol = solve_week(0.0, prm)
    s, seq = DEMAND, []
    for d in range(DAYS):
        k = int(sol["policy"][(d, 0) + s])
        seq.append(k)
        s = _step(s, sol["effs"][k], False, False)
    return seq


def q_learning(rain_p: float, prm: dict, episodes: int = 60000, seed: int = 0, alpha: float = 0.3, blocks: int = 20) -> dict:
    """表形式のQ学習（強化学習）。天候の確率を知らされず、試行錯誤だけで方策を学ぶ。承認なしの行動は選べない（行動の制約）。
    報酬は「重みつきの残りが減った量 − 締めの損失」。合計は週の損失と定数だけ違うので、目的は動的計画法と同じ。"""
    acts = _actions(True)
    effs = [_effect(a, prm) for a in acts]
    q = np.zeros((DAYS, 2, DEMAND[0] + 1, DEMAND[1] + 1, A_MAX + 1, len(acts)))
    rng = np.random.default_rng(seed)
    u = rng.random((episodes, DAYS, 4))
    pick = rng.integers(len(acts), size=(episodes, DAYS))
    ep_loss = np.empty(episodes)
    for e in range(episodes):
        eps = max(0.02, 0.3 * (1 - e / (0.8 * episodes)))
        s, rain, mid = DEMAND, bool(u[e, 0, 0] < rain_p), 0
        for d in range(DAYS):
            row = q[(d, int(rain)) + s]
            k = int(pick[e, d]) if u[e, d, 1] < eps else int(row.argmax())
            s2 = _step(s, effs[k], rain, bool(u[e, d, 2] < effs[k][3]))
            rain2 = bool(u[e, d, 3] < rain_p)
            target = (_loss(s) - _loss(s2) - _mid(d, s2)) + (q[(d + 1, int(rain2)) + s2].max() if d < DAYS - 1 else 0.0)
            row[k] += alpha * (target - row[k])
            mid += _mid(d, s2)
            s, rain = s2, rain2
        ep_loss[e] = _loss(s) + mid
    size = episodes // blocks
    curve = [(int((b + 1) * size), float(ep_loss[b * size:(b + 1) * size].mean())) for b in range(blocks)]
    return {"choose": lambda d, rain, s: int(q[(d, int(rain)) + s].argmax()), "acts": acts, "effs": effs, "curve": curve}


def compare_week(prm: dict, rain_p: float = 0.3, episodes: int = 60000, n: int = 2000, seed: int = 0) -> dict:
    """固定計画・貪欲法・Q学習・動的計画法（上限）を、同じ乱数の週で比べる。制約を外した場合も添える。"""
    dp = solve_week(rain_p, prm)
    acts, effs = dp["acts"], dp["effs"]
    seq = static_plan(prm)
    ql = q_learning(rain_p, prm, episodes, seed)
    free = solve_week(rain_p, prm, constrained=False)
    out = {
        "固定計画（晴れ前提）": simulate_week(lambda d, r, s: seq[d], acts, effs, rain_p, n, seed + 1),
        "貪欲法（その日いちばん進む）": simulate_week(greedy_chooser(effs), acts, effs, rain_p, n, seed + 1),
        "Q学習（強化学習）": simulate_week(ql["choose"], acts, effs, rain_p, n, seed + 1),
        "動的計画法（確率が既知の上限）": simulate_week(lambda d, r, s: int(dp["policy"][(d, int(r)) + s]), acts, effs, rain_p, n, seed + 1),
    }
    unconstrained = simulate_week(lambda d, r, s: int(free["policy"][(d, int(r)) + s]), free["acts"], free["effs"], rain_p, n, seed + 1)
    return {"results": out, "curve": ql["curve"], "dp_expected": dp["expected_loss"], "unconstrained": unconstrained,
            "static_seq": [(PATTERNS[acts[k][0]], MODES[acts[k][1]]) for k in seq]}


def rain_sweep(prm: dict, probs=(0.0, 0.15, 0.3, 0.45, 0.6), n: int = 1500, seed: int = 0) -> pd.DataFrame:
    """雨の確率を変えて、固定計画・貪欲法・動的計画法の損失を比べる（天候の不確かさが大きいほど、適応の価値が出るか）"""
    seq, rows = static_plan(prm), []
    for p in probs:
        dp = solve_week(p, prm)
        acts, effs = dp["acts"], dp["effs"]
        for name, ch in [("固定計画（晴れ前提）", lambda d, r, s: seq[d]), ("貪欲法（その日いちばん進む）", greedy_chooser(effs)),
                         ("動的計画法（確率が既知の上限）", lambda d, r, s: int(dp["policy"][(d, int(r)) + s]))]:
            rows.append({"雨の確率": p, "方法": name, "損失": simulate_week(ch, acts, effs, p, n, seed + 1)["loss"]})
    return pd.DataFrame(rows)


# ============================================================
# C 本当に効いたか：複数法人の ABAB、交絡の調整、階層ベイズ
# ============================================================
def overlap_table(abab: pd.DataFrame, col: str = "事務作業時間_分") -> pd.DataFrame:
    """法人ごとの 重なりのない割合・NAP（値が小さいほど良い指標なので、符号を反転して数える）"""
    rows = []
    for f, g in abab.groupby("法人", sort=False):
        a, b = (-g[g["期"].str[0] == "A"][col]).tolist(), (-g[g["期"].str[0] == "B"][col]).tolist()
        rows.append({"法人": f, "Aの平均": -float(np.mean(a)), "Bの平均": -float(np.mean(b)), "重なりのない割合": gc.pnd(a, b), "NAP": gc.nap(a, b)})
    return pd.DataFrame(rows)


def farm_effects(abab: pd.DataFrame, adjust: bool = True) -> pd.DataFrame:
    """法人ごとに log(事務作業時間) を回帰し、導入期Bの係数と標準誤差を出す。adjust=True で繁忙期・雨の日数を入れる。"""
    rows = []
    for f, g in abab.groupby("法人", sort=False):
        y = np.log(g["事務作業時間_分"].to_numpy(float))
        cols = [np.ones(len(g)), (g["期"].str[0] == "B").to_numpy(float)]
        if adjust:
            cols += [g["繁忙期"].to_numpy(float), g["雨の日数"].to_numpy(float)]
        x = np.column_stack(cols)
        coef = np.linalg.lstsq(x, y, rcond=None)[0]
        resid = y - x @ coef
        se = float(np.sqrt(resid @ resid / (len(y) - x.shape[1]) * np.linalg.inv(x.T @ x)[1, 1]))
        rows.append({"法人": f, "効果": float(coef[1]), "標準誤差": se})
    return pd.DataFrame(rows)


def hier_bayes(effect: np.ndarray, se: np.ndarray, n: int = 8000, seed: int = 0) -> dict:
    """階層ベイズ（正規–正規）。法人ごとの効果 θ_j ~ N(μ, τ²)。μ と τ は一様な事前分布、τ は格子で積分する。"""
    y, v = np.asarray(effect, float), np.asarray(se, float) ** 2
    taus = np.linspace(1e-4, 0.5, 400)
    logp = np.empty(len(taus))
    for i, t in enumerate(taus):
        w = 1 / (v + t ** 2)
        mu_hat = (w * y).sum() / w.sum()
        logp[i] = 0.5 * np.log(1 / w.sum()) + 0.5 * np.log(w).sum() - 0.5 * (w * (y - mu_hat) ** 2).sum()
    p = np.exp(logp - logp.max())
    p /= p.sum()
    rng = np.random.default_rng(seed)
    tau = rng.choice(taus, size=n, p=p)
    w = 1 / (v[None, :] + tau[:, None] ** 2)
    mu = rng.normal((w * y).sum(1) / w.sum(1), np.sqrt(1 / w.sum(1)))
    prec = 1 / v[None, :] + 1 / tau[:, None] ** 2
    theta = rng.normal((y / v + mu[:, None] / tau[:, None] ** 2) / prec, np.sqrt(1 / prec))
    q = lambda a, k: float(np.quantile(a, k))
    return {"mu": float(mu.mean()), "mu_lo": q(mu, .025), "mu_hi": q(mu, .975), "p_neg": float((mu < 0).mean()),
            "tau": float(np.median(tau)), "theta": theta.mean(0).tolist(),
            "theta_lo": np.quantile(theta, .025, axis=0).tolist(), "theta_hi": np.quantile(theta, .975, axis=0).tolist(),
            "saving": float(1 - np.exp(mu).mean()), "saving_lo": float(1 - np.exp(q(mu, .975))), "saving_hi": float(1 - np.exp(q(mu, .025)))}


def effect_summary(abab: pd.DataFrame) -> dict:
    naive, adj = farm_effects(abab, False), farm_effects(abab, True)
    return {"naive": naive, "adjusted": adj,
            "hb_naive": hier_bayes(naive["効果"], naive["標準誤差"]), "hb_adjusted": hier_bayes(adj["効果"], adj["標準誤差"])}


# ============================================================
# D ショックに耐えるか：委任水準 × ガードレール のシミュレーション
# ============================================================
SIM = {"days": 150, "demand": 0.97, "agent_extra": 0.5, "p0": 0.03, "guard_cut": 0.8, "incident_drop": 0.25,
       "incident_days": 5, "incident_cost": 3.0, "delay_cost": 0.1}   # すべて仮置き


def simulate_resilience(level: float, guard: float, saving: float, adm_share: float, shock: tuple, runs: int = 300, seed: int = 0) -> dict:
    """1法人を「日々の作業能力と、積み残し」で表す。
    level＝任せられる事務のうちエージェントに渡す割合（0〜1）、guard＝ガードレールの整備度（0〜1）、
    saving＝C で推定した事務の時短率、adm_share＝全作業に占める事務の割合、shock＝(名前, 開始日, 期間, 能力の低下率, 追加費用／日)"""
    _, start, length, drop, extra = shock
    rng = np.random.default_rng(seed)
    freed = adm_share * (saving + SIM["agent_extra"] * level)          # 事務から浮く人手の割合
    cap0 = 1 / (1 - freed)
    p_inc = SIM["p0"] * level ** 2 * (1 - SIM["guard_cut"] * guard)   # 誤作動・漏えいが起きる1日あたりの確率
    backlog, down = np.zeros(runs), np.zeros(runs, dtype=int)
    loss, incidents = np.zeros(runs), np.zeros(runs)
    recover = np.full(runs, float(SIM["days"] - start - length))       # 回復しなければ打ち切りの日数
    done = np.zeros(runs, dtype=bool)
    for t in range(SIM["days"]):
        hit = rng.random(runs) < p_inc
        incidents += hit
        loss += hit * SIM["incident_cost"]
        down = np.where(hit, SIM["incident_days"], np.maximum(down - 1, 0))
        cap = cap0 * (1 - (drop if start <= t < start + length else 0.0)) * (1 - SIM["incident_drop"] * (down > 0))
        backlog = np.maximum(backlog + SIM["demand"] - cap, 0)
        loss += backlog * SIM["delay_cost"] + (extra if start <= t < start + length else 0.0)
        if t >= start + length:
            now = (~done) & (backlog <= 0.05)
            recover[now] = t - (start + length)
            done |= now
    return {"loss": float(loss.mean()), "recovery": float(recover.mean()), "incidents": float(incidents.mean()),
            "not_recovered": float((~done).mean())}


def delegation_sweep(guard: float, saving: float, adm_share: float, shock: tuple, runs: int = 300, seed: int = 0) -> pd.DataFrame:
    levels = np.round(np.arange(0, 1.01, 0.1), 1)
    return pd.DataFrame([{"委任水準": float(lv), **simulate_resilience(float(lv), guard, saving, adm_share, shock, runs, seed)} for lv in levels])


def best_level(sweep: pd.DataFrame) -> float:
    return float(sweep.loc[sweep["loss"].idxmin(), "委任水準"])


def admin_share(tasks: pd.DataFrame) -> float:
    """全作業に占める事務の割合（B の週の作業量から）"""
    return DEMAND[2] / sum(DEMAND)


# ============================================================
# 一本の流れ
# ============================================================
def pipeline(data: dict[str, pd.DataFrame], episodes: int = 60000) -> dict:
    """A の出力が B の前提に、B の割当が C の「導入期」に、C の推定値が D の係数になる。"""
    d = classified(data["diary"])
    dmap = delegation_map(d, data["tasks"])
    use, agent = admin_shares(dmap)
    prm = week_params(use, agent)
    week = compare_week(prm, episodes=episodes)
    eff = effect_summary(data["abab"])
    saving = eff["hb_adjusted"]["saving"]
    share = admin_share(data["tasks"])
    sweeps = {tuple(s)[0]: delegation_sweep(0.5, saving, share, tuple(s)) for s in data["shocks"].itertuples(index=False)}
    return {"diary": d, "map": dmap, "shares": (use, agent), "prm": prm, "week": week, "effect": eff, "saving": saving,
            "adm_share": share, "sweeps": sweeps}


# ============================================================
# 自己チェック
# ============================================================
def _self_check() -> None:
    data = make_data()
    assert classify("遅れなし。順調。") == "" and classify("人手は足りた。") == "" and classify("機械の故障はなかった。") == ""
    assert classify("トラクターが故障し、作業を中断した。") == "身体作業型" and classify("段取りが悪く遅れた。") == "未分類"
    assert classify("人手が足りない中で、どの作業を優先するか決め直した。") == "判断型"
    kt = keyword_table(data["diary"]).set_index("語")
    assert (kt["否定を除いた日誌数"] < kt["含む日誌数"]).all() and (kt["出現回数"] >= kt["含む日誌数"]).all()
    d = classified(data["diary"])
    chk = dictionary_check(d)
    assert chk["拾った中の一致率"] > 0.95 and chk["見落とし"] > 0 and chk["誤って拾った"] == 0
    dmap = delegation_map(d, data["tasks"])
    assert set(dmap["目安"]) <= set(RECS) and (dmap.loc[dmap["作業"] == "収穫", "目安"] == RECS[2]).all()
    asg = assignment(data["skills"], data["tasks"])
    assert asg["best_score"] >= asg["greedy_score"] and len(set(asg["best"])) == len(SKILLS)
    prm = week_params(*admin_shares(dmap))
    sol = solve_week(0.3, prm)
    acts, effs = sol["acts"], sol["effs"]
    sim = simulate_week(lambda dd, r, s: int(sol["policy"][(dd, int(r)) + s]), acts, effs, 0.3, 3000, 1)
    assert abs(sim["loss"] - sol["expected_loss"]) < 4 * sim["se"] + 0.2 and sim["violations_per_week"] == 0
    seq = static_plan(prm)
    assert simulate_week(lambda dd, r, s: seq[dd], acts, effs, 0.3, 1000, 1)["loss"] >= sim["loss"] - 1.0
    assert solve_week(0.3, prm, constrained=False)["expected_loss"] <= sol["expected_loss"] + 1e-9
    eff = effect_summary(data["abab"])
    hb = eff["hb_adjusted"]
    assert hb["mu_lo"] < TRUE["mu"] < hb["mu_hi"] and hb["p_neg"] > 0.95 and 0 < hb["saving"] < 0.5
    sw = delegation_sweep(0.5, hb["saving"], admin_share(data["tasks"]), SHOCKS[0], runs=100)
    assert len(sw) == 11 and (sw["loss"] > 0).all()
    print("agri_case: 自己チェック OK")


if __name__ == "__main__":
    if "--make-data" in sys.argv:
        make_data(DATA)
        print(f"ダミーデータを書き出しました：{DATA}")
    else:
        _self_check()
