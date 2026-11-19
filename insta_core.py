"""
Instagram への投稿（Instagram API with Instagram Login）— Streamlit 非依存の部品

投稿は2段階：
  1. POST /{IG_ID}/media          … 画像の公開URLと本文から「下書き（コンテナ）」をつくる
  2. POST /{IG_ID}/media_publish  … 下書きを公開する
画像は Instagram 側が URL から取りにくるため、公開URL（https・JPEG）が要る。
アップロードした写真は、位置情報（EXIF）を消してから static/ig/ に置き、Streamlit の静的配信で公開URLにする。
アクセストークンは URL に載せず、Authorization ヘッダーで送る（ログやエラー文にトークンが残らないように）。

自己チェック： python insta_core.py
"""
from __future__ import annotations

import hmac
import io
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Callable

API_HOST = "https://graph.instagram.com"
DEFAULT_VERSION = "v26.0"
CAPTION_MAX = 2200          # 本文の上限（文字）
HASHTAG_MAX = 30            # ハッシュタグの上限（個）
DAILY_LIMIT = 50            # 24時間に公開できる投稿数
RATIO_MIN, RATIO_MAX = 4 / 5, 1.91   # 画像の縦横比（横÷縦）の許容範囲
LONG_EDGE = 1440            # 長い辺をこの長さ以下に縮める
DEFAULT_TAGS = ["農プラスX", "畑のある暮らし", "パン用小麦", "輪作", "広島の農業"]
STATIC_SUBDIR = "ig"        # static/ig/ に投稿用の画像を一時的に置く


class InstagramError(Exception):
    """Instagram API が失敗を返したとき（メッセージにトークンは含めない）"""


# ---------- 本文・ハッシュタグ ----------
def normalize_tags(text: str | list[str]) -> list[str]:
    """「#麦 ＃大豆、輪作」→ ['麦', '大豆', '輪作']。記号・空白を除き、重複を消す。"""
    items = text if isinstance(text, list) else re.split(r"[\s,、，]+", unicodedata.normalize("NFKC", text or ""))
    out: list[str] = []
    for t in items:
        t = re.sub(r"[^\w]", "", unicodedata.normalize("NFKC", t).lstrip("#"))
        if t and t not in out:
            out.append(t)
    return out


def build_caption(body: str, tags: list[str]) -> str:
    body = (body or "").strip()
    tag_line = " ".join(f"#{t}" for t in tags)
    return f"{body}\n\n{tag_line}".strip() if tag_line else body


def check_caption(caption: str) -> list[str]:
    """投稿できない理由のリスト（空なら投稿できる）"""
    problems = []
    if not caption.strip():
        problems.append("本文が空です。")
    if len(caption) > CAPTION_MAX:
        problems.append(f"本文が長すぎます（{len(caption)}字／上限 {CAPTION_MAX}字）。")
    n = len(re.findall(r"#\w+", caption))
    if n > HASHTAG_MAX:
        problems.append(f"ハッシュタグが多すぎます（{n}個／上限 {HASHTAG_MAX}個）。")
    return problems


def check_image_url(url: str) -> list[str]:
    u = urllib.parse.urlparse((url or "").strip())
    problems = []
    if u.scheme != "https" or not u.netloc:
        problems.append("画像のURLは https:// で始まる公開URLにしてください。")
    if not u.path.lower().endswith((".jpg", ".jpeg")):
        problems.append("画像はJPEG（.jpg / .jpeg）にしてください。")
    return problems


def passcode_ok(given: str, expected: str) -> bool:
    return bool(expected) and hmac.compare_digest((given or "").encode(), expected.encode())


# ---------- 画像 ----------
def prepare_jpeg(data: bytes) -> tuple[bytes, dict]:
    """写真を投稿できる形にする：向きを直す→縦横比を範囲内に切る→縮める→EXIF（位置情報など）を消してJPEGに。"""
    from PIL import Image, ImageOps

    im = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    w, h = im.size
    note = {"元のサイズ": f"{w}×{h}"}
    r = w / h
    if r < RATIO_MIN:            # 縦に長すぎる → 上下を切る
        nh = round(w / RATIO_MIN)
        top = (h - nh) // 2
        im = im.crop((0, top, w, top + nh))
        note["切りとり"] = "縦に長いので上下を切りました（4:5）"
    elif r > RATIO_MAX:          # 横に長すぎる → 左右を切る
        nw = round(h * RATIO_MAX)
        left = (w - nw) // 2
        im = im.crop((left, 0, left + nw, h))
        note["切りとり"] = "横に長いので左右を切りました（1.91:1）"
    im.thumbnail((LONG_EDGE, LONG_EDGE))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88, optimize=True)   # exif を渡さない＝位置情報は残らない
    note["投稿するサイズ"] = f"{im.size[0]}×{im.size[1]}"
    return buf.getvalue(), note


def save_public(jpeg: bytes, static_dir: str | Path, base_url: str) -> tuple[Path, str]:
    """static/ig/ に推測されにくい名前で保存し、(ファイルの場所, 公開URL) を返す"""
    d = Path(static_dir) / STATIC_SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.jpg"
    path = d / name
    path.write_bytes(jpeg)
    return path, f"{base_url.rstrip('/')}/app/static/{STATIC_SUBDIR}/{name}"


def cleanup(static_dir: str | Path, max_age_hours: float = 24) -> int:
    """古い投稿用画像を消す（消した数を返す）"""
    d = Path(static_dir) / STATIC_SUBDIR
    if not d.exists():
        return 0
    now, n = time.time(), 0
    for p in d.glob("*.jpg"):
        if now - p.stat().st_mtime > max_age_hours * 3600:
            p.unlink(missing_ok=True)
            n += 1
    return n


