<p align="center">
  <a href="https://xulang.org/ja">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-dark.svg">
      <img src="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-light.svg" alt="XU — ネイティブコード。明確な意図。" width="100%">
    </picture>
  </a>
</p>

<h1 align="center">Xu プログラミング言語</h1>

<p align="center">
  ネイティブコンパイル、所有権、組み込み並行性を備えたシステム言語。<br><strong>決定論的メモリ管理。ガベージコレクタ不要。</strong>
</p>

<p align="center">
  <a href="https://xulang.org/ja/playground"><strong>オンラインプレイグラウンド（インストール不要）</strong></a> &nbsp; · &nbsp;
  <a href="https://xulang.org/ja/docs/start">30秒クイックスタート</a> &nbsp; · &nbsp;
  <a href="https://xulang.org/ja/download">インストーラーのダウンロード</a> &nbsp; · &nbsp;
  <a href="https://github.com/xulang-org/xu">コンパイラソース</a>
</p>

<p align="center">
  <a href="README.md">English</a> / <a href="README.zh-CN.md">简体中文</a> / <a href="README.zh-TW.md">繁體中文</a> / <strong>日本語</strong> / <a href="README.ko.md">한국어</a> / <a href="README.es.md">Español</a> / <a href="README.fr.md">Français</a> / <a href="README.de.md">Deutsch</a> / <a href="README.ru.md">Русский</a> / <a href="README.pt-BR.md">Português</a>
</p>

## 簡潔な言語、明快なフロー

XU はコンパイル時の所有権・借用チェック、軽量コルーチン、型付きチャネルをシームレスに統合したシステム言語です。ソースコードは AOT によりネイティブマシンコードまたは WebAssembly へとコンパイルされ、決定論的なライフサイクル管理によってリソースが解放されます。

| 言語機能 | 提供される体験 |
| :--- | :--- |
| **GC 不要の所有権モデル** | コンパイル時にムーブと借用を検証し、ライフタイムを自動推論。リソースを決定論的に回収。 |
| **言語組み込みの並行処理** | `xu` で軽量コルーチンを起動し、型付き `chan` チャネルを介して安全に値を送受信。 |
| **可視化された制御フロー** | `<<` で値を返し、`>>>` でエラーを送出。呼び出し元の `>>> (err) { … }`（または `>>>`）で明示的にエラー処理。 |
| **統合ツールチェーン** | `xu` コマンドだけでビルド、実行、チェック、テスト、フォーマット、ドキュメント生成、言語サーバーを利用可能。 |

## XU コードを読む

2 つのワーカー、1 つのチャネル、そして明示的なエラー処理フロー：

```xu
@main
#errors

fn score(name string) int {
    if name.len == 0 { >> errors.new("empty name") }
    << name.len * 10
}

fn worker(name string, results chan int) {
    value := score(name) >>> (err) {
        results <- 0
        <<
    }
    results <- value
}

fn main() int {
    results := chan int{cap: 2}
    xu worker("hello", results)
    xu worker("world", results)
    println(<-results + <-results)
    << 0
}
```

`main.xu` として保存し、`xu run main.xu` を実行すると `100` が出力されます。

`#errors` でパッケージをインポートし、`xu worker(...)` でコルーチンを起動します。2 回のチャネル受信で結果を集約します。`score` が失敗した場合、`>>> (err) { … }` がフォールバック値 `0` をチャネルに送信し、現在のワーカーを終了します。

## ここから始める

