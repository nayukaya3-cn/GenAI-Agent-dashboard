"""3d-print-board（3Dプリンター業務推進ボード）の初期データと画面の定義が食い違っていないかを確かめる。

seed.json を学校用に書きかえたときや、index.html の AREAS・STATUS などを増やしたときに、
読み込んでも表示されない値（例：存在しない分野名）が混ざるのを防ぐ。
"""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "3d-print-board"
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SEED = json.loads((ROOT / "data" / "seed.json").read_text(encoding="utf-8"))


def js_list(name):
    """index.html の const NAME=['a','b',…]; を取り出す"""
    m = re.search(rf"const {name}=\[([^\]]*)\];", HTML)
    assert m, f"{name} が index.html に見つかりません"
    return re.findall(r"'([^']*)'", m.group(1))


def test_html_basics():
    assert HTML.startswith("<!DOCTYPE html>")
    assert "<title>3Dプリンター業務推進ボード</title>" in HTML
    assert len(re.findall(r"^const ITEMS=\[", HTML, re.M)) == 1


def test_seed_lists_exist():
    for key in ["tasks", "models", "partners", "events", "students", "evals"]:
        assert isinstance(SEED.get(key), list), key


def test_seed_values_match_html_choices():
    areas, status = set(js_list("AREAS")), set(js_list("STATUS"))
    kinds, mstate, pstatus = set(js_list("KINDS")), set(js_list("MSTATE")), set(js_list("PSTATUS"))
    for t in SEED["tasks"]:
        assert t["area"] in areas, t
        assert t["status"] in status, t
        assert int(t["stage"]) in range(0, 5), t
    for m in SEED["models"]:
        assert m["kind"] in kinds, m
        assert m["state"] in mstate, m
        assert m["food"] is False, f"食品に直接触れる造形物は初期データに入れない: {m['name']}"
    for p in SEED["partners"]:
        assert p["status"] in pstatus, p
        assert p["src"] == "" or p["src"].startswith("https://"), p


def test_seed_dates_and_ids():
    ids = [x["id"] for k in ["tasks", "models", "partners", "events"] for x in SEED[k]]
    assert len(ids) == len(set(ids)), "id が重複しています"
    for e in SEED["events"]:
        date.fromisoformat(e["date"])
    for t in SEED["tasks"]:
        if t.get("due"):
            date.fromisoformat(t["due"])


def test_no_student_records_in_seed():
    # 公開リポジトリなので、生徒の記録は初期データに入れない
    assert SEED["students"] == [] and SEED["evals"] == []
