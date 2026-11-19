"""農＋X の計算部品"""
import numpy as np

import genai_core as gc
import nox_core as nx


def test_self_check():
    nx._self_check()


def test_x_lifts_the_bad_year_under_any_weather():
    farm = [s for s in nx.STREAMS if s[1] in nx.PORTFOLIOS["農だけ"]]
    for sigma, p_bad in [(0.1, 0.0), (0.25, 0.1), (0.5, 0.3)]:
        a = nx.simulate_income(farm, sigma=sigma, p_bad=p_bad)
        b = nx.simulate_income(nx.STREAMS, sigma=sigma, p_bad=p_bad)
        assert np.quantile(b, 0.05) > np.quantile(a, 0.05)


def test_weatherproof_stream_ignores_weather():
    s = [("講師", "X", 10, 1000, 0.0, 0.0, 1.0)]
    assert np.allclose(nx.simulate_income(s, fixed_cost=0, sigma=0.6, p_bad=0.4), 10_000)


def test_more_teaching_never_adds_slack():
    a = nx.slack(nx.month_load(teach_week=5), 45)
    b = nx.slack(nx.month_load(teach_week=20), 45)
    assert all(x["余白"] >= y["余白"] for x, y in zip(a, b))


def test_sns_prompt_is_clean_and_complete():
    for scene in nx.SCENES:
        for m in nx.MONTHS:
            p = gc.build_prompt(nx.sns_parts(scene, m))
            assert "【目的】" in p and "【確かめ】" in p
            assert gc.scan(p)["level"] == "緑"


def test_new_flow_gates_the_irreversible_send():
    st = gc.flow_stats(gc.FLOWS["定期便（農＋X）"])
    assert st["gates"][-1] and st["stage"] == 3


def test_kentei_gate_and_grades():
    for name, k in nx.KENTEI.items():
        n = len(k["項目"])
        assert nx.kentei_grade(name, [])["級"] == "級なし"
        assert nx.kentei_grade(name, range(1, n + 1))["級"] == "1級"
        # 1・2のどちらかが欠けると、3以降をいくつ合格しても数えない
        assert nx.kentei_grade(name, range(2, n + 1))["数"] == 1
        # 項目が増えるほど級は下がらない
        order = k["級"]
        last = 0
        for m in range(n + 1):
            i = order.index(nx.kentei_grade(name, range(1, m + 1))["級"])
            assert i >= last
            last = i


def test_scene_check_covers_every_pattern():
    import itertools
    for row in itertools.product(nx.JEED_LEVELS, repeat=3):
        assert nx.scene_check(row)
    assert nx.scene_check(["まだ", "できる", "できる"]).startswith("作業学習でまだ")