インストール不要の [ブラウザプレイグラウンド](https://xulang.org/ja/playground) を試すか、ローカル開発用に [SDK をダウンロード](https://xulang.org/ja/download) してください。インストール後のコマンド：

```sh
xu --version
xu run main.xu
xu build main.xu -o hello
```

続いて [入門ガイド](https://xulang.org/ja/docs/start)、[言語リファレンス](https://xulang.org/ja/docs/lang/syntax)、または [公式サンプル集](https://github.com/xulang-org/examples) をご覧ください。

XU は現在 **0.x シリーズ** として活発に進化を続けています。リリース済み SDK は [Releases](https://github.com/xulang-org/xu/releases) を、プラットフォームおよびランタイム対応状況は [ステータスと制限](https://xulang.org/ja/docs/status) を参照してください。[ベンチマークダッシュボード](https://xulang.org/ja/benchmarks) では実測ワークロード、コンパイラバージョン、ソース出所を記録しています。

[API ドキュメント](https://xulang.org/api/) を開き、「API 検索」でパッケージの検索やページ内宣言へのジャンプが可能です。入力欄の外で `/` キーを押すと検索が開き、矢印キーと Enter で結果を操作、Escape で閉じます。モバイル表示では目次が自動的に折りたたまれ、本文に素早くアクセスできます。宣言の見出しは固定リンクとなっており、「リンクをコピー」で現在のページや宣言を共有できます。

API インデックスには、よく使うタスクへのショートカット、トピック解説、標準ライブラリ・UI・拡張パッケージのページ内検索が用意されています。パッケージページ冒頭には「宣言エクスプローラー」があり、名前、用途、種類で絞り込んで完全なシグネチャと説明へジャンプできます。関連ソースサンプルは必要に応じて展開可能です。

## エコシステムを探る

| プロジェクト | リンク |
| :--- | :--- |
| **言語とコンパイラ** | [xu](https://github.com/xulang-org/xu) — セルフホストコンパイラ、標準ライブラリ、CLI ツール。 |
| **サンプルから学ぶ** | [examples](https://github.com/xulang-org/examples) — 構文の基本、並行処理、ネットワーク、データベース、UI サンプル。 |
| **ライブラリと統合** | [packages](https://github.com/xulang-org/packages) — データベースドライバ、メッセージング、ストレージ、各種サービス統合。 |
| **エディタ対応** | [vscode-xu](https://github.com/xulang-org/vscode-xu) — VS Code および Cursor 向けの構文ハイライトと XU 言語サーバー。 |
| **パフォーマンスとベンチマーク** | [bench](https://github.com/xulang-org/bench) — 他言語との比較ワークロードと再現可能なベンチマークソース。 |
| **公式サイトとドキュメント** | [xulang-org](https://github.com/xulang-org/xulang-org) — xulang.org 公式サイト、ドキュメントセンター、WebAssembly プレイグラウンド。 |

## 一緒に XU を開発する

サンプルの実行、コンパイラの不具合報告、ドキュメントの改善、ライブラリの寄与など、どなたでも歓迎します。[コンパイラの Issues](https://github.com/xulang-org/xu/issues) や [公式サイトの Issues](https://github.com/xulang-org/xulang-org/issues) からご参加ください。

開発に参加する前に [貢献ガイド](CONTRIBUTING.md) および [共通リポジトリ規約](.github/REPOSITORY_RULES.md) をお読みください。メンテナーの方は [GitHub 設定チェックリスト](.github/GITHUB_SETTINGS.md) を参照してください。

[公式サイト](https://xulang.org/ja) · [GitHub](https://github.com/xulang-org) · [X / @xulang_org](https://x.com/xulang_org) · [MIT ライセンス](LICENSE)

---

<details>
<summary><strong>xulang.org の開発に参加する</strong> — Webサイトのビルド、プレイグラウンド、デプロイ</summary>

このホームページリポジトリには公式サイトのソースコードが含まれています。サイトは `VERSION` で指定された公式リリース済み **XU SDK** を使用しており、開発版ビルドとは分離されています。

### ローカルでのビルド

**Python 3.10+**（標準ライブラリのみ使用）が必要です。静的サイトのビルドと検証には XU、Node.js、隣接リポジトリは不要です。

```sh
make build                       # dist/ をビルドし、内部リンクとアセットを検証
make run                         # プレビュー：http://127.0.0.1:8080
make run PORT=18080               # 指定ポートでプレビュー
make check                       # 静的サイトのリグレッションテストを実行
make build BASE_PATH=/xulang-org  # プロジェクトのサブパス向けにビルド
make clean                       # dist/ と build/playground/ をクリーンアップ
```

| パス | 用途 |
| :--- | :--- |
| `content/{en,zh,ja,...}/` | ドキュメント、チュートリアル、ブログ、API 本文。 |
| `templates/` | ページテンプレート、API ガイド、サンプル選択設定。 |
| `www/` | スタイルシート、スクリプト、フォント、アイコン、静的アセット。 |
| `playground/typed/` | XU で書かれたブラウザ向け WebAssembly ランタイム。 |
| `scripts/` | 静的ビルダー、API 生成、リリース検証スクリプト。 |
| `tests/` | 静的サイト、プレイグラウンド、チャネルのリグレッションテスト。 |
| `brand/` | ブランドアセットとビジュアルアイデンティティガイドライン。 |

生成された出力は、Git 管理対象外の `dist/` および `build/` ディレクトリに配置されます。コンテンツフラグメントは `<!--title: ...-->` でタイトルを宣言し、`docs/start/index.html` などのディレクトリルートとしてレンダリングされます。

### 共有サイトメタデータ

`templates/site-metadata.json` は、すべての言語共通でサイト全体のメタデータを管理します。

- サイト名、ベースタイトル、説明
- テーマカラー、作成者、ソーシャルプレビューカード（Open Graph / Twitter）
- 検索キーワード、言語対応設定（デフォルト言語、サポート言語一覧）
- 言語切り替えナビゲーション（各言語のラベルと URL プレフィックス）
- ソーシャルリンクとライセンス情報

言語を追加または変更する際は、このメタデータファイルおよび `scripts/build-static.py` の言語設定を更新してください。

### API ドキュメントの生成

静的サイトは `VERSION` で指定されたリリース済み SDK のスナップショットを使用します。

```sh
make api
make api XU_SRC=/path/to/released-sdk/src
```

外部の `examples` リポジトリから UI サンプルを結合する場合：

```sh
make api XU_EXAMPLES=/path/to/examples XU_EXAMPLES_REF=FULL_EXAMPLES_COMMIT_SHA
```

選択されたファイルはそのコミットと一致している必要があります。両方のサンプル変数が指定されていない場合、`make api` は既存のスナップショットを再利用して検証します。

### WebAssembly プレイグラウンド

適合する SDK と Node.js 22+ を使用して、XU ランナーを WebAssembly にコンパイルおよび最適化します。
ロックファイルによりビルド時に使用する Binaryen 最適化ツールのバージョンが固定されます。静的サイトのビルド自体には Python のみが必要です。

```sh
npm ci --ignore-scripts # 固定バージョンの WASM オプティマイザをインストール
make wasm XU_ROOT=/path/to/released-sdk
make check-playground  # Node.js 上で実際の WASM とサンプル実行を検証
make check-chan        # XU でネイティブチャネルサンプルを検証
make build             # ランナーを dist/ にバンドル
```

プレイグラウンドはブラウザクライアント上で動作します。通常のドキュメント閲覧やホームページアクセス時に WASM がプリロードされることはありません。初回実行時にページがモジュールをダウンロードして非同期コンパイルし、コンパイル結果をワーカーに渡してインスタンス化・実行します。

### ベンチマークとデプロイ

ベンチマークを更新する際は、同一の 6 プラットフォーム完全 Actions 成果物をダウンロードし、以下を実行します：

```sh
python3 scripts/import-benchmarks.py --artifacts DIR --commit FULL_SHA --run-id ID --date YYYY-MM-DD
python3 scripts/gen-benchmarks.py
```

インポート処理では、コンパイラの識別情報、ソースクロージャ、ブートストラップ固定点、完全なワークロード、標準出力を検証します。

`VERSION` はダウンロードページ、API ドキュメント、ブラウザランタイムが使用する公式 SDK を指定します。Pages ワークフローは SDK の SHA-256 を検証し、ビルド成果物をテストした上で、`main` へのプッシュ時にデプロイします。

</details>

### UI API とサンプル

[日本語 UI ガイド](content/ja/docs/ui.html) と [英語ガイド](content/en/docs/ui.html) は、`VERSION` で選定された公式 Xu SDK に対応しています。`ui`、`ui/draw`、`ui/layout`、`ui/chart`、`ui/widgets`、`ui/webview` の 6 パッケージすべてが公式 API ナビゲーションに含まれています。

公式の手書きガイドは `templates/api-guides/{en,ja}/ui*` にあり、セマンティック規約とフィールド説明は `templates/api-contracts.json` に配置されています。

ブラウザプレイグラウンドでは [3ページのコントロールギャラリー](https://xulang.org/ja/playground?example=ui-gallery) を提供しています。

Widgets ドキュメントは **API → UI → Widgets → コンポーネント** の階層で構成されています。`templates/widgets.json` で分類・用法・体験説明を管理し、`scripts/gen-widgets.py` が公式宣言と連動してページを生成します。
