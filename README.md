# xulang-org

Xu 官网源码，使用 GitHub Pages 托管。默认中文，英文入口为 `/en/`，已绑定域名 `xulang.org`。

## 构建与本地预览

需要 Python 3.10 或更新版本，仅使用标准库。静态构建不依赖 Xu 编译器、Node.js 或相邻仓库。

```sh
make build                      # 输出到 dist/，同时检查站内页面与资源链接
make run                        # http://127.0.0.1:8080
make run PORT=18080
make check                      # 静态构建回归测试
make build BASE_PATH=/xulang-org # GitHub 项目站点路径
```

`content/{zh,en}/` 保存 HTML 正文片段，首行 `<!--title: ...-->` 指定标题；
`templates/page.html` 与 `scripts/site_layout.py` 提供页头、导航、侧栏和页脚；
`www/` 保存 CSS、JavaScript、字体和图标。`/docs/start` 等页面生成对应的
`docs/start/index.html`，链接统一使用目录 URL。`dist/` 是构建产物，不提交。

## GitHub Pages

1. 将仓库上传到 GitHub，默认分支使用 `main`。
2. 在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
3. `.github/workflows/pages.yml` 在推送到 `main` 时测试、构建并部署；Pull Request 只测试和构建。

构建从 `actions/configure-pages` 读取实际 `base_path`，因此默认项目地址
`https://<owner>.github.io/xulang-org/` 和自定义域名都能使用。

绑定域名时，在 **Settings → Pages → Custom domain** 填入 `xulang.org`，
再按 [GitHub 官方域名配置文档](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
设置 DNS，启用 **Enforce HTTPS**。绑定完成后重新运行 Pages workflow，更新资源的基础路径。
本仓库使用 Actions 发布，GitHub 不要求 `CNAME` 文件；域名配置以仓库 Pages 设置为准。

## 下载与 playground

编译器下载入口指向 [Xu GitHub Releases](https://github.com/xulang-org/xu/releases)。
编译器二进制和本地 `www/releases/` 不提交，也不会打包到官网。

Pages workflow 使用校验和固定的公开 Xu 0.8.3 产品发行包。
Xu 编译器先编译 `playground/compiler/emit_wasm.xu`（隔离的驱动扩展），
再将 `playground/runtime/*.xu` 和产品 Xu 前端编译成 `xu-play.wasm`。
解析器、类型与借用检查器、MIR 解释器、信道调度及内存/字符串支持均为 Xu 源码；
构建链不需要 Rust、LLVM、Emscripten 或 bootstrap 仓库。
发布构建使用 `--require-playground`；运行器缺失时构建失败。

```sh
make wasm                      # 下载固定 Xu 发布包并构建；需要联网
XU_PLAYGROUND_SEED=/path/to/xu-bundle make wasm # 使用已有产品发行包
make check-playground           # Node.js 运行真实 WASM 与首页示例
make build
```

生成的 `www/xu-play.wasm` 与 `build/` 不提交。普通 `make build` / `make check`
仍只需 Python；本地没有 WASM 时保留未启用提示。

WASM 后端目前作为官网独立构建扩展维护；已发布 Xu 的普通 CLI 尚未提供
`--target wasm32`。`scripts/prepare_wasm_compiler.py` 在忽略目录复制产品驱动，
接入本仓库的 Xu 后端，原产品源码和安装的 Xu 编译器保持原样。

用户代码在独立 Web Worker 中经过真实 Xu 解析、检查与 MIR 解释执行。
每次运行创建独立的 64 MiB WASM arena，源码上限 128 KiB，输出上限 256 KiB；
支持停止、10 秒超时和执行步数限制，源码不发往服务器。
`www/xu-play-runtime.mjs` 只负责编码、内存 ABI 和输出读取，JavaScript 不解释 Xu。

19 个在线示例覆盖基本类型、控制流、递归、数组、枚举、结构体、断言、借用诊断，
以及 chan 缓冲收发、多 worker 汇总和生产者流水线。
示例定义在 `www/xu-play-examples.json`，中英文标题和说明从同一份数据生成。
协程由 Xu 执行器协作调度，支持有缓冲和无缓冲信道、关闭和死锁诊断；
浏览器不提供文件、网络或完整标准库。未实现的 MIR 操作返回明确诊断。
教程 10 和 `www/examples/chan-*/main.xu` 保留可下载的三个本机程序。
`make check-chan XU_ROOT=/path/to/xu` 用产品编译器编译并验证这些程序。

## 内容维护

```sh
make api XU_ROOT=/path/to/xu XU_PACKAGES_ROOT=/path/to/packages
# 从编译器与扩展包源码重建 API 正文、索引和统计；构建官网无需执行
```

`scripts/gen-api.py` 提取标准库、UI 与 packages 的公开声明，跳过编译器内部包、
测试夹具和测试源码。中英文 API 正文、索引与统计一起生成，扩展包使用完整导入路径。
`docs/modules`、`docs/packages` 说明模块依赖及驱动范围；教程命令在独立 examples
仓库根执行。源码文档版本与实际已发布的下载附件分别说明。

`xu.xun` 的 `version:` 和根 `VERSION` 是官网版本，`xu:` 记录内容对应的 Xu 版本。
官网头部与页脚从 `xu:` 读取语言版本。

原 Xu HTTP 服务源码保留用于兼容本地开发，可执行 `make run-http`。
GitHub Pages 的构建和部署均使用静态流程。
