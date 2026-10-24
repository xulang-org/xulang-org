# 参与 xulang.org 开发

请先阅读 [XU GitHub 仓库管理规范](.github/REPOSITORY_RULES.md)；维护者另见 [GitHub 配置与验收清单](.github/GITHUB_SETTINGS.md)。规范适用于 XU 全部仓库，本文件补充官网的实际入口。

XU 源码还须遵守 [XU 代码规范](https://github.com/xulang-org/xu/blob/main/.github/XU_CODING_STANDARDS.md)；涉及配套语言或跨语言接口时，按各语言工具链及其中的边界契约验证。

日常开发从 `dev` 建立任务分支并通过 PR 合回；正式部署进入 `main`。独立文档、链接或治理修订可按统一规范通过维护 PR 进入 `main`。若尚未启用对应分支与门禁，先由维护者按配置清单完成衔接。不得直接推送或擅自触发发布。

## 修改与验证

在仓库根执行；静态站点需要 Python 3.10+，无须 Xu、Node.js 或伙伴仓库：

```sh
make build
make check
make build BASE_PATH=/xulang-org
```

修改演练场或 API 生成时，按 README 准备所选正式 SDK 和示例源码，补充运行适用检查：

```sh
make wasm
make check-playground
make check-chan
```

`make check-playground` 需要 Node.js；WASM 与原生检查使用实际选定的 Xu SDK。仅修改仓库规则和模板时，核对 Markdown 链接、Issue 表单与各仓库模板一致性即可。

官网根 `VERSION`、根 `xu.xun` 的 `version:` 与 `xu:` 跟随选定的正式 SDK；不因正文或治理修订独立升级。运行器模块的自身版本另行维护。公开正文位于 `content/{en,zh}/`；本机研发材料和生成产物保持忽略。

## 提交 PR

使用 Issue 表单报告缺陷或提议功能、文档改进。PR 写明问题与结果、目标分支、SDK 与模块版本影响、实际验证结果及回滚方法；没有执行的检查如实标注。`main` 的合并可能触发 GitHub Pages 部署，合并前须核对发布范围。
