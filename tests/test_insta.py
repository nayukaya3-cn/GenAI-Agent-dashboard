"""Instagram 投稿の部品（ネットワークには出ない。API は偽物で置きかえる）"""
import io
import json
import urllib.error
import urllib.parse
from pathlib import Path

import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

import insta_core as ig

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "IGAA-secret-token"


def test_self_check():
    ig._self_check()


class FakeRes(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeAPI:
    """呼ばれた順に (method, path, params, headers) を記録し、決めた答えを返す"""

    def __init__(self, status=("IN_PROGRESS", "FINISHED"), fail_publish=False):
        self.calls, self.status, self.fail_publish = [], list(status), fail_publish

    def __call__(self, req, timeout=30):
        u = urllib.parse.urlparse(req.full_url)
        path = u.path.split("/", 2)[2]
        params = dict(urllib.parse.parse_qsl(u.query or (req.data or b"").decode()))
        self.calls.append((req.get_method(), path, params, dict(req.header_items()), req.full_url))
        if path == "me":
            body = {"user_id": "1784", "username": "test_farm"}
        elif path == "1784/media":
            body = {"id": "C1"}
        elif path == "C1":
            body = {"status_code": self.status.pop(0)}
        elif path == "1784/media_publish":
            if self.fail_publish:
                err = json.dumps({"error": {"message": f"bad token {TOKEN}"}}).encode()
                raise urllib.error.HTTPError(req.full_url, 400, "Bad", {}, io.BytesIO(err))
            body = {"id": "M1"}
        elif path == "M1":
            body = {"permalink": "https://www.instagram.com/p/xyz/"}
        else:
            body = {"data": [{"quota_usage": 3}]}
        return FakeRes(json.dumps(body).encode())


def client(api):
    return ig.Client(TOKEN, opener=api, sleep=lambda s: None)


def test_post_flow_in_two_steps_and_token_only_in_header():
    api = FakeAPI()
    res = client(api).post_image("https://x.example/a.jpg", "朝の畑\n\n#麦", alt_text="麦畑", ai_generated=True)
    assert res == {"id": "M1", "permalink": "https://www.instagram.com/p/xyz/"}
    paths = [c[1] for c in api.calls]
    assert paths == ["me", "1784/media", "C1", "C1", "1784/media_publish", "M1"]
    media = api.calls[1][2]
    assert media["image_url"] == "https://x.example/a.jpg" and media["alt_text"] == "麦畑" and media["is_ai_generated"] == "true"
    assert api.calls[4][2] == {"creation_id": "C1"}
    for method, _, params, headers, url in api.calls:
        assert TOKEN not in url and TOKEN not in json.dumps(params)
        assert headers["Authorization"] == f"Bearer {TOKEN}"


def test_ai_flag_is_not_sent_unless_checked():
    api = FakeAPI()
    client(api).post_image("https://x.example/a.jpg", "本文")
    assert "is_ai_generated" not in api.calls[1][2]


def test_container_error_stops_before_publish():
    api = FakeAPI(status=("ERROR",))
    with pytest.raises(ig.InstagramError, match="ERROR"):
        client(api).post_image("https://x.example/a.jpg", "本文")
    assert "1784/media_publish" not in [c[1] for c in api.calls]


def test_api_error_message_hides_token():
    with pytest.raises(ig.InstagramError) as e:
        client(FakeAPI(fail_publish=True)).post_image("https://x.example/a.jpg", "本文")
    assert TOKEN not in str(e.value) and "***" in str(e.value)


def test_bad_inputs_are_refused_before_any_call():
    api = FakeAPI()
    with pytest.raises(ig.InstagramError):
        client(api).post_image("http://x.example/a.png", "")
    assert api.calls == []


def _photo(w, h, gps=True):
    im = Image.new("RGB", (w, h), (200, 180, 90))
    buf = io.BytesIO()
    exif = Image.Exif()
    if gps:
        exif[0x8825] = {1: "N", 2: (34.0, 24.0, 0.0)}   # GPSInfo
        exif[0x010F] = "PhoneMaker"
    im.save(buf, "JPEG", exif=exif)
    return buf.getvalue()


@pytest.mark.parametrize("w,h", [(1000, 3000), (4000, 1000), (3000, 3000)])
def test_prepare_jpeg_fits_ratio_and_size_and_drops_exif(w, h):
    out, note = ig.prepare_jpeg(_photo(w, h))
    im = Image.open(io.BytesIO(out))
    r = im.size[0] / im.size[1]
    assert ig.RATIO_MIN - 0.01 <= r <= ig.RATIO_MAX + 0.01
    assert max(im.size) <= ig.LONG_EDGE
    assert len(im.getexif()) == 0


def test_save_public_and_cleanup(tmp_path):
    path, url = ig.save_public(b"jpeg", tmp_path, "https://app.example/")
    assert path.exists() and url == f"https://app.example/app/static/ig/{path.name}"
    assert ig.cleanup(tmp_path, max_age_hours=-1) == 1 and not path.exists()


def test_market_page_without_secrets_shows_manual_route(monkeypatch):
    monkeypatch.chdir(ROOT)
    at = AppTest.from_file(str(ROOT / "views" / "nox_market.py"), default_timeout=30).run()
    assert not at.exception
    assert not [b for b in at.button if b.key == "ig_post"]
    assert any("まだ Instagram の接続が設定されていません" in i.value for i in at.info)


def test_market_page_with_secrets_locks_post_button(monkeypatch):
    monkeypatch.chdir(ROOT)
    at = AppTest.from_file(str(ROOT / "views" / "nox_market.py"), default_timeout=30)
    at.secrets["instagram"] = {"access_token": TOKEN, "passcode": "mugi", "public_base_url": "https://app.example"}
    at.run()
    assert not at.exception
    post = next(b for b in at.button if b.key == "ig_post")
    assert post.disabled   # 画像・確認・合言葉がそろうまで押せない
    at.text_input(key="ig_pass").set_value("wrong").run()
    at.button(key="ig_test").click().run()
    assert any("合言葉がちがいます" in e.value for e in at.error)
    assert at.session_state["ig_fails"] == 1
