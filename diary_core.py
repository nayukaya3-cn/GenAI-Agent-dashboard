"""
作業日誌・お客さんの声の「困りごと分析」 ─ データと計算部品

「X 売る」の ⑥ で使う。支援先の作業日誌（困りごと）や、定期便の感想（不満の芽）を、
  ① 匿名化・前処理（氏名・取引先・電話・URL を置換、NFKC で表記をそろえる。元の文は別に残す）
  ② 数える（1件に2回出ても件数は1。出現回数は別に数える。分母をつける）
  ③ 原文を読む（否定・解消の表現に印。困りごとかどうかは人が決める）
  ④ 示唆（作業ごとの割合をベイズで推定し、エージェントに任せられそうな仕事へ）
  ⑤ 確かめて報告（生成AIの答えは合計より先に内訳を照合。方法｜結果｜限界）
の順に扱う。もとはブラウザ1枚で動く static/diary_analysis.html（同じ手順のフル版）。

方針（genai_core.py・nox_core.py と同じ）
  - 生成AIを呼び出さない。外へ何も送らない。
  - 初期データはすべて架空。人・取引先・電話番号も架空。
  - 否定表現のルール・例外の辞書は仮置きの目安。最後に決めるのは原文を読んだ人。

Streamlit に依存しない。`python diary_core.py` で自己チェック。
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from collections.abc import Iterable, Sequence

import numpy as np

# ============================================================
# 初期データ（架空）
# ============================================================
DIARY_TSV = """\
日付	作業	記入者	本文
2026-04-03	育苗	佐藤	育苗ハウスの温度管理。換気扇が一時止まったが、故障ではなかった。
2026-04-07	育苗	鈴木	播種作業。予定より半日遅れ。人手が足りず、高橋さんに応援を頼んだ。
2026-04-10	機械整備	高橋	田植機の点検。爪の摩耗あり、部品をみなと運送経由で取り寄せ。
2026-04-15	育苗	山本	苗の生育は順調。遅れはない。
2026-04-18	草刈り	佐藤	畦の草刈り。刈払機のエンジンがかかりにくい。故障かもしれない。
2026-04-22	育苗	鈴木	水やり。特に問題なし。
2026-04-25	機械整備	高橋	刈払機を修理に出した。故障箇所はキャブレター。
2026-04-28	出荷調整	山本	ひがし青果向けの葉物を出荷。箱詰めが遅れ、集荷に間に合わなかった。
2026-05-02	田植え	佐藤	田植え開始。田植機の故障はなかった。
2026-05-06	田植え	鈴木	雨で田植えが遅れ。遅れ、遅れで予定が詰まってきた。
2026-05-09	田植え	高橋	人手不足。補植まで手が回らない。
2026-05-13	田植え	山本	田植え完了。人手は足りた。佐藤さんの段取りが良かった。
2026-05-17	防除	佐藤	除草剤散布。風が強く半日延期。
2026-05-21	出荷調整	鈴木	やまびこ食品から追加注文。人手が足りず、残業で対応。
2026-05-26	草刈り	高橋	草刈り。刈払機は修理から戻り、問題なく動いた。
2026-05-30	防除	山本	散布機のノズルが詰まり、作業が遅れた。
2026-06-03	防除	佐藤	病害の初期症状。早めに防除。遅れなし。
2026-06-07	草刈り	鈴木	暑さで作業ペースが落ちる。人手がもう一人ほしい。
2026-06-11	出荷調整	高橋	ひがし青果への出荷。選別機が故障し、手作業で選別。2時間遅れ。
2026-06-14	機械整備	山本	選別機の故障を業者に連絡。部品待ち。
2026-06-18	出荷調整	佐藤	選別機はまだ直らない。人手で対応しているが限界。
2026-06-22	草刈り	鈴木	梅雨の晴れ間に草刈り。順調。
2026-06-26	防除	高橋	散布機のホースが破れた。故障ではなく消耗。交換した。
2026-06-30	出荷調整	山本	選別機が直った。遅れは解消。
2026-07-03	収穫	佐藤	きゅうりの収穫。収穫量が多く人手が追いつかない。
2026-07-07	収穫	鈴木	収穫と出荷が重なり、出荷が遅れた。山本さんに連絡済み。
2026-07-10	出荷調整	高橋	やまびこ食品の担当者（090-1234-5678）から納期の確認。
2026-07-14	収穫	山本	収穫順調。人手は足りている。
2026-07-17	草刈り	佐藤	草の伸びが早い。草刈りが遅れ気味。
2026-07-21	機械整備	鈴木	軽トラのエアコン故障。熱中症が心配。
2026-07-24	収穫	高橋	収穫。特に遅れなし。
2026-07-28	出荷調整	山本	出荷ラベルの印刷ミス。貼り直しで30分遅れ。
2026-08-01	収穫	佐藤	猛暑で午前のみ作業。人手が足りず収穫が遅れた。
2026-08-05	防除	鈴木	害虫が増えている。防除が遅れたかもしれない。
2026-08-08	収穫	高橋	お盆前で注文増。人手不足が深刻。
2026-08-12	出荷調整	山本	ひがし青果へ出荷。遅れなし。
2026-08-16	草刈り	佐藤	休み明けの草刈り。故障なし。
2026-08-19	機械整備	鈴木	冷蔵庫の温度が下がらない。故障の可能性があり業者に連絡。
2026-08-23	収穫	高橋	収穫量が落ちてきた。人手は足りた。
2026-08-27	出荷調整	山本	冷蔵庫の故障で出荷前の保管ができず、当日出荷に切り替え。
2026-09-01	稲刈り準備	佐藤	コンバインの点検。動かなくなる箇所はなかった。
2026-09-04	稲刈り準備	鈴木	乾燥機の試運転。異音あり。
2026-09-08	稲刈り	高橋	稲刈り開始。コンバインが詰まり、作業が遅れた。
2026-09-11	稲刈り	山本	台風で稲刈りが遅れ。人手を集め直す必要あり。
2026-09-15	稲刈り	佐藤	稲刈り再開。人手が足りず、鈴木さんと二人で対応。
2026-09-18	乾燥調製	鈴木	乾燥機の故障。修理まで3日。籾の保管場所が足りない。
2026-09-22	乾燥調製	高橋	乾燥機が直り、作業再開。遅れを取り戻す。
2026-09-26	出荷調整	山本	新米をやまびこ食品へ出荷。予定どおり。
"""

FEEDBACK_TSV = """\
日付	便	会員	本文
2026-06-10	初夏の便	田中	パンがもちもちでおいしい。箱を開けたときの小麦の香りが良かった。
2026-06-10	初夏の便	中村	配送が1日遅れた。パンが少し固くなっていた。
2026-06-11	初夏の便	小林	値段は高いけど、畑の便りが付いているので納得。
2026-06-12	初夏の便	加藤	量が少なめで、家族4人だと足りない。
2026-06-12	初夏の便	吉田	高いとは思わない。体験に行けたのがうれしい。
2026-06-15	初夏の便	田中	届くのが遅く、不在票が入っていた。
2026-07-20	枝豆の便	中村	枝豆がゆでたてのように甘い。量も十分。
2026-07-20	枝豆の便	小林	枝豆の量が少なくないのに、値段は据え置きでありがたい。
2026-07-21	枝豆の便	加藤	到着が遅れ、枝豆が少ししなびていた。
2026-07-22	枝豆の便	吉田	送料込みだとやや高い。量はちょうど良い。
2026-07-25	枝豆の便	田中	遅れはなかった。収穫祭の写真が楽しい。
2026-07-26	枝豆の便	松本	ゆで方のメモがあって助かった。
2026-09-15	収穫祭の便	中村	イベントの日程連絡が遅れて、参加できなかった。
2026-09-15	収穫祭の便	小林	味噌づくり体験は高いかもしれないが、子どもが喜ぶなら参加したい。
2026-09-16	収穫祭の便	加藤	パンの数が少ない。もう1個ほしい。
2026-09-18	収穫祭の便	吉田	担当の松本さん（090-2222-3333）に連絡したら、すぐ返事が来た。
2026-11-10	冬の便	田中	小麦粉の量が少なく、パンを2回しか焼けなかった。
2026-11-10	冬の便	中村	冬の便は値段が高い。年末は出費が重なる。
2026-11-11	冬の便	小林	配送の遅れは解消していた。前回より早い。
2026-11-12	冬の便	加藤	種まきの便りを読んで、来年も続けたいと思った。
2026-11-12	冬の便	吉田	量は少ないが質が良いので満足。
2026-11-14	冬の便	松本	箱が大きいわりに中身が少ない気がする。
2026-11-15	冬の便	田中	年末の配送が遅れないか心配。
2026-11-16	冬の便	中村	ひがし青果のパンより高いが、香りが全然違う。
"""

DEF_NEG = "ない|なかった|なし|無し|ません|ではなく|足りた|足りている|解消|直った|問題なく"
DEF_EX = "かもしれない|追いつかない|間に合わな|足りない|回らない|直らない|動かな|下がらない|できない"

# 人の判定例（行番号1始まり → キーワード: 1=困りごと・不満, 0=該当せず）
PRESETS: dict[str, dict] = {
    "作業日誌（支援先の困りごと）": {
        "text": DIARY_TSV, "names": ["佐藤", "鈴木", "高橋", "山本"], "orgs": ["ひがし青果", "やまびこ食品", "みなと運送"],
        "unit": "日誌", "target": "困りごと", "group_col": "作業", "writer": "作業者",
        "question": "作業上の困りごとが、どの作業や時期に、どのような言葉で書かれているか。",
        "groups": [("d", "遅れ", "遅延, 間に合わ, 延期, 押した"),
                   ("f", "故障", "壊れ, 直らない, 動かな, 不調, 異音, 詰まり, 破れ"),
                   ("h", "人手", "人が足り, 手が回らない, 手が足り, 応援, 残業")],
        "labels": {1: {"f": 0}, 2: {"d": 1, "h": 1}, 4: {"d": 0}, 5: {"f": 1}, 7: {"f": 1}, 8: {"d": 1}, 9: {"f": 0},
                   10: {"d": 1}, 11: {"h": 1}, 12: {"h": 0}, 14: {"h": 1}, 16: {"d": 1}, 17: {"d": 0}, 18: {"h": 1},
                   19: {"f": 1, "d": 1}, 20: {"f": 1}, 21: {"h": 1}, 23: {"f": 0}, 24: {"d": 0}, 25: {"h": 1},
                   26: {"d": 1}, 28: {"h": 0}, 29: {"d": 1}, 30: {"f": 1}, 31: {"d": 0}, 32: {"d": 1},
                   33: {"h": 1, "d": 1}, 34: {"d": 1}, 35: {"h": 1}, 36: {"d": 0}, 37: {"f": 0}, 38: {"f": 1},
                   39: {"h": 0}, 40: {"f": 1}, 43: {"d": 1}, 44: {"d": 1, "h": 1}, 45: {"h": 1}, 46: {"f": 1}, 47: {"d": 1}},
    },
    "定期便の感想（お客さんの不満の芽）": {
        "text": FEEDBACK_TSV, "names": ["田中", "中村", "小林", "加藤", "吉田", "松本"], "orgs": ["ひがし青果"],
        "unit": "感想", "target": "不満", "group_col": "便", "writer": "会員",
        "question": "定期便のどの便で、どんな不満が、どのような言葉で書かれているか。（ほめ言葉は数えるより、そのまま読む）",
        "groups": [("d", "遅れ", "遅く, 遅延, 届かな"), ("p", "高い", "高め, 割高, 送料"), ("q", "少な", "足りな, 物足り")],
        "labels": {2: {"d": 1}, 3: {"p": 0}, 4: {"q": 1}, 5: {"p": 0}, 8: {"q": 0}, 9: {"d": 1}, 10: {"p": 1}, 11: {"d": 0},
                   13: {"d": 1}, 14: {"p": 1}, 15: {"q": 1}, 17: {"q": 1}, 18: {"p": 1}, 19: {"d": 0}, 21: {"q": 0},
                   22: {"q": 1}, 23: {"d": 1}, 24: {"p": 0}},
    },
}

# ============================================================
# ① 読み込みと匿名化・前処理
# ============================================================
_COLS = {"date": r"^(日付|date)", "task": r"^(作業|便|商品|task)", "writer": r"^(記入者|会員|氏名|author|name)",
         "raw": r"^(本文|内容|感想|text|body|メモ)"}


def parse_table(text: str) -> list[dict]:
    """タブ区切りかカンマ区切りの表。1行目に見出し（日付・作業・記入者・本文）。見出しが無ければ列の順で読む。"""
    text = (text or "").strip("\n")
    if not text:
        return []
    delim = "\t" if "\t" in text.split("\n")[0] else ","
    tbl = [r for r in csv.reader(io.StringIO(text), delimiter=delim) if any(c.strip() for c in r)]
    head = [c.strip() for c in tbl[0]]
    idx = {k: next((i for i, h in enumerate(head) if re.search(p, h, re.I)), -1) for k, p in _COLS.items()}
    body = tbl[1:]
    if idx["raw"] < 0:
        idx, body = {"date": 0, "task": 1, "writer": 2, "raw": 3}, tbl
    get = lambda r, k: r[idx[k]].strip() if 0 <= idx[k] < len(r) else ""  # noqa: E731
    rows = [{"n": i + 1, "date": get(r, "date"), "task": get(r, "task") or "（未記入）", "writer": get(r, "writer"),
             "raw": get(r, "raw")} for i, r in enumerate(body)]
    return [r for r in rows if r["raw"]]


_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NOTNAME = re.compile(r"^(皆|お客|奥|業者|担当|社長|みな|皆様|お子)$")
AUTO_RULES = [
    ("電話番号", re.compile(r"0\d{1,4}-\d{1,4}-\d{3,4}")),
    ("URL", re.compile(r"https?://[^\s、。）)」]+")),
    ("メール", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
]
ORG_AUTO = re.compile(r"(株式会社|有限会社|\(株\))[ァ-ヶー一-龥ぁ-んA-Za-z]{1,10}|[ァ-ヶー一-龥ぁ-んA-Za-z]{1,6}(青果|食品|商店|運送|商事|農協|物産)")
NAME_AUTO = re.compile(r"([一-龥]{1,3}|[ァ-ヶ][ァ-ヶー]{1,5})(さん|様|くん|氏)")


def _code(prefix: str, i: int) -> str:
    return prefix + (_LETTERS[i] if i < 26 else _LETTERS[i // 26 - 1] + _LETTERS[i % 26])


def anonymize(rows: Sequence[dict], names: Iterable[str] = (), orgs: Iterable[str] = (), auto: bool = True,
              nfkc: bool = True, person: str = "作業者") -> tuple[list[dict], list[dict]]:
    """氏名→「作業者A」、取引先→「取引先A」、電話・URL・メール→［電話番号］などに置きかえる。
    置きかえた部分は \x00 で囲った目印にしてから戻すので、あとの規則が置換済みの文字に反応しない。
    返り値：(行, 置換の記録)。行には raw（元の文・共有しない）、norm（NFKC後）、anon（分析に使う文）が入る。"""
    names = [n.strip() for n in names if n and n.strip()]
    orgs = [o.strip() for o in orgs if o and o.strip()]
    pmap: dict[str, str] = {}
    omap: dict[str, str] = {}
    log: dict[tuple[str, str], dict] = {}

    def pcode(n: str) -> str:
        return pmap.setdefault(n, _code(person, len(pmap)))

    def ocode(n: str) -> str:
        return omap.setdefault(n, _code("取引先", len(omap)))

    def note(kind: str, src: str, dst: str, how: str) -> None:
        e = log.setdefault((kind, src), {"種類": kind, "元の語": src, "置換後": dst, "方法": how, "回数": 0})
        e["回数"] += 1

    for r in rows:
        if r["writer"]:
            pcode(r["writer"])
    for n in names:
        pcode(n)
    for o in orgs:
        ocode(o)
    out = []
    for r in rows:
        norm = unicodedata.normalize("NFKC", r["raw"]) if nfkc else r["raw"]
        slots: list[str] = []

        def put(s: str) -> str:
            slots.append(s)
            return f"\x00{len(slots) - 1}\x00"

        t = norm
        dic = sorted({*pmap, *orgs}, key=len, reverse=True)
        if dic:
            def dict_rep(m: re.Match) -> str:
                w = m.group(0)
                if w in omap and w not in pmap:
                    note("取引先", w, omap[w], "辞書")
                    return put(omap[w])
                note("氏名", w, pcode(w), "辞書")
                return put(pcode(w))
            t = re.sub("|".join(map(re.escape, dic)), dict_rep, t)
        if auto:
            for kind, pat in AUTO_RULES:
                t = pat.sub(lambda m, k=kind: (note(k, m.group(0), f"［{k}］", "自動"), put(f"［{k}］"))[1], t)
            t = ORG_AUTO.sub(lambda m: (note("取引先", m.group(0), ocode(m.group(0)), "自動"), put(ocode(m.group(0))))[1], t)

            def name_rep(m: re.Match) -> str:
                nm, hon = m.group(1), m.group(2)
                if NOTNAME.match(nm):
                    return m.group(0)
                note("氏名", nm, pcode(nm), "自動")
                return put(pcode(nm)) + hon
            t = NAME_AUTO.sub(name_rep, t)
        anon = re.sub(r"\x00(\d+)\x00", lambda m: slots[int(m.group(1))], t)
        mo = re.match(r"^(\d{4})[-/](\d{1,2})", r["date"])
        out.append({**r, "id": f"D{r['n']:03d}", "norm": norm, "nfkc_changed": norm != r["raw"], "anon": anon,
                    "writer_code": pcode(r["writer"]) if r["writer"] else "",
                    "month": f"{mo.group(1)}-{int(mo.group(2)):02d}" if mo else "不明"})
    return out, sorted(log.values(), key=lambda e: (e["種類"], -e["回数"]))


RISK = [("敬称つきの語", re.compile(r"[一-龥ァ-ヶー]{1,6}(?:さん|様|くん|氏|ちゃん)")), ("長い数字の並び", re.compile(r"\d{6,}")),
        ("郵便番号・〒", re.compile(r"〒|(?<!\d)\d{3}-\d{4}(?!\d)")),
        ("住所らしき並び", re.compile(r"[一-龥]{2,4}(?:市|町|村)[一-龥]{1,4}(?:\d|丁目|番地)")), ("@を含む語", re.compile(r"\S*@\S*"))]
_NOTN_FULL = re.compile(r"^(皆|お客|奥|業者|担当|社長|みな|皆様|お子)(さん|様)$")


def residual(rows: Sequence[dict]) -> list[dict]:
    """匿名化のあとに残っていそうなもの。機械の目安で、見つからなくても残っていないとは限らない。"""
    found = []
    for r in rows:
        for kind, pat in RISK:
            for m in pat.finditer(r["anon"]):
                w = m.group(0)
                if kind == "敬称つきの語" and _NOTN_FULL.match(w):
                    continue
                found.append({"ID": r["id"], "種類": kind, "見つかった語": w})
    return found


# ============================================================
# ② 数える：件数と回数、否定・解消の印
# ============================================================
def terms(base: str, syn: str, use_syn: bool) -> list[str]:
    t = [base.strip()] if base.strip() else []
    if use_syn:
        t += [s.strip() for s in re.split(r"[,、，]", syn or "") if s.strip() and s.strip() not in t]
    return t


def _compile(p: str, flags: int = 0) -> re.Pattern | None:
    try:
        return re.compile(p, flags) if p and p.strip() else None
    except re.error:
        return None


def _neg_in(after: str, neg: re.Pattern | None, ex: re.Pattern | None) -> tuple[str, str]:
    """直後の文に否定・解消の表現があれば (その語, 打ち消した例外) を返す。例外に一致した部分は否定として見ない。"""
    if neg is None:
        return "", ""
    exw = ""
    if ex is not None:
        m = ex.search(after)
        if m:
            exw = m.group(0)
            after = ex.sub(lambda x: "□" * len(x.group(0)), after)
    m = neg.search(after)
    return (m.group(0) if m else ""), exw


def match_row(text: str, ts: Sequence[str], neg: str = DEF_NEG, ex: str = DEF_EX, use_ex: bool = True,
              window: int = 12) -> list[dict]:
    """語の出現位置。重なりは長い語・基本の語を優先。各出現に「直後12文字（句点まで）」の否定の印を付ける。"""
    occ: list[dict] = []
    base = ts[0] if ts else ""
    for t in sorted(ts, key=lambda w: (w != base, -len(w))):
        i = text.find(t)
        while i != -1:
            e = i + len(t)
            if not any(i < o["e"] and e > o["s"] for o in occ):
                occ.append({"s": i, "e": e, "t": t})
            i = text.find(t, e)
    occ.sort(key=lambda o: o["s"])
    nre, xre = _compile(neg), _compile(ex) if use_ex else None
    for o in occ:
        after = text[o["e"]:].split("。")[0][:window]
        w, exw = _neg_in(after, nre, xre)
        w0, _ = _neg_in(after, nre, None)
        o.update(after=after, neg=bool(w), neg_word=w, ex_word=exw, neg_noex=bool(w0))
    return occ


def analyze(rows: Sequence[dict], groups: Sequence[tuple[str, str, str]], use_syn: bool = False, neg: str = DEF_NEG,
            ex: str = DEF_EX, use_ex: bool = True) -> list[dict]:
    """行ごと・語ごとに {hit, count, neg, neg_noex, occ} を r["m"][key] に入れる"""
    for r in rows:
        r["m"] = {}
        for k, base, syn in groups:
            occ = match_row(r["anon"], terms(base, syn, use_syn), neg, ex, use_ex)
            r["m"][k] = {"occ": occ, "hit": bool(occ), "count": len(occ), "neg": any(o["neg"] for o in occ),
                         "neg_noex": any(o["neg_noex"] for o in occ)}
    return list(rows)


BASIS = {"all": "一致した", "noneg": "否定の可能性を除いた", "human": "人が判定した"}


def counted(r: dict, k: str, basis: str, labels: dict) -> bool:
    x = r["m"][k]
    if not x["hit"]:
        return False
    if basis == "noneg":
        return not x["neg"]
    if basis == "human":
        return labels.get((r["id"], k)) == 1
    return True


def summary(rows: Sequence[dict], groups: Sequence[tuple], basis: str, labels: dict) -> list[dict]:
    """語ごとの 件数（基準つき）・一致した件数・出現回数・否定の可能性。分母は全件数。"""
    n = len(rows)
    out = []
    for k, base, _ in groups:
        hit = [r for r in rows if r["m"][k]["hit"]]
        c = sum(counted(r, k, basis, labels) for r in rows)
        out.append({"語": base, "件数": c, "全件": n, "割合": c / n if n else 0.0, "一致": len(hit),
                    "出現回数": sum(r["m"][k]["count"] for r in hit), "否定の可能性": sum(r["m"][k]["neg"] for r in hit)})
    return out


def by_task(rows: Sequence[dict], groups: Sequence[tuple], basis: str, labels: dict) -> list[dict]:
    """作業（または便）ごとの件数と、その作業の日誌数（分母）"""
    tasks = list(dict.fromkeys(r["task"] for r in rows))
    out = []
    for t in tasks:
        rs = [r for r in rows if r["task"] == t]
        row = {"作業": t, "日誌数": len(rs)}
        for k, base, _ in groups:
            row[base] = sum(counted(r, k, basis, labels) for r in rs)
        out.append(row)
    return sorted(out, key=lambda x: (-sum(x[b] for _, b, _ in groups), -x["日誌数"]))


def by_month(rows: Sequence[dict], groups: Sequence[tuple], basis: str, labels: dict) -> list[dict]:
    months = sorted({r["month"] for r in rows})
    return [{"月": m, "日誌数": sum(r["month"] == m for r in rows),
             **{base: sum(r["month"] == m and counted(r, k, basis, labels) for r in rows) for k, base, _ in groups}}
            for m in months]


def by_writer(rows: Sequence[dict], groups: Sequence[tuple], basis: str, labels: dict) -> list[dict]:
    """1件は1人ではない：記入者コードごとの件数（偏りを確かめるためだけに使う）"""
    ws = list(dict.fromkeys(r["writer_code"] or "（記入なし）" for r in rows))
    out = []
    for w in ws:
        rs = [r for r in rows if (r["writer_code"] or "（記入なし）") == w]
        k = sum(any(counted(r, g[0], basis, labels) for g in groups) for r in rs)
        out.append({"記入者": w, "件数": len(rs), "該当": k, "割合": k / len(rs) if rs else 0.0})
    return sorted(out, key=lambda x: -x["件数"])


# ============================================================
# ③ 原文を読む：KWIC と、ルールと人の判定のずれ
# ============================================================
def kwic(rows: Sequence[dict], groups: Sequence[tuple], width: int = 16) -> list[dict]:
    out = []
    for r in rows:
        for k, base, _ in groups:
            x = r["m"][k]
            for i, o in enumerate(x["occ"]):
                t = r["anon"]
                rule = (f"否定の可能性：{o['neg_word']}" if o["neg"] else
                        f"一致（例外：{o['ex_word']}）" if o["ex_word"] and o["neg_noex"] else "一致")
                out.append({"ID": r["id"], "key": k, "語": base, "日付": r["date"], "作業": r["task"],
                            "前": t[max(0, o["s"] - width):o["s"]], "一致": o["t"], "後": t[o["e"]:o["e"] + width],
                            "ルール": rule, "回目": f"{i + 1}/{x['count']}"})
    return out


def rule_accuracy(rows: Sequence[dict], groups: Sequence[tuple], labels: dict) -> dict:
    """「否定なし→困りごと、否定あり→該当せず」と読んだとき、人の判定と合う割合（例外あり・なし）"""
    n = ok = ok0 = 0
    diff = []
    for r in rows:
        for k, base, _ in groups:
            x, lab = r["m"][k], labels.get((r["id"], k))
            if not x["hit"] or lab is None:
                continue
            n += 1
            ok += int((0 if x["neg"] else 1) == lab)
            ok0 += int((0 if x["neg_noex"] else 1) == lab)
            if (0 if x["neg"] else 1) != lab:
                diff.append({"ID": r["id"], "語": base, "ずれ方": "ルールは否定、人は該当" if x["neg"] else "ルールは一致、人は該当せず",
                             "原文": r["anon"]})
    return {"n": n, "例外あり": ok, "例外なし": ok0, "ずれ": diff}


def sample_labels(preset: dict, rows: Sequence[dict]) -> dict:
    """サンプルの判定例を (ID, 語のキー) → 1/0 に。一致していない語の判定は捨てる"""
    lab = {}
    for r in rows:
        for k, v in preset["labels"].get(r["n"], {}).items():
            if k in r.get("m", {}) and r["m"][k]["hit"]:
                lab[(r["id"], k)] = int(v)
    return lab


# ============================================================
# ④ 示唆：作業ごとの割合（ベイズ）と、エージェントに任せられそうな仕事
# ============================================================
def task_bayes(rows: Sequence[dict], groups: Sequence[tuple], basis: str, labels: dict, keys: Sequence[str] | None = None,
               draws: int = 4000, seed: int = 0) -> list[dict]:
    """作業ごとの「該当する日誌の割合」を Beta(1,1) から推定。90%の幅と、ほかの作業をまとめた割合を上回る確率"""
    keys = list(keys) if keys else [g[0] for g in groups]
    hit = lambda r: any(counted(r, k, basis, labels) for k in keys)  # noqa: E731
    N, K = len(rows), sum(hit(r) for r in rows)
    rng = np.random.default_rng(seed)
    out = []
    for t in dict.fromkeys(r["task"] for r in rows):
        rs = [r for r in rows if r["task"] == t]
        n, k = len(rs), sum(hit(r) for r in rs)
        a = rng.beta(1 + k, 1 + n - k, draws)
        b = rng.beta(1 + K - k, 1 + (N - n) - (K - k), draws)
        out.append({"作業": t, "該当": k, "日誌数": n, "推定": (1 + k) / (2 + n), "下": float(np.quantile(a, 0.05)),
                    "上": float(np.quantile(a, 0.95)), "ほかより高い確率": float((a > b).mean())})
    return sorted(out, key=lambda x: -x["推定"])


AGENT_IDEAS = {
    "遅れ": ("遅れの早期通知と予定の組み直し", "遅れの記載が出た時点で後の工程（出荷・発送）の予定を組み直し、相手への連絡文を下書きする",
             "相手への送信は人が確かめてから。遅れの原因（天候・機械・人手）を分けて記録できるか試す"),
    "故障": ("故障の受付と復旧の追跡", "記載から対象の機械と日付を抜き出して故障票をつくり、業者連絡・部品待ち・復旧を状態として追う",
             "故障票の項目を現場と決める。業者への連絡文は下書きまで"),
    "人手": ("繁忙期の人員計画と応援要請の下書き", "記載が多い時期の前に作業量の見込みを出し、応援要請の文面を下書きする",
             "前年でも同じ時期に増えるか確かめる。シフトの確定は人"),
    "高い": ("値段への声の整理と、説明文の下書き", "値段に触れた感想を集め、中身・送料・体験の価値を伝える説明文を下書きする",
             "値段を変えるかは人が決める。④のMVP判定で、値段を変えた案を小さく試す"),
    "少な": ("量への声の整理と、箱の中身の見直し案", "量に触れた感想を便ごとにまとめ、家族の人数に合わせた箱の案を出す",
             "原価と収入のページで、箱を増やしたときの手取りを確かめる"),
}


def agent_ideas(rows: Sequence[dict], groups: Sequence[tuple], basis: str, labels: dict) -> list[dict]:
    """語ごとに、件数・いちばん多い作業（分母つき）と、任せられそうな仕事の候補を並べる。送信・確定は人が承認する前提。"""
    out = []
    for k, base, _ in groups:
        tb = task_bayes(rows, groups, basis, labels, keys=[k])
        c = sum(counted(r, k, basis, labels) for r in rows)
        if not c:
            continue
        top = max(tb, key=lambda x: (x["該当"], x["推定"]))
        name, what, nxt = AGENT_IDEAS.get(base, (f"「{base}」の記載の整理", f"「{base}」に触れた記載を集めて分類し、担当者に週1回まとめて知らせる", "分類の項目を現場と決める"))
        out.append({"任せられそうな仕事": name, "何をするか": what,
                    "根拠（このデータ）": f"「{base}」{c}件。いちばん多いのは{top['作業']}（{top['日誌数']}件中{top['該当']}件）",
                    "次に確かめること・人が決めること": nxt})
    return out


# ============================================================
# ⑤ 確かめて報告：生成AIの答えの照合（合計より先に内訳）と、方法｜結果｜限界
# ============================================================
def count_sub(t: str, w: str) -> int:
    return t.count(w) if w else 0


def ai_scope(rows: Sequence[dict], word: str, extra_zero: int = 3) -> list[dict]:
    hit = [r for r in rows if count_sub(r["anon"], word)]
    zero = [r for r in rows if not count_sub(r["anon"], word)][:extra_zero]
    return sorted(hit + zero, key=lambda r: r["n"])


def ai_prompt(rows: Sequence[dict], word: str) -> str:
    body = "\n".join(f"{r['id']}\t{r['anon']}" for r in rows)
    return (f"次の文（教材用の架空データ）について、「{word}」という文字列が各行に何回出てくるか数えてください。\n"
            "条件：\n1. 原文を変えずに数える。言い換えや似た意味の語は数えない。\n2. 1行に2回出たら2回と数える。\n"
            "3. 回答は「ID 回数」を1行ずつ書く（例：D001 0）。最後に、合計の回数と、1回以上出てくる行の件数を書く。\n"
            "4. プログラムを実行して数えたと確認できない場合は、「実行していない」と明記する。\n\n" + body)


def ai_mock(rows: Sequence[dict], word: str) -> str:
    """教員作成の模擬回答：2回以上の行を1つ減らし、0回の行を1にする（合計の回数はそろうが内訳がずれる例）"""
    m = {r["id"]: count_sub(r["anon"], word) for r in rows}
    two = next((i for i, v in m.items() if v >= 2), None)
    zero = next((i for i, v in m.items() if v == 0), None)
    if two and zero:
        m[two] -= 1
        m[zero] = 1
    elif zero:
        m[zero] = 1
    lines = "\n".join(f"{i} {v}" for i, v in m.items())
    return f"（教員作成の模擬回答。AIの応答ログではありません）\n{lines}\n合計 {sum(m.values())}回、{sum(v > 0 for v in m.values())}件"


def ai_compare(rows: Sequence[dict], word: str, answer: str) -> dict:
    truth = {r["id"]: count_sub(r["anon"], word) for r in rows}
    got: dict[str, int] = {}
    for m in re.finditer(r"(D\d{3})[^\d\n]{0,8}?(\d+)", answer or ""):
        if m.group(1) in truth and m.group(1) not in got:
            got[m.group(1)] = int(m.group(2))
    table = [{"ID": i, "このページ": t, "AI": got.get(i), "照合": "一致" if got.get(i) == t else ("読めない" if i not in got else "ずれ")}
             for i, t in truth.items()]
    tT, gT = sum(truth.values()), sum(got.values())
    same = sum(x["照合"] == "一致" for x in table)
    verdict = ("確認した範囲で一致" if same == len(table) else
               "合計の回数は一致しているが、内訳がずれている（誤りが打ち消し合っている）" if gT == tT else "ずれがある")
    first = max(truth, key=truth.get) if truth else None
    return {"table": sorted(table, key=lambda x: (x["照合"] == "一致", -x["このページ"])), "一致した行": same, "行数": len(table),
            "合計（AI）": gT, "合計（ページ）": tT, "件数（AI）": sum(v > 0 for v in got.values()),
            "件数（ページ）": sum(v > 0 for v in truth.values()), "判定": verdict, "最初に確かめる行": first}


def report(rows: Sequence[dict], groups: Sequence[tuple], labels: dict, preset: dict, nfkc: bool, use_syn: bool,
           sample: bool) -> str:
    """小さな分析報告（方法｜結果｜解釈の根拠｜限界）の下書き。数字は数えた結果から入れ、解釈は人が書く"""
    n = len(rows)
    unit, target = preset["unit"], preset["target"]
    dates = sorted(r["date"] for r in rows if r["date"])
    lines = []
    for k, base, _ in groups:
        hit = [r for r in rows if r["m"][k]["hit"]]
        yes = [r for r in hit if labels.get((r["id"], k)) == 1]
        lines.append((k, base, hit, sum(r["m"][k]["count"] for r in hit), yes))
    top = []
    for k, base, hit, _, yes in lines:
        if yes:
            cnt: dict[str, int] = {}
            for r in yes:
                cnt[r["task"]] = cnt.get(r["task"], 0) + 1
            t, c = max(cnt.items(), key=lambda x: x[1])
            top.append(f"「{base}」は{t}（その{preset['group_col']}の{unit}{sum(r['task'] == t for r in rows)}件中{c}件）")
    ev = [f"{yes[0]['id']}「{yes[0]['anon']}」" for _, _, _, _, yes in lines if yes][:2]
    no = [f"{r['id']}「{r['anon']}」" for k, _, hit, _, _ in lines for r in hit if labels.get((r["id"], k)) == 0][:1]
    wr = [x["件数"] for x in by_writer(rows, groups, "all", labels)]
    wtxt = f"全員{wr[0]}件で同じだが、書き方の癖は人によって違いうる" if wr and min(wr) == max(wr) else f"{min(wr, default=0)}〜{max(wr, default=0)}件"
    return (f"方法｜{'架空の' if sample else ''}{unit}{n}件（{dates[0] + '〜' + dates[-1] if dates else '期間不明'}）を対象にした。"
            f"氏名・取引先・連絡先を置換し{'、表記を NFKC でそろえた（元の文は別に保管）' if nfkc else ''}うえで、"
            f"{'・'.join('「' + b + '」' for _, b, _ in groups)}{'とその言い換え' if use_syn else ''}を部分文字列一致で検索した。"
            f"1件の{unit}に2回出ても件数は1件とし、出現回数は別に数えた。語の直後12文字（句点まで）の否定・解消の表現は目安として印を付け、"
            f"一致した{unit}は原文を読んで人が判定した。\n"
            f"結果｜{'。'.join(f'「{b}」は{occ}回、全{n}件のうち{len(hit)}件に現れた' for _, b, hit, occ, _ in lines)}。"
            f"このうち人が{target}と判定したのは{'・'.join(f'「{b}」{len(y)}件' for _, b, _, _, y in lines)}。"
            f"{'最も多いのは、' + '、'.join(top) + '。' if top else ''}\n"
            f"解釈の根拠｜{'、'.join(ev) + '。' if ev else ''}［ここに原文の言葉を引いて、自分の読みを書く］\n"
            f"限界｜{no[0] + 'のように、一致しても' + target + 'ではないものがある。' if no else ''}"
            f"件数は書いた回数であり、{target}の重さや人数ではない（記入者ごとの件数は{wtxt}）。前後関係が見えても、因果とはいえない。"
            f"{'この' + unit + 'は教材用の架空データで、実際の傾向を示すものではない。' if sample else ''}")


REPORT_CHECKS = ["回数と件数を区別した", "分母（全何件か・作業ごとの件数）を示した", "原文のIDと言葉を根拠にした",
                 "人数・重要度・因果へ読み替えていない", "前処理（匿名化・NFKC）と数え方（部分一致・否定ルール）を書いた",
                 "生成AIの利用・未使用と、自分で照合した範囲を記録した"]


def load(preset_name: str, text: str | None = None, names: Iterable[str] | None = None, orgs: Iterable[str] | None = None,
         auto: bool = True, nfkc: bool = True, use_syn: bool = False, neg: str = DEF_NEG, ex: str = DEF_EX,
         use_ex: bool = True) -> dict:
    """読み込み→匿名化→照合を一度に。text を省くとサンプル（判定例つき）"""
    p = PRESETS[preset_name]
    sample = text is None or text.strip() == p["text"].strip()
    rows, log = anonymize(parse_table(p["text"] if text is None else text), p["names"] if names is None else names,
                          p["orgs"] if orgs is None else orgs, auto=auto, nfkc=nfkc, person=p["writer"])
    analyze(rows, p["groups"], use_syn, neg, ex, use_ex)
    return {"rows": rows, "log": log, "preset": p, "sample": sample, "labels": sample_labels(p, rows) if sample else {}}


# ============================================================
# 自己チェック
# ============================================================
def _self_check() -> None:
    # 件数と回数（第6回の4件）
    occ = [match_row(t, ["故障"]) for t in ["故障", "故障、故障", "故障はなかった"]]
    assert [len(o) for o in occ] == [1, 2, 1] and [any(x["neg"] for x in o) for o in occ] == [False, False, True]
    # 例外：「かもしれない」は否定として数えない
    o = match_row("故障かもしれない。", ["故障"])[0]
    assert not o["neg"] and o["neg_noex"] and o["ex_word"] == "かもしれない"
    # 匿名化：辞書・自動・全角の電話番号（NFKC）・URL・置換済みに反応しない
    rows, log = anonymize(parse_table("日付\t作業\t記入者\t本文\n2026-05-01\t出荷\t田中\tグエンさんから電話（０９０－１１１１－２２２２）。"
                                      "https://example.com 参照。ひがし青果へ。"), names=["田中"], orgs=[])
    a = rows[0]["anon"]
    assert "グエン" not in a and "1111" not in a and "example" not in a and "ひがし青果" not in a, a
    assert rows[0]["writer_code"] == "作業者A" and rows[0]["nfkc_changed"]
    assert not residual(rows)
    assert residual([{"id": "D1", "anon": "〒123-4567 に配送"}])
    # サンプル
    for name, p in PRESETS.items():
        d = load(name)
        rs, lab = d["rows"], d["labels"]
        assert d["sample"] and len(rs) == len(parse_table(p["text"])) and lab
        assert all("作業者" in r["writer_code"] or "会員" in r["writer_code"] for r in rs)
        assert all(n not in r["anon"] for r in rs for n in p["names"] + p["orgs"]), name
        s = summary(rs, p["groups"], "all", lab)
        assert all(x["出現回数"] >= x["一致"] >= x["件数"] - 0 for x in s)
        acc = rule_accuracy(rs, p["groups"], lab)
        assert acc["n"] == len(lab) and acc["例外あり"] >= acc["例外なし"]
        tb = task_bayes(rs, p["groups"], "human", lab)
        assert all(0 <= x["下"] <= x["推定"] <= x["上"] <= 1 for x in tb)
        assert "方法｜" in report(rs, p["groups"], lab, p, True, False, True)
    d = load("作業日誌（支援先の困りごと）")
    s = {x["語"]: x for x in summary(d["rows"], d["preset"]["groups"], "all", d["labels"])}
    assert (s["遅れ"]["一致"], s["遅れ"]["出現回数"]) == (18, 20)   # 1件に3回の日誌があるので、件数と回数が違う
    # 生成AIの照合：合計はそろうが内訳がずれる模擬回答を見抜く
    sc = ai_scope(d["rows"], "遅れ")
    c = ai_compare(sc, "遅れ", ai_mock(sc, "遅れ"))
    assert c["合計（AI）"] == c["合計（ページ）"] and c["一致した行"] == c["行数"] - 2 and c["判定"].startswith("合計の回数は一致")
    assert ai_compare(sc, "遅れ", "\n".join(f"{r['id']} {count_sub(r['anon'], '遅れ')}" for r in sc))["判定"] == "確認した範囲で一致"
    print("diary_core: 自己チェック OK")


if __name__ == "__main__":
    _self_check()
