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
