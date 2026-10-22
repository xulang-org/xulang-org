# GitHub 仓库设置与验收清单

本文是 [XU 仓库管理规范](REPOSITORY_RULES.md) 的管理员操作清单。以下复选框均表示**待逐仓库验收的目标配置**，不是已启用状态。文档或模板不能代替后台设置。

适用活跃仓库：`xu`、`packages`、`examples`、`bench`、`vscode-xu`、`xulang-org`。`bootstrap` 保持现有归档状态。设置按仓库执行，不假设账号已具备组织级规则功能。

## 1. 启用前核对

- [ ] 使用任务授权的管理员身份，核对目标仓库、现有规则、默认分支和发布触发器；保留原设置及恢复方法。
- [ ] 先将官网仓库的统一规范与配置清单合入公开分支，确认链接可访问，再合入其他仓库的贡献入口和模板，避免跨仓库链接暂时失效。
- [ ] 确认 `main` 的正式基线；从已确认基线建立缺失的 `dev`。不混入未验收开发内容，不覆盖已有分支。
- [ ] 先让质量检查覆盖 `pull_request` 到 `main` 和 `dev`，以及需要检查的分支更新；在真实 PR 上成功运行一次。
- [ ] 检查长分支互相合并能使用 Merge commit。没有要求线性历史的旧规则阻断发布合并。
- [ ] 维护者确认当前采用单维护者还是多人审查模式；单维护者不设置无法满足的独立批准要求。
- [ ] 先核实套餐与仓库可见性支持所选功能。Rulesets 不可用时使用支持的分支保护；两者均不可用时明确记录缺口，不能宣称已有强制保护。

现有工作流要逐仓库核对，尤其 `xu/.github/workflows/ci.yml` 等文件的分支过滤；不能仅建立 `dev` 就认为它已经获得与 `main` 相同的检查。

## 2. 基础设置

在仓库 Settings → General 中配置：

- [ ] 默认分支保持 `main`，README 与贡献指南引导日常开发到 `dev`。
- [ ] 启用 Squash merge 和 Merge commit；任务 PR 使用 Squash，长期分支间同步使用 Merge commit。Rebase merge 非必要时关闭。
- [ ] 启用自动删除已合并任务分支前，先保护 `main`、`dev` 和维护分支，防止它们成为被删除的 PR 来源分支。
- [ ] 启用 Issues；确认贡献指南、Issue 表单和 PR 模板可见，问题能提交到正确仓库。
- [ ] Actions 默认令牌权限保持只读；发布或部署 job 单独声明所需写权限。
- [ ] 启用仓库支持的依赖与安全提醒。只有配置好实际可用的私密渠道后，才在公开说明中宣称支持私密漏洞报告。

### 贡献者署名核对

- [ ] 提交工具、agent、编辑器、提交模板和机器人均不会自动追加 `Co-authored-by:` 或引入未经用户明确确认的新作者身份。
- [ ] 如存在自动更新 README、网站或贡献者名单的流程，关闭未经确认的自动登记行为。
- [ ] 推送和合并前检查实际作者、提交者、作者邮箱及完整正文；特别复查 GitHub Squash merge 自动生成的最终作者和共同作者署名。
- [ ] 将身份核对纳入合并审查；若采用脚本门禁，须实际验收其覆盖范围，不能把 PR 复选框宣称为已启用的强制校验。

