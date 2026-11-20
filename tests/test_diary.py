"""「X 売る」⑥ 困りごと分析の部品"""
import diary_core as dc


def test_self_check():
    dc._self_check()


def test_count_vs_occurrence_and_negation():
    rows, _ = dc.anonymize(dc.parse_table("日付\t作業\t記入者\t本文\n2026-01-01\tA\t甲\t故障\n2026-01-02\tA\t甲\t故障、故障\n2026-01-03\tB\t乙\t故障はなかった"))
    dc.analyze(rows, [("f", "故障", "")])
    s = dc.summary(rows, [("f", "故障", "")], "all", {})[0]
    assert (s["件数"], s["出現回数"], s["否定の可能性"]) == (3, 4, 1)
    assert dc.summary(rows, [("f", "故障", "")], "noneg", {})[0]["件数"] == 2


def test_no_name_or_org_survives_in_samples():
    for name, p in dc.PRESETS.items():
        d = dc.load(name)
        for r in d["rows"]:
            assert not any(w in r["anon"] for w in p["names"] + p["orgs"]), (name, r["anon"])
            assert "090-" not in r["anon"]


def test_real_data_gets_no_sample_labels():
    p = dc.PRESETS["作業日誌（支援先の困りごと）"]
    d = dc.load("作業日誌（支援先の困りごと）", text=p["text"] + "\n2026-10-01\t収穫\t佐藤\t遅れた。")
    assert not d["sample"] and d["labels"] == {}


def test_human_basis_needs_labels():
    d = dc.load("定期便の感想（お客さんの不満の芽）")
    g = d["preset"]["groups"]
    assert all(x["件数"] == 0 for x in dc.summary(d["rows"], g, "human", {}))
    assert sum(x["件数"] for x in dc.summary(d["rows"], g, "human", d["labels"])) == sum(d["labels"].values())


def test_ai_compare_catches_offsetting_errors():
    d = dc.load("作業日誌（支援先の困りごと）")
    sc = dc.ai_scope(d["rows"], "遅れ")
    c = dc.ai_compare(sc, "遅れ", dc.ai_mock(sc, "遅れ"))
    assert c["合計（AI）"] == c["合計（ページ）"] and c["一致した行"] < c["行数"]
