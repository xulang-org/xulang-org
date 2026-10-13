# xulang-org

Xu 官网源码，使用 GitHub Pages 托管。默认中文，英文入口为 `/en/`，计划绑定域名 `xulang.org`。

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

首页 playground 是可选的浏览器 WASM 运行器。若构建输入包含 `www/xu-play.wasm`，
构建会带上该文件；没有 WASM 时，页面说明在线运行尚未启用，运行按钮禁用。
普通 GitHub checkout 不含该生成文件，因此默认 Pages 部署不启用在线运行。
需要启用时，由独立的 WASM 发布流程在 `make build` 前提供该文件。
本机构建可以运行 `make wasm XU_ROOT=/path/to/xu`，再执行 `make build`。

## 内容维护

```sh
make api XU_ROOT=/path/to/xu    # 从 Xu 源码重建 API 正文；构建官网无需执行
```

`scripts/gen-api.py` 提取公开声明，跳过 `src/cmd/**` 和 `test_*.xu`，
不覆盖手写的 API 索引。中文与英文页面都应保留。

`xu.xun` 的 `version:` 和根 `VERSION` 是官网版本，`xu:` 记录内容对应的 Xu 版本。
官网头部与页脚从 `xu:` 读取语言版本。

原 Xu HTTP 服务源码保留用于兼容本地开发，可执行 `make run-http`。
GitHub Pages 的构建和部署均使用静态流程。
