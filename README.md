# 「農＋X」ライフスタイル × 生成AI ダッシュボード

**農産物そのもの（モノ）を主役にせず、その農産物が生まれる背景にある「心地よい暮らし方や価値観」を商品にする。**
第一歩は、畑の風景・食卓の風景（例：自家製小麦のパンと豆のスープがある朝の食卓）をパッケージにし、
小さな定期便や体験イベントからファンと直接つながること。その設計を、時間・収入・立ち上げの3つの壁とあわせて数で確かめる画面です。

- **農**：パン用小麦 🔁 枝豆・大豆（＋ハウスの野菜）の輪作、食品加工（製粉・パン生地・味噌）
- **X**：教える（支援学校の作業学習、定時制・通信制の「科学と人間生活」）／支える（農業法人・農業関連企業へのマーケティング支援）

## 農＋X ライフスタイル（メイン）

| ページ | ファイル | できること |
|---|---|---|
| 農＋X | `views/nox_home.py` | モノから暮らしの風景へ、の整理。レジリエンスの3点、3つの原則、はじめの一歩、人手と関係人口 |
| 農 | `views/nox_rotation.py` | ブロック輪作の一年。農・加工・X（講師・支援・発信・体験）の月別時間を重ね、余白を見る |
| 収入 | `views/nox_portfolio.py` | 収入の柱を組み合わせ、天候・不作・契約の成否を1万年分引いて「悪い年（下位5%）」の手取りを比べる |
| X 売る | `views/nox_market.py` | 風景パッケージの設計、発信カレンダー→生成AIに貼る質問文、ファンの育ち方とLTV、MVPのベイズ判定、農業法人への支援メニュー、⑥ 支援先の声を読む（作業日誌・定期便の感想の困りごと分析：匿名化→件数と回数→原文で人が判定→作業ごとの割合のベイズ推定→エージェントに任せる候補→生成AIの答えの照合と報告） |
| X 教える | `views/nox_teach.py` | 作業学習→技能検定→職場体験実習→就職・定着の流れ、畑の工程↔検定種目↔実習先、評価表で級の目安と次のめあて、3場面の記録（JEED の3段階・CSV）、POP特別編（`static/pop_card.html`）、卒業生講座、同じ工程の「なぜ」＝「科学と人間生活」 |

計算は `nox_core.py`（Streamlit 非依存、`python nox_core.py` で自己チェック）。⑥ の困りごと分析は `diary_core.py`（同じく `python diary_core.py`）と `diary_ui.py`。ブラウザだけで動くフル版は `static/diary_analysis.html`（ページからダウンロードできます）。

## 生成AIの道具箱（01〜07）

生成AIを現場で使い、必要なところだけAIエージェントに任せるための7段の教材です。農＋X の各ページから、発信の下書き・点検・工程設計・効果の確かめに使います。
「定期便（農＋X）」の工程と、着手段階の診断の例（定期便・農園の発信）を追加しました。

| 段 | ページ | できること |
|---|---|---|
| 01 知る | `views/overview.py` | 生成AIとエージェントの違い、3段階、業務ごとの着手段階の目安 |
| 02 学ぶ | `views/learn.py` | 仕組みの言葉 → 要点・使い方への効き方・読む章。目的別の読む順 |
| 03 聞く | `views/ask.py` | 質問の型（5部品）、「分からない」の5段階、部品チェック |
| 04 守る | `views/guard.py` | 貼る前の点検と伏せ字、まぎれこんだ指示の検出、出力と元の文の照合 |
| 05 組む | `views/fit.py` | 得意×AIの道筋、作業と人の組み合わせ（全探索と貪欲法）、支援の量と転移 |
| 06 任せる | `views/agent.py` | 工程ごとの担当・権限・承認を決める設計シート、ガードレール確認 |
| 07 確かめる | `views/measure.py` | トンプソン抽出（探索と活用）、ABAB（PND・NAP・ベイズ）、公平な比較 |

## 作業学習×生成AIで「働く入口」をつくる（対象：特別支援学校／通信制高校・サポート校）

校長に提案するためのページです（`views/entry.py`、URLは `/entry`）。農業・食品加工・流通物流・ものづくり（3Dモデリング・3Dプリンター）の4分野を、
同じ「手順書 → 練習 → 外部評価 → 練習しなおし」の型で回し、職場体験実習と就職・定着までつなぎます。学校種を選ぶと中身が切りかわります。

| タブ | できること |
|---|---|
| ① 型と全体像 | 共通の型、4分野のつながり（図：`static/entry_flow.svg`）、特別支援の視点の工夫、学校種ごとの段階、2校種の比較、通信制で特別支援の視点が活きる理由 |
| ② 困りごと→解決 | 校長の困りごとに印をつけ、解決策と対応させる（⑤ のトークに使う） |
| ③ 4分野の具体例 | 活動・手順書の例・工夫・AIの使いどころ・つなぐ先・校長への一言（学校種ごとの補足つき） |
| ④ 始めやすさと3か月計画 | いま学校にあるものから始めやすい分野の順と費用の目安、3か月の試行計画とKPI |
| ⑤ PRトーク | 30秒版・2分版のトークを組み立てる。想定質問と答え方 |
| ⑥ 生成AIで手順書 | 生成AIに貼る手順書づくりの質問文を組み立てる（生成AIは呼び出さない） |
| ⑦ 評価をベイズで見る | 評価表の記録から「この工程ができる確率」をベータ分布で推定 |
| ⑧ 注意点 | 検定の受検資格、食品の販売、3Dプリンター・ロボットの安全、個人情報、言葉選び |

