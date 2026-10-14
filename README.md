# xulang-org

Xu 官网源码，使用 GitHub Pages 托管，域名为 `xulang.org`。默认英文，中文入口为 `/zh/`；页面右上角可切换语言，保留当前页面。旧 `/en/` 地址自动跳转到对应英文页面。

官方帐号入口在所有页面的顶部和页脚：GitHub [@xulang-org](https://github.com/xulang-org)，
X [@xulang_org](https://x.com/xulang_org)。链接统一维护于 `scripts/site_layout.py` 的
`SOCIAL_PROFILES`，页脚展示完整帐号；移动端保留顶部图标入口。

## 目录

| 目录 | 内容 |
| --- | --- |
| `content/{zh,en}/` | 中英文页面、教程与 API 正文 |
| `templates/` | 页面模板 |
| `www/` | CSS、JavaScript、字体、图标与可下载示例 |
| `playground/runtime/` | Xu 编写的浏览器运行器 |
| `scripts/` | 静态构建、运行器构建与 API 生成 |
| `tests/` | 构建、在线运行与 chan 示例验证 |
| `brand/` | Xu 品牌资源 |

生成文件统一放在忽略的 `build/` 和 `dist/`；本机记录与历史备份放在忽略目录中。
WASM 编译后端由 Xu 编译器仓库维护，官网直接调用产品编译器。

## 静态构建与预览

需要 Python 3.10 或更新版本，仅使用标准库。

```sh
make build                      # 输出 dist/，检查页面和资源链接
make run                        # http://127.0.0.1:8080
make run PORT=18080
make check                      # 静态构建与 API 生成回归测试
make build BASE_PATH=/xulang-org # GitHub 项目站点路径
make clean                      # 清理 dist/ 和 build/playground/
```

静态构建无需 Xu、Node.js 或相邻仓库。`content/` 的 HTML 正文片段以
`<!--title: ...-->` 指定标题；`/docs/start` 等页面生成 `docs/start/index.html`。

## 在线运行器

需要支持实验性 `wasm32` 目标的 Xu 产品编译器，以及匹配的标准库源码。
本机默认使用同级 `../xu`；历史 Xu 0.8.3 SDK 尚不支持该目标。

```sh
make wasm                           # 使用 ../xu/bin/xu
make wasm XU_ROOT=/path/to/xu-sdk     # 使用支持 wasm32 的 SDK
XU_BIN=/path/to/xu make wasm XU_ROOT=/path/to/xu
make check-playground                # Node.js 执行真实 WASM 与首页示例
make check-chan                      # 产品编译器验证三个原生 chan 示例
make build
```

构建脚本准备运行器和嵌入的标准库源码，执行 `xu build --target wasm32`，
输出 `build/playground/xu-play.wasm`。静态构建将其复制到 `dist/xu-play.wasm`。
`www/` 只保存静态资源；运行器构建不复制、修改或重新编译 Xu 编译器。

运行器使用真实 Xu 解析器、类型与借用检查器、MIR 解释器和 chan 调度器。
JavaScript 负责 Web Worker、内存接口和输出读取。构建无需 Rust、LLVM 或 Emscripten。
19 个示例统一定义于 `www/xu-play-examples.json`，覆盖基础语法、函数、数据结构、
编译诊断，以及信道收发、多 worker 汇总和生产者流水线。

每次运行使用独立的 64 MiB WASM arena，源码上限 128 KiB、输出上限 256 KiB，
支持停止、10 秒超时和执行步数限制。源码不发往服务器。
浏览器信道由 Xu 执行器协作调度，支持缓冲、无缓冲、关闭与死锁诊断；
文件、网络、完整标准库与 f64 运算尚不支持，未实现的操作返回明确诊断。
本地未构建 WASM 时，静态首页显示运行器未启用。

## GitHub Pages

在仓库 **Settings → Pages** 中选择 **GitHub Actions**，填写自定义域名
`xulang.org` 并启用 **Enforce HTTPS**。

`.github/workflows/pages.yml` 在推送 `main` 时测试、构建和部署；Pull Request
只测试和构建。流水线锁定 `xulang-org/xu` 的 main 提交，读取该提交的 `VERSION`，
只下载同版本的正式 Linux ARM64 SDK，并验证附件 SHA-256。
该版本必须已经正式发布且支持 WASM；版本不匹配、草稿或预发布版本均无法部署。
发布构建使用 `--require-playground`，运行器缺失会失败。

页面中的 `{{xu_version}}` 在构建时统一展开。发布流水线用同一 SDK 重建 API，
再用 `--xu-version` 将 SDK 版本用于首页、页头页脚、文档、API 和下载链接。
API 源码快照的版本与 SDK 不一致时构建失败；历史博客保留当时的版本。
WASM 也记录实际编译版本和校验和，旧版本产物无法随新版页面一起发布。
本地离线构建默认使用 `xu.xun` 中的 `xu:`，无需访问 GitHub。
`make api` 会将此次 API 源码版本同步到官网 `VERSION`、根清单的 `version:` / `xu:`
和运行器清单的 `xu:`。

构建读取 `actions/configure-pages` 的 `base_path`，同时支持项目地址与自定义域名。
编译器下载链接指向 [Xu GitHub Releases](https://github.com/xulang-org/xu/releases)，
安装包由编译器仓库发布。

## 内容维护

```sh
make api XU_ROOT=/path/to/xu XU_PACKAGES_ROOT=/path/to/packages
```

`scripts/gen-api.py` 从标准库和扩展包源码生成中英文 API 正文、索引与统计，
跳过编译器内部包、测试源码和夹具。生成 API 需要相邻源码，构建官网无需执行该步骤。
教程中的本机程序在独立 examples 仓库运行；三个 chan 程序也可从官网直接下载。

官网 `VERSION`、根 `xu.xun` 的 `version:` 和 `xu:` 与 Xu main 对应的最终发布版本一致。
运行器模块自身的 `version:` 独立管理。
