"""「X 売る」ページの ⑥ Instagram に投稿する（画面部分）

設定は Streamlit の Secrets（.streamlit/secrets.toml、またはCommunity Cloud の Settings → Secrets）に置く：
    [instagram]
    access_token    = "IGAA..."     # Instagram ユーザーの長期アクセストークン（60日で切れる）
    passcode        = "合言葉"        # 投稿ボタンを押せる人を本人に限る
    public_base_url = "https://genai-agent-dashboard-e5xwcfhek9efndwczfb9k9.streamlit.app"
    # user_id     = "1784..."      # 省略可（/me から自動で取る）
    # api_version = "v26.0"        # 省略可
設定がなければ、本文と画像をダウンロードして手で投稿する道だけを出す。
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

import genai_core as gc
import insta_core as ig
import nox_core as nx
import ui

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_FAILS = 5   # 合言葉をまちがえてよい回数（この画面を開いている間）
CHECKS = [
    "生徒・利用者・支援先の人の顔や名前、名札、車のナンバーが写っていない（写っているなら、本人・保護者・学校の同意がある）",
    "支援先の法人の顧客・売上・従業員の情報を書いていない",
    "数字・日付・値段を、元の記録と照らした",
    "家の場所が特定される風景（住所が分かる看板・表札など）が写っていない",
]


def _config() -> dict:
    try:
        return dict(st.secrets.get("instagram", {}))
    except Exception:  # noqa: BLE001  secrets.toml が無いとき
        return {}


def _setup_guide() -> None:
    with st.expander("Instagram 投稿の設定のしかた（最初に1回だけ）"):
        st.markdown(
            "1. Instagram のアカウントを **プロアカウント（ビジネスまたはクリエイター）** に切りかえる（個人アカウントにはAPIで投稿できません）。\n"
            "2. [Meta for Developers](https://developers.facebook.com/apps/) でアプリをつくり、**Instagram → Instagram ログインによるAPI設定** を追加する。\n"
            "3. 権限 `instagram_business_basic` と `instagram_business_content_publish` で自分のアカウントをつなぎ、**長期アクセストークン** を発行する（60日で切れます）。\n"
            "4. Streamlit Community Cloud の **App settings → Secrets** に、次を貼って保存する。")
        st.code('[instagram]\naccess_token    = "IGAA...（発行したトークン）"\npasscode        = "自分だけが知る合言葉"\n'
                'public_base_url = "https://genai-agent-dashboard-e5xwcfhek9efndwczfb9k9.streamlit.app"', language="toml")
        st.markdown("5. このページを開きなおし、下の **接続を確かめる** でアカウント名が出れば完了です。\n\n"
                    "トークンを延ばすとき（60日以内に）：`curl \"https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=今のトークン\"` で出た新しいトークンを Secrets に貼りかえる。")
        st.caption("トークンと合言葉は GitHub に入れません（.streamlit/secrets.toml は .gitignore 済み）。")


def section(scene: str, farm_name: str, month: str) -> None:
    st.subheader("⑥ Instagram に投稿する")
    st.write("②の質問文で生成AIにつくらせた案を、自分の言葉に直してから投稿します。写真は位置情報（EXIF）を消し、Instagram の縦横比に合わせてから送ります。")
    cfg = _config()
    ready = bool(cfg.get("access_token") and cfg.get("passcode") and cfg.get("public_base_url"))
    row = next(r for r in nx.STORY if r[0] == month)

    left, right = st.columns([1, 1])
    with left:
        draft = ig.draft_body(row, farm_name)
        if st.session_state.get("ig_draft_src") != (month, farm_name):
            st.session_state["ig_body"] = draft
            st.session_state["ig_draft_src"] = (month, farm_name)
        body = st.text_area("本文", key="ig_body", height=190, help="②の「今月」と①の呼び名から下書きをつくっています。")
        tags = ig.normalize_tags(st.text_input("ハッシュタグ（空白か読点で区切る）", " ".join(ig.DEFAULT_TAGS), key="ig_tags"))
        src = st.radio("画像", ["写真をアップロード", "公開済みの画像URL（JPEG）"], horizontal=True, key="ig_src")
        jpeg, image_url, note = None, "", {}
        if src == "写真をアップロード":
            up = st.file_uploader("写真（JPEG・PNG・WebP）", type=["jpg", "jpeg", "png", "webp"], key="ig_file")
            if up is not None:
                try:
                    jpeg, note = ig.prepare_jpeg(up.getvalue())
                except Exception:  # noqa: BLE001
                    st.error("この画像は読みこめませんでした。JPEGかPNGで書き出してからためしてください。")
        else:
            image_url = st.text_input("画像のURL", key="ig_url", placeholder="https://.../photo.jpg")
        alt = st.text_input("代替テキスト（画像の説明・目の不自由な人の読み上げ用）", key="ig_alt",
                            placeholder="例：朝の食卓に、自家製小麦のパンと豆のスープ")
        ai_made = st.checkbox("画像を生成AIでつくった（「AI情報」ラベルをつける）", key="ig_ai")

    caption = ig.build_caption(body, tags)
    problems = (["本文の「（ここに、今日の畑の様子を1〜3文で）」を、自分の言葉に書きかえてください。"] if "（ここに" in body else [])
    problems += ig.check_caption(caption) + (ig.check_image_url(image_url) if src != "写真をアップロード" and image_url else [])
    chk = gc.scan(caption)
    with right:
        st.markdown("**プレビュー**")
        with st.container(border=True):
            if jpeg:
                st.image(jpeg, width="stretch")
            elif image_url and not ig.check_image_url(image_url):
                st.image(image_url, width="stretch")
            else:
                st.caption("（画像を選ぶとここに出ます）")
            st.text(caption)
        st.caption(f"{len(caption)} / {ig.CAPTION_MAX} 字　・　ハッシュタグ {len(tags)} / {ig.HASHTAG_MAX} 個"
                   + (f"　・　{note.get('投稿するサイズ', '')}" if note else ""))
        if note.get("切りとり"):
            st.caption(note["切りとり"])
        st.caption(f"投稿前の点検：{ui.LIGHT_ICON[chk['level']]} {gc.LIGHT_MESSAGE[chk['level']]}")
        if chk["found"]:
            st.caption("見つけたもの：" + "、".join(sorted({f'{k}「{w}」' for _, k, w in chk["found"]})))

    st.markdown("**公開する前に（すべて確かめたらチェック）**")
    checked = all([st.checkbox(c, key=f"ig_chk{i}") for i, c in enumerate(CHECKS)])
    for p in problems:
        st.warning(p)
    has_image = bool(jpeg) or bool(image_url and not ig.check_image_url(image_url))
    can_post = checked and has_image and not problems and chk["level"] != "赤"
    if chk["level"] == "赤":
        st.error("本文に個人情報・配慮の情報らしい語があります。消してから投稿してください。")

    if not ready:
        st.info("この公開アプリには、まだ Instagram の接続が設定されていません。いまは、本文と画像をダウンロードして、スマホの Instagram から手で投稿できます。")
    c1, c2, c3 = st.columns(3)
    c1.download_button("本文をダウンロード", caption.encode("utf-8"), "instagram_caption.txt", "text/plain",
                       width="stretch", key="ig_dl_txt")
    if jpeg:
        c2.download_button("画像をダウンロード（位置情報なし）", jpeg, "instagram_photo.jpg", "image/jpeg",
                           width="stretch", key="ig_dl_img")
    c3.link_button("Instagram を開く", "https://www.instagram.com/", width="stretch")
    _setup_guide()
    if not ready:
        return

    # ---- 本人だけが押せる投稿ボタン ----
    st.markdown("**アプリから直接投稿する（本人のみ）**")
    fails = st.session_state.get("ig_fails", 0)
    if fails >= MAX_FAILS:
        st.error("合言葉を続けてまちがえたため、この画面からの投稿を止めました。ページを開きなおしてください。")
        return
    code = st.text_input("合言葉", type="password", key="ig_pass")
    client = ig.Client(cfg["access_token"], cfg.get("user_id", ""), cfg.get("api_version", ig.DEFAULT_VERSION))
    b1, b2 = st.columns(2)
    if b1.button("接続を確かめる", width="stretch", key="ig_test", disabled=not code):
        if not ig.passcode_ok(code, cfg["passcode"]):
            st.session_state["ig_fails"] = fails + 1
            st.error("合言葉がちがいます。")
        else:
            try:
                me = client.me()
                used = client.publishing_limit()
                st.success(f"@{me.get('username', '?')} につながっています。この24時間の投稿：{used} / {ig.DAILY_LIMIT}")
            except ig.InstagramError as e:
                st.error(f"接続できませんでした：{e}")
    if b2.button("📸 Instagram に投稿する", type="primary", width="stretch", key="ig_post",
                 disabled=not (code and can_post)):
        if not ig.passcode_ok(code, cfg["passcode"]):
            st.session_state["ig_fails"] = fails + 1
            st.error("合言葉がちがいます。")
            return
        path = None
        with st.status("投稿しています…", expanded=True) as status:
            try:
                ig.cleanup(STATIC_DIR)
                url = image_url
                if jpeg:
                    path, url = ig.save_public(jpeg, STATIC_DIR, cfg["public_base_url"])
                res = client.post_image(url, caption, alt, ai_made, on_step=st.write)
                status.update(label="投稿しました", state="complete")
                st.success("Instagram に公開しました。" + (f" [投稿を開く]({res['permalink']})" if res.get("permalink") else ""))
            except ig.InstagramError as e:
                status.update(label="投稿できませんでした", state="error")
                st.error(str(e))
            except OSError:
                status.update(label="投稿できませんでした", state="error")
                st.error("画像を公開用に置けませんでした。「公開済みの画像URL」でためしてください。")
            finally:
                if path is not None:
                    path.unlink(missing_ok=True)
    if not can_post:
        st.caption("投稿ボタンは、画像を選び、本文の点検が赤でなく、4つの確認にすべてチェックすると押せます。")
