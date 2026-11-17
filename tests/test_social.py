"""Facebook・LinkedIn のボタン"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

import social as sn

ROOT = Path(__file__).resolve().parents[1]


def test_urls_point_to_the_author_not_the_viewer():
    assert sn.FACEBOOK_URL.startswith("https://www.facebook.com/")
    assert sn.LINKEDIN_URL.startswith("https://www.linkedin.com/in/")
    assert "/feed" not in sn.LINKEDIN_URL      # /feed/ は開いた人自身のフィードになる


def _labels(at):
    return [b.proto.label for b in at.get("link_button")]


def test_sidebar_shows_both_buttons(monkeypatch):
    monkeypatch.chdir(ROOT)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not at.exception, at.exception
    labels = _labels(at)
    assert "📘 Facebookで活動内容を見る" in labels and "💼 LinkedInで活動内容を見る" in labels


def test_overview_has_contact_buttons(monkeypatch):
    monkeypatch.chdir(ROOT)
    at = AppTest.from_file(str(ROOT / "views" / "overview.py"), default_timeout=30).run()
    assert not at.exception, at.exception
    assert "📘 Facebookで声をかける" in _labels(at)