# ---------- API ----------
class Client:
    def __init__(self, token: str, user_id: str = "", version: str = DEFAULT_VERSION,
                 opener: Callable | None = None, sleep: Callable[[float], None] = time.sleep, timeout: float = 30):
        if not token:
            raise InstagramError("アクセストークンが設定されていません。")
        self._token, self.user_id, self.version = token, str(user_id or ""), version or DEFAULT_VERSION
        self._open = opener or urllib.request.urlopen
        self._sleep, self._timeout = sleep, timeout

    def _call(self, method: str, path: str, params: dict | None = None) -> dict:
        params = {k: v for k, v in (params or {}).items() if v not in (None, "")}
        url = f"{API_HOST}/{self.version}/{path.lstrip('/')}"
        data = None
        if method == "GET" and params:
            url += "?" + urllib.parse.urlencode(params)
        elif method == "POST":
            data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data, method=method,
                                     headers={"Authorization": f"Bearer {self._token}"})
        try:
            with self._open(req, timeout=self._timeout) as res:
                return json.loads(res.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode()).get("error", {})
                msg = err.get("error_user_msg") or err.get("message") or str(e)
            except Exception:  # noqa: BLE001
                msg = f"HTTP {e.code}"
            raise InstagramError(msg.replace(self._token, "***")) from None
        except urllib.error.URLError as e:
            raise InstagramError(f"Instagram に接続できませんでした（{e.reason}）") from None

    def me(self) -> dict:
        info = self._call("GET", "me", {"fields": "user_id,username"})
        if not self.user_id and info.get("user_id"):
            self.user_id = str(info["user_id"])
        return info

    def _uid(self) -> str:
        if not self.user_id:
            self.me()
        if not self.user_id:
            raise InstagramError("Instagram のユーザーIDが分かりませんでした。")
        return self.user_id

    def publishing_limit(self) -> int:
        """この24時間に公開した数"""
        r = self._call("GET", f"{self._uid()}/content_publishing_limit", {"fields": "quota_usage"})
        rows = r.get("data") or [{}]
        return int(rows[0].get("quota_usage", 0))

    def create_container(self, image_url: str, caption: str, alt_text: str = "", ai_generated: bool = False) -> str:
        params = {"image_url": image_url, "caption": caption, "alt_text": alt_text}
        if ai_generated:
            params["is_ai_generated"] = "true"
        r = self._call("POST", f"{self._uid()}/media", params)
        if "id" not in r:
            raise InstagramError("下書き（コンテナ）をつくれませんでした。")
        return str(r["id"])

    def wait_ready(self, container_id: str, tries: int = 10, interval: float = 3) -> None:
        for _ in range(tries):
            code = self._call("GET", container_id, {"fields": "status_code"}).get("status_code", "")
            if code in ("FINISHED", "PUBLISHED"):
                return
            if code in ("ERROR", "EXPIRED"):
                raise InstagramError(f"Instagram 側で画像の取りこみに失敗しました（{code}）。画像のURLが公開されているか確かめてください。")
            self._sleep(interval)
        raise InstagramError("Instagram 側の準備が時間内に終わりませんでした。少し待ってからもう一度ためしてください。")

    def publish(self, container_id: str) -> str:
        r = self._call("POST", f"{self._uid()}/media_publish", {"creation_id": container_id})
        if "id" not in r:
            raise InstagramError("公開できませんでした。")
        return str(r["id"])

    def permalink(self, media_id: str) -> str:
        return self._call("GET", media_id, {"fields": "permalink"}).get("permalink", "")

    def post_image(self, image_url: str, caption: str, alt_text: str = "", ai_generated: bool = False,
                   on_step: Callable[[str], None] = lambda s: None) -> dict:
        problems = check_caption(caption) + check_image_url(image_url)
        if problems:
            raise InstagramError(" ".join(problems))
        on_step("アカウントを確かめています")
        self._uid()
        on_step("下書き（コンテナ）をつくっています")
        cid = self.create_container(image_url, caption, alt_text, ai_generated)
        on_step("Instagram が画像を取りこむのを待っています")
        self.wait_ready(cid)
        on_step("公開しています")
        mid = self.publish(cid)
        link = ""
        try:
            link = self.permalink(mid)
        except InstagramError:
            pass
        return {"id": mid, "permalink": link}


def draft_body(story_row: tuple, farm_name: str) -> str:
    """発信カレンダーの1行から、本文の下書きをつくる（例。自分の言葉に書きかえて使う）"""
    month, field, topic, offer, _ = story_row
    return (f"{month}の畑は「{field}」。\n"
            f"今月のテーマは「{topic}」です。\n\n"
            f"（ここに、今日の畑の様子を1〜3文で）\n\n"
            f"{farm_name}より。{offer}のご案内は、プロフィールのリンクから。")


def _self_check() -> None:
    assert normalize_tags("#麦 ＃大豆、輪作 麦 #パン-用") == ["麦", "大豆", "輪作", "パン用"]
    assert build_caption("本文", ["a", "b"]) == "本文\n\n#a #b"
    assert check_caption("x" * 2201) and not check_caption("ok #a")
    assert check_image_url("http://x/a.png") and not check_image_url("https://x.example/a.JPG")
    assert passcode_ok("abc", "abc") and not passcode_ok("abc", "") and not passcode_ok("ab", "abc")
    print("insta_core: ok")


if __name__ == "__main__":
    _self_check()
