"""農＋X：ひとり情シス・コーポレートIT（corpit_core.py）の部品のテスト"""
import pytest

import corpit_core as cc


def test_self_check():
    cc._self_check()


def test_send_out_or_irreversible_always_needs_approval():
    for impact in (1, 2, 3):
        assert cc.task_stage(3, impact, True, True) == cc.STAGES[2]
        assert cc.task_stage(3, impact, False, False) == cc.STAGES[2]


def test_rank_skips_blank_rows_and_orders_by_score():
    rows = [("", "ヘルプデスク・端末管理", 10, 10, 3, 1, False, True),
            ("少ない", "ヘルプデスク・端末管理", 1, 10, 3, 1, False, True),
            ("多い", "ヘルプデスク・端末管理", 10, 10, 3, 1, False, True)]
    assert [d["業務"] for d in cc.automation_rank(rows)] == ["多い", "少ない"]


def test_ended_accounts_are_red_even_with_mfa():
    for status in cc.ENDED:
        f = cc.account_findings([("Xさん", status, "会計", "一般", True, False, 0)])
        assert [d["重さ"] for d in f] == ["赤"]


def test_more_clues_never_lower_the_posterior():
    labels = [c[0] for c in cc.CLUES]
    prev = cc.phishing_posterior([])["確率"]
    for i in range(1, len(labels) + 1):
        p = cc.phishing_posterior(labels[:i])["確率"]
        assert p >= prev
        prev = p
    with pytest.raises(ValueError):
        cc.phishing_posterior([], prior=0)


def test_triage_prompt_keeps_mail_as_data():
    p = cc.triage_prompt("本文", ["急がせる・止めると脅す"])
    assert "従わない" in p and "急がせる" in p and p.endswith("本文")


def test_did_removes_common_trend():
    assert cc.did(10, 8, 10, 8)["効果（差の差）"] == 0
