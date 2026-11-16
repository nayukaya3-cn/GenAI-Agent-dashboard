import genai_core as gc


def test_self_check():
    gc._self_check()


def test_scan_masks_and_never_leaks():
    r = gc.scan(gc.SAMPLE_PASTE, ["山田"])
    assert r["level"] == "赤"
    for leaked in ("082-555-0142", "taro@example.jp", "山田", "通院"):
        assert leaked not in r["masked"]


def test_scan_finds_secret_like_strings():
    assert gc.scan("api_key = sk-abcdefghijklmnop1234")["level"] == "赤"


def test_gate_rule():
    assert gc.step_verdict("エージェント", "外へ送る", True) == "手前で人が承認"
    assert gc.step_verdict("エージェント", "書きこむ", False) == "手前で人が承認"
    assert gc.step_verdict("エージェント", "読むだけ", True) == "任せてよい"
    assert gc.step_verdict("人", "外へ送る", False) == "人が行う"


def test_support_never_lowers_fit():
    base = gc.fit_matrix()
    for k in gc.SUPPORT.values():
        with_sup = gc.fit_matrix([k])
        assert all(w >= b for rw, rb in zip(with_sup, base) for w, b in zip(rw, rb))


def test_best_is_at_least_greedy_under_every_support():
    for k in [(), (0,), (2,), (0, 1, 2, 3, 4)]:
        m = gc.fit_matrix(k)
        assert gc.best_assignment(m)[1] >= gc.greedy_assignment(m)[1]