Contributors 由 GitHub 按提交历史生成。上述步骤控制新增署名来源，不会将图表改为手动审批，也不会清理既有历史；处理历史身份须另外取得用户授权。完整要求见 [贡献者署名规则](REPOSITORY_RULES.md#43-contributors-与贡献署名)。

## 3. 长期分支 Ruleset

在 Settings → Rules → Rulesets 为 `main`、`dev`、`maintenance/*` 建立规则，启用状态设为 Active。若使用传统 branch protection，逐项配置等价保护，并检查名称覆盖范围。

| 设置 | 目标 |
| --- | --- |
| Restrict deletions | 开启。 |
| Block force pushes | 开启。 |
| Require a pull request before merging | 开启。 |
| Require conversation resolution before merging | 开启。 |
| Require status checks to pass | 先完成第 4 节验收，再选择实际检查名。 |
| Require branches to be up to date | 存在有效必需检查后开启；分支更新后重新验证。 |
| Required approvals：单维护者 | `0`，仍要求 PR、验证证据与合并理由。 |
| Required approvals：多人协作 | 至少 `1` 位非作者批准，新的实质修改撤销旧批准。 |
| Require review from Code Owners | 仅在有效 `CODEOWNERS` 和实际可用审查者配置后开启。 |
| Require approval of the most recent reviewable push | 仅在有独立审查者时按需开启。 |
| Require linear history | 关闭，允许长期分支之间保留 Merge commit。 |
| Restrict updates | 不作为普通分支保护启用，避免正常 PR 合并也依赖旁路权限。 |
| Bypass list | 日常为空；确需应急时限于已授权发布负责人或专用 App，事后复查。 |

可选的 `release/*` 分支采用相同的 PR、检查、禁强推规则；完成发布并确认同步回 `dev` 后，由维护者按规则清理。`CODEOWNERS` 使用真实且拥有 write 权限的账号或团队，不填虚构团队，不以作者自己的批准充当独立审查。

`main` 只接收发布、hotfix 或独立维护 PR 的来源要求，还须由合并者根据规范核对；上述通用规则不自动判断分支内容是否属于正式发布。

## 4. 必需检查的选择

不要把下面的工作流名称直接填成状态检查名。GitHub 应选择实际 PR 上出现的 job/check context，矩阵任务还可能带平台后缀。不同工作流的 job 名不能含糊冲突。

| 仓库 | 检查来源与前置核对 |
| --- | --- |
| `xu` | 从 `ci.yml` 的源码契约、产品编译器验证及适用的平台或 SDK 工作流选择；先补齐 `dev` 的触发覆盖。 |
| `xulang-org` | 从 `pages.yml` 选择 PR 上实际出现的 `build` 检查；`deploy` 只在部署时运行，不设为 PR 必需。 |
| `bench` | 核查 `bench.yml` 的触发器与 job；仅手动或发布后产生的测量不设为每个 PR 的必需检查。 |
| `packages`、`examples`、`vscode-xu` | 先建立与本仓库公开构建入口匹配的 PR 验证并成功运行，再配置必需检查；没有检查时明确记录，不能填一个不存在的名称。 |

- [ ] 检查在目标分支的普通 PR、仅文档 PR 和后续提交上均能报告结果。
- [ ] 同一检查名的来源明确；如可选择来源 App，绑定实际 CI 提供方。
- [ ] 不依赖本机研发材料、Xu 本机测试目录或未提交文件。
- [ ] 失败时阻断合并；修复后最新 SHA 的检查结果才允许通过。
- [ ] 路径或分支过滤不会令必需检查一直 Pending；被跳过的 job 不能冒充实际验收。

暂无公共 CI 的仓库以 PR 中的本机验证证据作为过渡，记录缺口。完成公开、独立的检查后再启用相应强制门禁，不为迁就门禁上传本机材料。

## 5. 标签与发布权限

对 `v*` 标签建立单独 Ruleset：

- [ ] 限制更新与删除，禁止正式标签被移动或复用。
- [ ] 限制创建，仅允许被授权的发布者或发布 App。
- [ ] 标签创建权限与更新、删除权限分离。使用独立规则：创建规则可给发布者旁路，更新、删除规则不提供日常旁路，避免「可发布」同时变成「可移动旧标签」。
- [ ] 若 Release 或部署需要环境授权，确认授权人在实际协作模式下可完成审批，凭据只向发布任务开放。
- [ ] 核实 `v*` 推送、手动工作流和 Release 创建是否自动发布；任何一种触发方式都执行相同版本、验收和授权要求。

GitHub 标签保护不校验版本语义，也不能证明附件与源码一致；发布脚本和发布负责人仍须执行规范中的发行检查。

## 6. 启用后的实际验收

使用临时任务分支及测试 PR 验证，测试材料不进入长期分支，也不触发正式标签或生产发布：

- [ ] 未经 PR 的长期分支更新被拒绝，删除与强推被拒绝；若验证这些拒绝行为，先准备可恢复引用并使用测试范围，不能拿生产分支做破坏性试验。
- [ ] 未解决讨论、失败检查和缺少必需审查均阻止合并。
- [ ] 单维护者模式不会等待作者自己的批准；多人模式的独立审查确实生效。
- [ ] 任务 PR 的 Squash 与长分支同步的 Merge commit 都符合规则。
- [ ] `dev` 检查能运行；从 `dev` 合入 `main` 前能核对正式版本和发布授权。
- [ ] 普通贡献者不能创建正式标签；发布者能创建允许的标签但不能移动或删除已有标签。用不匹配生产发布触发器的测试标签规则验证权限设计。
- [ ] 关闭并清理测试 PR 和临时分支，保留设置变更、验收结果及仍未启用项的本机记录。

如果启用后阻断正常工作，先查触发器、检查名、审查资格和叠加规则，再修正配置；不能把长期绕过保护作为解决办法。

GitHub 功能依据：[Rulesets 可用规则](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)、[必需检查排障](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)、[CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)、[自动删除分支](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches)。
