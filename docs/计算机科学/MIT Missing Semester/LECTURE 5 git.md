学习资料：

- [Learn Git Branching](https://learngitbranching.js.org/?demo=&locale=zh_CN)：用游戏来解决 git，全流程学习大概 5 小时

| 指令 | 拓展 | 作用 |
|---|---|---|
| `git commit` |  | 基础提交 |
| `git rebase` |  | 将提交链转移到某此提交 |
|  | `-i` | 打开可视化界面 |
| `git checkout <name>` | `-b` | 创建并转移到分支中 |
|  | `<name>^` | 从节点向上移动 HEAD |
|  | `<name>~<num>` | 从节点向上移动 n 次 HEAD |
| `git revert <branch>` |  | 重新创建一个新提交，覆盖原先的提交 |
| `git reset <name>` |  | 更改提交为未提交状态 |
|  | `--soft` | 保留暂存更改 |
|  | `--hard` | 删除暂存更改 |
|  | `--mixed` | 保留工作区，重置暂存区 |
| `git cherry-pick <commit1> <commit2> ....` |  | 复制粘贴你想要的 commit |
| `git tag <tag> <commit>` |  | 增加 tag |
| `git describe <branch>` |  | 在链上查找到最近的 tag |
| `<remote name>/<branch name>` |  | 仓库/分支 |
| `git fetch` |  | 下载未同步的操作 |
| `git pull` |  | fetch 和 merge 的缩写 |
|  | `--rebase` | 先 fetch 再 rebase |
| `git fakeTeamwork` |  | 在远端仓库做一次提交 |
|  | `<name> <nums>` | 指定次数 |
| `git push` |  | 从本地到云端 |

当然，我们git的commit开发命名也存在着规范

| 类别 | 含义 | 示例 |
| :--- | :--- | :--- |
| feat | 新功能（feature） | `feat: 增加用户注册功能` |
| fix | 修复 bug | `fix: 修复登录页面崩溃的问题` |
| docs | 文档变更 | `docs: 更新README文件` |
| style | 代码风格变动（不影响代码逻辑） | `style: 删除多余的空行` |
| refactor | 代码重构（既不是新增功能也不是修复bug的代码更改） | `refactor: 重构用户验证逻辑` |
| perf | 性能优化 | `perf: 优化图片加载速度` |
| test | 添加或修改测试 | `test: 增加用户模块的单元测试` |
| chore | 杂项（构建过程或辅助工具的变动） | `chore: 更新依赖库` |
| build | 构建系统或外部依赖项的变更 | `build: 升级webpack到版本5` |
| ci | 持续集成配置的变更 | `ci: 修改GitHub Actions配置文件` |
| revert | 回滚之前的提交 | `revert: 回滚feat: 增加用户注册功能` |