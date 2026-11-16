"""仮想研究事例（agri_case.py）の部品と、研究ページの鍵"""
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

import agri_case as ac

ROOT = Path(__file__).resolve().parents[1]
KEY = "CASE_STUDY_PASSWORD"


def test_self_check():
    ac._self_check()


def test_committed_data_is_reproducible():
    fresh, saved = ac.make_data(), ac.load()
    for k in ac.FILES:
        pd.testing.assert_frame_equal(fresh[k].astype(str), saved[k].astype(str))


def test_negation_is_not_counted_as_trouble():
    for text in ("遅れなし。順調。", "機械の故障はなかった。", "人手は足りた。"):
        assert ac.classify(text) == ""
    assert ac.classify("収穫の人手が足りず、残業になった。") == "身体作業型"


def test_approval_cannot_be_skipped_under_constraint():
    prm = ac.week_params(1.0, 0.4)
    sol = ac.solve_week(0.3, prm)
    assert all(mode != 3 for _, mode in sol["acts"])
    free = ac.solve_week(0.3, prm, constrained=False)
    assert free["expected_loss"] <= sol["expected_loss"]


def test_adjustment_recovers_true_effect_better_than_naive():
    eff = ac.effect_summary(ac.load()["abab"])
    assert abs(eff["hb_adjusted"]["mu"] - ac.TRUE["mu"]) < abs(eff["hb_naive"]["mu"] - ac.TRUE["mu"])
    assert eff["hb_adjusted"]["mu_hi"] < 0 < eff["hb_naive"]["mu_hi"]


def test_guardrails_never_shrink_the_best_delegation_level():
    for shock in ac.SHOCKS:
        best = [ac.best_level(ac.delegation_sweep(g, 0.19, 0.2, shock)) for g in (0.0, 0.5, 1.0)]
        assert best == sorted(best)


def _page(monkeypatch, secret=None):
    monkeypatch.chdir(ROOT)
    monkeypatch.delenv(KEY, raising=False)
    at = AppTest.from_file(str(ROOT / "views" / "case_study.py"), default_timeout=120)
    if secret:
        at.secrets[KEY] = secret
    return at


def test_case_page_shows_nothing_without_secret(monkeypatch):
    at = _page(monkeypatch).run()
    assert not at.exception and not at.tabs and not at.text_input


def test_case_page_stays_locked_on_wrong_password(monkeypatch):
    at = _page(monkeypatch, "correct-horse").run()
    at.text_input[0].set_value("wrong").run()
    assert not at.exception and not at.tabs and at.error


def test_case_page_opens_with_password(monkeypatch):
    at = _page(monkeypatch, "correct-horse").run()
    assert not at.tabs
    at.text_input[0].set_value("correct-horse").run()
    assert not at.exception, at.exception
    assert len(at.tabs) == 6 and at.metric


def test_menu_hides_case_page_without_secret(monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.delenv(KEY, raising=False)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not at.exception, at.exception
