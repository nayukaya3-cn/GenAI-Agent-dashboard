"""作業学習×生成AIで「働く入口」をつくる（entry_core.py）の部品のテスト"""
import pytest

import entry_core as ec


def test_self_check():
    ec._self_check()


@pytest.mark.parametrize("school", ec.SCHOOLS)
def test_every_field_has_school_specific_text(school):
    for f in ec.FIELDS:
        assert ec.FIELD_DETAIL[f][school]


def test_start_order_puts_missing_resources_last():
    order = ec.start_order(["備品庫・教材室", "はかり・調理台"], ec.SCHOOLS[0])
    assert [r["分野"] for r in order][-1] == "ものづくり"  # 2つ足りない
    assert order[0]["足りないもの"] == []


def test_pr_talk_uses_at_most_two_pains():
    keys = list(ec.PAINS[ec.SCHOOLS[0]])
    talk = ec.pr_talk(ec.SCHOOLS[0], keys, "食品加工")
    assert ec.PAINS[ec.SCHOOLS[0]][keys[0]][0] in talk
    assert ec.PAINS[ec.SCHOOLS[0]][keys[2]][0] not in talk
    with pytest.raises(ValueError):
        ec.pr_talk("全日制", [], "農業")


def test_manual_prompt_needs_steps():
    with pytest.raises(ValueError):
        ec.manual_prompt("農業", "播種", ["", " "], ec.SCHOOLS[1])
    assert "（ ）" not in ec.manual_prompt("農業", "播種", ["種を2粒"], ec.SCHOOLS[1], furigana=False)


def test_step_probability_narrows_with_more_records():
    few, many = ec.step_probability(4, 5), ec.step_probability(40, 50)
    assert many["上"] - many["下"] < few["上"] - few["下"]