計算とデータは `entry_core.py`（Streamlit 非依存、`python entry_core.py` で自己チェック）。費用・順番の境目は仮置きです。

## 3Dプリンター業務推進ボード（`3d-print-board/`）

特別支援学校の作業学習と障害者雇用で、3Dプリンター・3Dモデリングを使う業務（仕上げ作業・治具・自助具・3Dモデリング）の進み具合を見える化する、ブラウザ1枚で動くダッシュボードです（試作）。Streamlit とは独立しています。
推進業務のかんばん、仕上げ作業評価表（試案）の記録と級・ベイズ推定、OpenSCADの治具生成、職域・連携先、逆算カレンダー、JSONの書き出し・読み込みがあります。Streamlit アプリでは「特別支援学校 × 3Dプリンター」のページ（`views/print3d.py`、URLは `/print3d`）に埋め込んでいます。詳しくは [`3d-print-board/README.md`](3d-print-board/README.md)。初期データの形式は `tests/test_3d_board.py` で確かめます。

## つくった人・連絡先

全ページのサイドバーと、「01 知る」「07 確かめる」の最後に、Facebook・LinkedIn へのボタンがあります。
URL は `social.py` で一括管理しています（姉妹サイト「スマートパン屋農家」と同じ内容）。

- Facebook：<https://www.facebook.com/profile.php?id=100079624235158>
- LinkedIn：<https://www.linkedin.com/in/%E9%9A%86%E8%A6%8F-%E6%A5%A0%E9%A6%99%E8%B0%B7-392aa12a0/>

支援の記録や個人が分かる情報は、メッセージに書かないでください。

## 方針

- **生成AIを呼び出しません。** APIキーを持たず、入力を外へ送りません。組み立てた文は、利用者が自分で貼ります。
  例外は「X 売る」の ⑦ Instagram 投稿だけです。Secrets に設定した合言葉を入れた本人が投稿ボタンを押したときだけ、本文と画像を Instagram に送ります。
- **初期データはすべて架空です。** 作業時間・単価・確率も仮置きで、収入のシミュレーションは予測ではなく考えるための道具です。 人は「Aさん」などの仮名。障害の種類や診断名を書く欄は作っていません。
- **判定の境目・辞書・点数は仮置きです。** 現場の支援者が `genai_core.py` を書きかえて使います。
- **点検は見落とします。** 「見つからなかった」は「安全」ではありません。最後に確かめるのは人です。

## 動かす

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 確かめる

```bash
python nox_core.py       # 農＋X の計算部品の自己チェック
python genai_core.py     # 道具箱の計算部品の自己チェック
python insta_core.py     # Instagram 投稿部品の自己チェック
python diary_core.py     # 困りごと分析の部品の自己チェック
python entry_core.py     # 「働く入口」提案ページの部品の自己チェック
pip install pytest && pytest -q   # 部品のテスト＋全ページの描画テスト
```

`main` への push と pull request で、GitHub Actions（`.github/workflows/ci.yml`）が同じチェックを実行します。

## 公開する（Streamlit Community Cloud）

1. このリポジトリを GitHub に push する
2. https://share.streamlit.io で「Create app」→ リポジトリとブランチ `main`、Main file path に `app.py` を指定する
3. Secrets は、Instagram 投稿を使うときだけ設定します（使わなければ不要。そのときは本文と画像をダウンロードして手で投稿する道だけが出ます）

### Instagram 投稿の設定（「X 売る」⑦）

Instagram API with Instagram Login（`graph.instagram.com`）の2段階投稿（`/media` → `/media_publish`）を使います。

1. Instagram をプロアカウント（ビジネス／クリエイター）にする
2. Meta for Developers でアプリをつくり「Instagram ログインによるAPI設定」を追加、`instagram_business_basic`・`instagram_business_content_publish` で自分のアカウントをつなぎ、長期アクセストークンを発行する
3. Community Cloud の App settings → Secrets に貼る（ひな形：`.streamlit/secrets.toml.example`）

```toml
[instagram]
access_token    = "IGAA..."
passcode        = "自分だけが知る合言葉"
public_base_url = "https://genai-agent-dashboard-e5xwcfhek9efndwczfb9k9.streamlit.app"
```

- 公開アプリなので、投稿ボタンは合言葉を知っている人しか押せません（まちがいは5回まで）。
- アップロードした写真は、位置情報（EXIF）を消し、縦横比を 4:5〜1.91:1 に合わせて `static/ig/` に一時的に置き、`/app/static/ig/…` の公開URLを Instagram に渡します（`server.enableStaticServing = true`）。投稿後に消します。
- 長期トークンは60日で切れます。期限前に `refresh_access_token` で延ばし、Secrets を貼りかえてください。
- 24時間に公開できるのは50件までです。

## 構成

```
insta_core.py     Instagram 投稿の部品（本文・画像の整形、API呼び出し。Streamlit 非依存）
diary_core.py     「X 売る」⑥ 困りごと分析の部品（匿名化・件数と回数・否定の印・ベイズ・照合。Streamlit 非依存）
diary_ui.py       「X 売る」⑥ 支援先の声を読む の画面
insta_ui.py       「X 売る」⑦ Instagram に投稿する の画面
app.py            入口（st.navigation で「農＋X」5ページと「道具箱」7ページを束ねる）
nox_core.py       農＋X のデータと計算（Streamlit 非依存）
genai_core.py     道具箱のデータと計算（Streamlit 非依存）
ui.py             見出し・色・サイドバー・連絡欄などの共通部品
social.py         Facebook・LinkedIn のボタン（URLの一括管理）
views/            12のページ（nox_*.py が農＋X）
tests/            部品のテスト、ページの描画テスト
.streamlit/       テーマ設定
```
