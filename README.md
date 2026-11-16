# 生成AI＆AIエージェント利活用ダッシュボード

生成AIを現場で使い、必要なところだけAIエージェントに任せるための、7段のインタラクティブ教材です。
「福祉×生成AI」（スマートパン屋農家）、「特別支援学校版カリキュラム」「AIを自分の武器にする」（科学と人間生活）の3ページと、
生成AIの本棚メモ、「生成AIの利活用＝AIエージェントの適用ではない」という整理を、1つにまとめました。

| 段 | ページ | できること |
|---|---|---|
| 01 知る | `views/overview.py` | 生成AIとエージェントの違い、3段階、業務ごとの着手段階の目安 |
| 02 学ぶ | `views/learn.py` | 仕組みの言葉 → 要点・使い方への効き方・読む章。目的別の読む順 |
| 03 聞く | `views/ask.py` | 質問の型（5部品）、「分からない」の5段階、部品チェック |
| 04 守る | `views/guard.py` | 貼る前の点検と伏せ字、まぎれこんだ指示の検出、出力と元の文の照合 |
| 05 組む | `views/fit.py` | 得意×AIの道筋、作業と人の組み合わせ（全探索と貪欲法）、支援の量と転移 |
| 06 任せる | `views/agent.py` | 工程ごとの担当・権限・承認を決める設計シート、ガードレール確認 |
| 07 確かめる | `views/measure.py` | トンプソン抽出（探索と活用）、ABAB（PND・NAP・ベイズ）、公平な比較 |

## 方針

- **生成AIを呼び出しません。** APIキーを持たず、入力を外へ送りません。組み立てた文は、利用者が自分で貼ります。
- **初期データはすべて架空です。** 人は「Aさん」などの仮名。障害の種類や診断名を書く欄は作っていません。
- **判定の境目・辞書・点数は仮置きです。** 現場の支援者が `genai_core.py` を書きかえて使います。
- **点検は見落とします。** 「見つからなかった」は「安全」ではありません。最後に確かめるのは人です。

## 動かす

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 確かめる

```bash
python genai_core.py     # 計算部品の自己チェック
pip install pytest && pytest -q   # 部品のテスト＋全ページの描画テスト
```

`main` への push と pull request で、GitHub Actions（`.github/workflows/ci.yml`）が同じチェックを実行します。

## 公開する（Streamlit Community Cloud）

1. このリポジトリを GitHub に push する
2. https://share.streamlit.io で「Create app」→ リポジトリとブランチ `main`、Main file path に `app.py` を指定する
3. Secrets の設定は不要です（外部サービスを呼びません）

## 構成

```
app.py            入口（st.navigation で7ページを束ねる）
genai_core.py     データと計算（Streamlit 非依存）
ui.py             見出し・色などの共通部品
views/            7つのページ
tests/            部品のテスト、ページの描画テスト
.streamlit/       テーマ設定
```
