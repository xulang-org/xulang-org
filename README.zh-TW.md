<p align="center">
  <a href="https://xulang.org/zh-tw">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-dark.svg">
      <img src="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-light.svg" alt="XU — 原生編譯，清晰表達。" width="100%">
    </picture>
  </a>
</p>

<h1 align="center">XU 程式語言</h1>

<p align="center">
  一門融合原生編譯、所有權與內建併發的系統程式語言。<br>
  <strong>確定性記憶體管理，無垃圾回收器。</strong>
</p>

<p align="center">
  <a href="https://xulang.org/zh-tw/playground"><strong>線上體驗</strong></a> &nbsp; · &nbsp;
  <a href="https://xulang.org/zh-tw/docs/start">閱讀指南</a> &nbsp; · &nbsp;
  <a href="https://xulang.org/zh-tw/download">下載 XU</a> &nbsp; · &nbsp;
  <a href="https://github.com/xulang-org/xu">編譯器原始碼</a>
</p>

<p align="center">
  <a href="README.md">English</a> / <a href="README.zh-CN.md">简体中文</a> / <strong>繁體中文</strong> / <a href="README.ja.md">日本語</a> / <a href="README.ko.md">한국어</a> / <a href="README.es.md">Español</a> / <a href="README.fr.md">Français</a> / <a href="README.de.md">Deutsch</a> / <a href="README.ru.md">Русский</a> / <a href="README.pt-BR.md">Português</a>
</p>

## 簡潔的語言，清晰的流向

XU 將編譯期所有權與借用檢查、輕量協程和強型別通道結合在一起。原始碼透過 AOT 編譯為原生機器碼或 WebAssembly，資源按生命週期確定性釋放。

| 語言設計 | 帶來的體驗 |
| :--- | :--- |
| **所有權，無 GC** | 編譯期檢查移動與借用，推導生命週期，確定性回收資源。 |
| **語言內建併發** | 用 `xu` 啟動協程，透過強型別 `chan` 通道傳遞值。 |
| **看得見的控制流** | `<<` 返回、`>>` 拋錯，`>>> (err) { … }` 在呼叫處處理錯誤。 |
| **整合的工具鏈** | 透過 `xu` 完成建置、執行、檢查、測試、格式化、文件生成與語言服務。 |

## 讀一段 XU

兩個工作協程、一個通道，以及明確的錯誤處理路徑：

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

儲存為 `main.xu`，執行 `xu run main.xu`，輸出 `100`。

`#errors` 匯入包，`xu worker(...)` 啟動協程，兩次通道接收匯總結果。若 `score` 失敗，`>>> (err) { … }` 會傳送兜底值 `0`，然後結束當前工作協程。

## 從這裡開始

