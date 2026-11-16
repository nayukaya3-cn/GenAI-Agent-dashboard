"""各ページが例外なく描画できるか（Streamlit の AppTest）"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted(p.name for p in (ROOT / "views").glob("*.py"))


@pytest.mark.parametrize("page", PAGES)
def test_page_runs(page, monkeypatch):
    monkeypatch.chdir(ROOT)
    at = AppTest.from_file(str(ROOT / "views" / page), default_timeout=30).run()
    assert not at.exception, at.exception


def test_app_runs(monkeypatch):
    monkeypatch.chdir(ROOT)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not at.exception, at.exception
