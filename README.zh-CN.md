<p align="center">
  <a href="https://xulang.org"><img src="www/xu_classic.svg" alt="Xu Logo" width="100" height="100"></a>
</p>

<h1 align="center">xulang-org</h1>

<p align="center">
  <a href="README.md">English</a> | <b>简体中文</b>
</p>

<p align="center">
  <a href="https://xulang.org"><img src="https://img.shields.io/badge/site-xulang.org-rose" alt="Site"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://github.com/xulang-org/xulang-org/actions/workflows/pages.yml"><img src="https://github.com/xulang-org/xulang-org/actions/workflows/pages.yml/badge.svg" alt="Pages CI"></a>
</p>

Xu 官方网站源码仓库，托管于 GitHub Pages，生产环境域名为 [`xulang.org`](https://xulang.org)。站点默认语言为英文，中文入口为 `/zh/`；页面右上角提供无损路径的语言切换按钮。

官方帐号入口统一展示在所有页面的顶部与页脚：
- GitHub: [@xulang-org](https://github.com/xulang-org)
- X (Twitter): [@xulang_org](https://x.com/xulang_org)

## 目录结构

| 目录 / 文件 | 说明 |
| --- | --- |
| `content/{zh,en}/` | 中英文文档、教程、博客与 API 正文源码 |
| `templates/` | HTML 页面结构模板 |
| `www/` | CSS、JavaScript、矢量字体、图标与静态资产 |
| `playground/runtime/` | 由 Xu 编写的浏览器客户端 WebAssembly 运行器沙箱 |
| `scripts/` | 静态页面构建、WebAssembly 编译、API 生成与发布校验工具 |
| `tests/` | 静态路由、在线演练场与并发信道示例测试套件 |
| `brand/` | Xu 官方品牌物料与 VI 资产 |

生成文件统一输出至被忽略的 `dist/` 与 `build/` 目录中。

## 本地构建与预览

需要 Python 3.10 或更高版本（仅使用标准库，无需外部三方依赖）：

```sh
make build                      # 构建至 dist/，检查页面与资源完整性
make run                        # 启动本地实时预览：http://127.0.0.1:8080
make run PORT=18080             # 指定端口预览
make check                      # 执行全量单元测试与路由校验
make build BASE_PATH=/xulang-org # 指定项目子路径构建
make clean                      # 清理 dist/ 和 build/playground/
```

静态构建无需配置编译器或相邻仓库。`content/` 中的 HTML 正文片段以 `<!--title: ...-->` 指定标题，自动渲染并生成标准美化路径。

## WebAssembly 在线演练场

演练场运行器由 Xu 源码直接 AOT 编译输出至 WebAssembly：

```sh
make wasm                           # 本地编译 xu-play.wasm
make check-playground                # Node.js 环境下测试真实 WASM 与交互逻辑
make check-chan                      # 验证原生信道并发示例
make build                          # 打包集成到 dist/
```

演练场在浏览器纯客户端内运行，无服务器计算负载，支持协程并发、信道收发与模式匹配等完整语法演练。

## GitHub Pages 自动化部署

仓库配置了 `.github/workflows/pages.yml`：
- 推送到 `main` 分支时自动触发测试、SDK 版本对齐校验、WASM 编译、静态构建与 GitHub Pages 部署；
- 自动化流水线会严格校验并下载 `xulang-org/xu` 发布的对应正式 SDK 附件及 SHA-256 签名，保障官网文档与实际编译器版本严密一致。

## 许可证

本项目采用 [MIT 许可证](LICENSE) 开源。