無需安裝，直接開啟 [瀏覽器演練場](https://xulang.org/zh-tw/playground)；也可以 [下載 SDK](https://xulang.org/zh-tw/download)，在本地開發。安裝後執行：

```sh
xu --version
xu run main.xu
xu build main.xu -o hello
```

接著閱讀 [入門指南](https://xulang.org/zh-tw/docs/start)、[語言參考](https://xulang.org/zh-tw/docs/lang/syntax)，或執行 [官方示例](https://github.com/xulang-org/examples)。

XU 正在 **0.x 階段**持續演進。已釋出 SDK 見 [Releases](https://github.com/xulang-org/xu/releases)，平臺與執行時覆蓋見 [限制與現狀](https://xulang.org/zh-tw/docs/status)。[基準看板](https://xulang.org/zh-tw/benchmarks) 保留實測負載、編譯器版本與原始碼來源。

開啟 [API 文件](https://xulang.org/zh/api/)，使用「搜尋 API」查詢包或直達本頁宣告。在輸入框外按 `/` 開啟搜尋，方向鍵和 Enter 操作結果，Escape 關閉。手機上目錄預設收起，便於直接閱讀正文；宣告標題可直達對應位置，「複製連結」可分享當前頁面或宣告。

API 索引提供常用任務入口、主題用途說明和頁內包搜尋，可按標準庫、UI、擴充套件包篩選。包詳情頂部提供「宣告速覽」，按名稱、用途或宣告型別篩選，再跳轉到完整簽名與說明；相關原始碼示例預設摺疊，按需展開。

## 探索生態

| 專案 | 入口 |
| :--- | :--- |
| **語言與編譯器** | [xu](https://github.com/xulang-org/xu) — 自舉編譯器、標準庫與命令列工具。 |
| **從示例入手** | [examples](https://github.com/xulang-org/examples) — 語法基礎、併發、網路、資料庫與 UI 示例。 |
| **庫與服務整合** | [packages](https://github.com/xulang-org/packages) — 資料庫驅動、訊息佇列、儲存與服務整合。 |
| **編輯器支援** | [vscode-xu](https://github.com/xulang-org/vscode-xu) — VS Code 與 Cursor 的語法高亮和 XU 語言服務。 |
| **效能與橫測** | [bench](https://github.com/xulang-org/bench) — 跨語言負載與可復現的基準原始碼。 |
| **官網與文件** | [xulang-org](https://github.com/xulang-org/xulang-org) — xulang.org、文件中心與 WebAssembly 演練場。 |

## 一起建設 XU

執行一個示例、反饋編譯器問題、完善文件，或貢獻一個庫。可以從 [編譯器 Issues](https://github.com/xulang-org/xu/issues) 和 [官網 Issues](https://github.com/xulang-org/xulang-org/issues) 開始。

參與開發前請閱讀 [貢獻指南](CONTRIBUTING.md) 與 [統一倉庫管理規範](.github/REPOSITORY_RULES.md)；維護者可按 [GitHub 配置清單](.github/GITHUB_SETTINGS.md) 啟用並驗收後臺規則。

[官網](https://xulang.org/zh-tw) · [GitHub](https://github.com/xulang-org) · [X / @xulang_org](https://x.com/xulang_org) · [MIT 許可證](LICENSE)

---

<details>
<summary><strong>參與 xulang.org 開發</strong> — 網站建置、演練場與部署</summary>

這個主頁倉庫也儲存了官網原始碼。站點使用 `VERSION` 指定的已釋出 **XU SDK**，開發版另行迭代。

### 本地建置

需要 **Python 3.10+**，僅使用標準庫。靜態建置與檢查無需 XU、Node.js 或相鄰倉庫。

```sh
make build                       # 建置 dist/，校驗內部連結與資源
make run                         # 預覽：http://127.0.0.1:8080
make run PORT=18080               # 指定預覽埠
make check                       # 執行靜態站點回歸檢查
make build BASE_PATH=/xulang-org  # 建置到專案子路徑
make clean                       # 清理 dist/ 與 build/playground/
```

| 路徑 | 用途 |
| :--- | :--- |
| `content/{en,zh}/` | 文件、教程、部落格與 API 正文。 |
| `templates/` | 頁面模板、API 手寫指南與示例選擇配置。 |
| `www/` | 樣式、指令碼、字型、圖示與靜態資源。 |
| `playground/typed/` | 使用 XU 編寫的瀏覽器 WebAssembly 執行器。 |
| `scripts/` | 靜態建置、API 生成與釋出校驗。 |
| `tests/` | 站點、演練場與通道迴歸檢查。 |
| `brand/` | 品牌物料與視覺識別規範。 |

產物輸出至已忽略的 `dist/` 與 `build/`。正文片段透過 `<!--title: ...-->` 宣告標題，生成 `docs/start/index.html` 等目錄路由。

### 共享站點後設資料

狀態頁的包數來自生成的 `content/{en,zh}/api/index.html` 清單。建置器檢查中英清單相同且包頁面存在；控制元件詳情與開發預覽頁不計入包數。新增包時透過 API 生成器更新清單。

`templates/releases.json` 同時提供中英版本記錄、部落格索引的近期釋出條目與側欄釋出連結。新增版本時更新此檔案，並新增對應的雙語博文；較早的歷史博文仍由正文維護。首頁橫幅、頁頭和頁尾不顯示 SDK 補丁版本；下載、文件與 API 區保留版本身份，結構化軟體後設資料仍準確標識選定 SDK。

手動選擇語言將 `xu-lang=en` 或 `xu-lang=zh` 寫入 localStorage 及有效期一年的 SameSite=Lax cookie。localStorage 按來源共享，cookie 的路徑限定在部署字首。語言連結還附帶 `?lang=en` 或 `?lang=zh`，因此儲存被禁用時本次選擇仍生效。優先順序為有效查詢引數、localStorage、cookie；只有英文首頁入口會自動選擇中文，先遵循已存選擇，再參考简体中文瀏覽器語言。若所有儲存都被禁用，之後不帶查詢引數的訪問將再次使用瀏覽器語言。

sitemap 有意省略 `lastmod`：檢出時間和 API 重新生成時間不能證明編輯日期，重複建置不應制造內容更新。只有具備可靠的逐頁內容歷史（包含共享相依性）後才應新增日期。

### API 內容與示例

手寫說明儲存在 `templates/api-guides/{en,zh-tw}/`，生成時與所選 SDK 的公開宣告合併。示例從官方 examples 倉庫的固定提交匯入；`www/api-examples/` 中的快照支援本地與 CI 獨立建置。

逐函式說明儲存在 `templates/api-contracts.json`，按包、接收者型別和名稱定位。中英內容須說明具體用途、引數含義和返回行為；`notes` 補充邊界與前提，`errors` 說明錯誤處理，`examples` 儲存可獨立執行的本機 SDK 程式和可選的預期 `output`。反引號表示行內程式碼。型別成員分別顯示為公開欄位或要求的方法，避免與函式引數混淆。

經過原始碼核對的條目儲存 `source_sha256`（簽名與函式體）和 `package_sha256`（含私有輔助函式的包原始碼）。任一摘要變化都會阻止生成；先重新核對行為並更新說明，再重新整理摘要。引數名與手寫示例欄位也會在寫頁面前校驗。用匹配的原生編譯器驗證函式旁的示例：

```sh
python3 scripts/check-api-examples.py --xu /path/to/selected-sdk/bin/xu
```

LLM 文件使用 `templates/llms/*.md`、站點共享示例、`VERSION` 與 `www/benchmarks.json`。靜態建置按選定 SDK 身份生成文件；執行 `python3 scripts/gen_llms.py` 更新已跟蹤的 `www/llms*.txt` 副本。

重新整理宣告與示例時，在 `templates/api-examples.json` 中選擇相容原始碼，用所選 SDK 檢查，再指定示例倉庫及完整提交 SHA：

```sh
make api XU_ROOT=/path/to/selected-sdk XU_PACKAGES_ROOT=/path/to/selected-sdk/packages \
  XU_EXAMPLES_ROOT=../examples XU_EXAMPLES_REF=FULL_EXAMPLES_COMMIT_SHA
```

所選檔案必須與該提交一致。未提供兩個示例變數時，`make api` 複用並校驗已有快照。原生示例使用本地 SDK 執行。

### WebAssembly 演練場

使用匹配的 SDK 和 Node.js 22+ 將 XU 執行器編譯並最佳化為 WebAssembly。
鎖檔案固定建置時使用的 Binaryen 最佳化器；只建置靜態站點仍僅需 Python。

```sh
npm ci --ignore-scripts # 安裝固定版本的 WASM 最佳化器
make wasm XU_ROOT=/path/to/released-sdk
make check-playground  # 在 Node.js 中檢查真實 WASM 與示例執行
make check-chan        # 使用 XU 檢查原生通道示例
make build             # 將執行器打包到 dist/
```

演練場在瀏覽器客戶端執行。閱讀文件或僅開啟首頁不會預載入 WASM。首次執行時，頁面下載模組並非同步編譯，再將編譯結果交給 worker 例項化和執行 Xu。編譯結果在當前頁面內複用；初始化失敗可以重試，停止或切換程式會取消舊 worker 的初始化。

執行器線性記憶體的初始大小由 SDK 決定，最多增長到 256 MiB。`build/playground/build.json` 記錄 WASM 與 gzip 體積、摘要、最佳化引數和記憶體限制。生成的 WASM 儲存在 `build/playground/`。

### 基準與部署

重新整理基準時，下載同一次完整六平臺 Actions 附件，然後執行：

```sh
python3 scripts/import-benchmarks.py --artifacts DIR --commit FULL_SHA --run-id ID --date YYYY-MM-DD
python3 scripts/gen-benchmarks.py
```

匯入會驗證編譯器身份、源閉包、自舉定點、完整負載與 stdout。未測項保留空缺，C、Rust 行取 O1/O2/O3 中位數最小值。

`VERSION` 指定下載頁、API 文件和瀏覽器執行時使用的正式 SDK。Pages 工作流校驗 SDK 的 SHA-256、測試建置產物，並在推送到 `main` 後部署。

</details>

### UI API 與示例

[繁體中文 UI 指南](content/zh-tw/docs/ui.html) 與 [英文指南](content/en/docs/ui.html) 對應 `VERSION` 中選定的正式 Xu SDK。`ui`、`ui/draw`、`ui/layout`、`ui/chart`、`ui/widgets`、`ui/webview` 六個包均已進入正式 API 導航。舊 UI preview URL 重定向到對應正式頁面，並保留宣告錨點。

正式版手寫指南位於 `templates/api-guides/{en,zh-tw}/ui*`，語義契約和欄位說明位於 `templates/api-contracts.json`。使用選定的正式 SDK 執行 `make api` 重新生成宣告。示例目錄涵蓋繪圖、佈局、編輯器、桌面服務、視窗、WebView 請求、樣式與擴充套件控制元件；每項鍊接到不可變的完整專案和校驗摘要驗證的原始碼下載。

未來尚未釋出的 API 仍可顯式生成開發預覽：

```sh
python3 scripts/gen-api.py --src /path/to/development-sdk/src --preview --package ui
make build
make check
```

預覽指南與契約位於 `templates/api-guides/{en,zh-tw}/preview/ui*` 和 `templates/api-preview-contracts.json`。顯式生成的預覽標明開發 SDK 版本與原始碼 SHA-256，並優先於舊 URL 重定向。正式建置繼續使用選定的正式 SDK 與已有示例快照。

瀏覽器演練場提供[三頁控制元件畫廊](https://xulang.org/zh-tw/playground?example=ui-gallery)：
基礎控制元件、Radio、ListBox、Scroll、Tabs、StyledLabel、Card、Badge、Progress 與只展示的只讀 Editor
在 WASM 中執行同步自桌面的 Xu 控制元件邏輯，Canvas 呈現繪圖命令；畫廊中的 Editor 僅供展示，原生文字編輯與 IME 尚未接入。原有形狀與文字、點選計數器示例繼續保留。
[瀏覽器 UI 架構與建置說明](playground/README.md)列出了原始碼同步、支援介面、鍵盤操作與重放限制。

Widgets 文件按 **API → UI → Widgets → 元件** 組織，中英文各有 46 個元件頁面。`templates/widgets.json` 管理分類、用法與體驗說明，`scripts/gen-widgets.py` 結合正式宣告生成頁面，並在正式 API 生成後自動執行；使用 `--check` 檢查生成結果。

46 個元件體驗均執行可編輯的 Xu/WASM 示例，原始碼位於 `playground/examples/widget-*.xu`，由 `python3 scripts/gen-widget-examples.py` 釋出。部分體驗使用組合或受限實現：DatePicker 展示日期條，WebView 為佔位示例，TaskButton 不啟動後臺任務，文字欄位僅支援基本按鍵編輯，不提供原生選區、剪貼簿或 IME。各體驗註明能力邊界；執行 Xu 不代表完整桌面元件已經移植。

[瀏覽器 UI 使用指南](https://xulang.org/zh-tw/docs/ui/#browser-playground)說明了 ComboBox 候選選單、MultiSelect 勾選、Popover 偏好設定與 Modal 焦點操作。工作區與預覽遵循固定的 XUUI 設計參考，使用硃紅色焦點邊界，並對齊控制元件文字。手機上透過「檔案」「編輯」「預覽」「輸出」切換檢視；「適應視窗」縮放畫布，「100%」配合「平移」檢視大畫布，關閉平移後即可操作控制元件。
