# Git：代码的存档系统

在开始学指令以前，我们先讲清楚 Git、GitHub 和 GitLab 到底是什么。

## 什么是 Git？

我们写代码的时候肯定遇到过这种文件：

```text
实验报告.docx
实验报告最终版.docx
实验报告最终版2.docx
实验报告真的最终版.docx
```

这种做法其实是在手动保存文件的不同版本，但是时间久了以后，我们很难知道每一版修改了什么，也不知道哪一版能够正常运行。

Git 就是专门解决这个问题的工具。

Git 是一个**分布式版本控制系统**。它会记录文件在不同时间点的状态，让我们可以查看修改、保存版本、建立分支，也可以在写坏以后回到之前的状态。

注意，Git 并不是自动保存软件。你修改文件以后，需要主动选择要记录的内容，再创建一次提交。

```text
工作区中的文件
      ↓ git add
暂存区中的修改
      ↓ git commit
Git 仓库中的一个新版本
```

其中：

- **工作区（working tree）**：我们正在编辑的文件。
- **暂存区（staging area）**：准备放进下一次提交的修改。
- **提交（commit）**：一次有说明、有编号的版本记录。
- **仓库（repository）**：项目的文件和全部 Git 历史。

所以一次最基础的 Git 操作是：

```bash
git status
git add <文件名>
git commit -m "说明这次做了什么"
```

`git status` 用来看现在有哪些文件发生了变化；`git add` 决定哪些变化进入下一次提交；`git commit` 则真正创建一个可以查找和回退的版本。

## Git 为什么是“分布式”的？

Git 仓库不只存在于某一台中央服务器上。

当我们把一个 Git 仓库完整地克隆到本地时，本地不只有最新的文件，还有项目的提交历史。即使暂时没有网络，我们仍然可以查看记录、建立分支和创建提交。

远端仓库主要负责让不同电脑和不同开发者交换这些提交：

```text
本地仓库  ← git fetch / git pull — 远端仓库
本地仓库  ———— git push ————→ 远端仓库
```

我们经常把远端仓库放在 GitHub 或 GitLab 上，但这并不意味着 Git 必须联网，也不意味着 Git 就是 GitHub。

## 什么是 GitHub？

[GitHub](https://github.com/) 是一个托管 Git 仓库的网站。

除了替我们保存远端仓库，它还提供了很多围绕软件协作的功能：

- Pull Request：讨论和合并代码修改；
- Issue：记录 bug、需求和任务；
- Actions：自动测试、构建和部署项目；
- Releases：发布软件版本和安装包；
- Pages：托管静态网站。

你可以只在本地使用 Git 而完全不用 GitHub，也可以把同一个本地 Git 仓库托管到其他平台。

## 什么是 GitLab？

[GitLab](https://gitlab.com/) 同样是围绕 Git 仓库建立的协作平台。

它提供代码托管、Issue、代码审查、CI/CD 等功能。GitLab 中通常把类似 GitHub Pull Request 的功能叫作 **Merge Request**。

GitHub 和 GitLab 的关系有点像两个提供相近服务的网站：它们都使用 Git，但它们本身都不是 Git。

简单来说：

| 名称 | 它是什么 | 没有网络能否使用 |
|---|---|---|
| Git | 安装在电脑上的版本控制工具 | 可以 |
| GitHub | 提供 Git 仓库托管和协作功能的平台 | 通常不可以 |
| GitLab | 提供 Git 仓库托管和协作功能的平台，也支持自行部署 | 通常不可以 |

## 仓库、提交和分支

我们可以把一次 commit 想成一个存档点。每个提交都会记录它的上一个提交，于是许多提交连接成了一条历史。

```text
A ← B ← C
        ↑
       main
```

`main` 是一个分支名，它指向提交 `C`。分支并不是把整个项目复制一遍，而是一个会随着新提交移动的指针。

如果我们从 `C` 建立一个新分支并继续开发，就可能得到：

```text
A ← B ← C ← D        main
         \
          E ← F      feature
```

这样我们可以在 `feature` 上尝试新功能，而不影响 `main` 上相对稳定的代码。完成以后，再通过 merge 或 rebase 整理两边的历史。

这部分只看文字很难建立直觉，所以不再重复做一套本地实验。直接使用 Learn Git Branching 会更加清楚。

## 学习资料

- [Learn Git Branching](https://learngitbranching.js.org/?demo=&locale=zh_CN)：用游戏来解决 git，全流程学习大概 5 小时

建议至少完成基础篇中的 commit、branch、merge 和 rebase。网页里的提交图会直接展示 HEAD、分支和提交如何移动。

下面保留一份完成练习以后用于复习的指令表。

| 指令 | 拓展 | 作用 |
|---|---|---|
| `git commit` |  | 基础提交 |
| `git rebase <name>` |  | 将当前分支上的提交转移到另一个基点之后 |
|  | `-i` | 交互式整理提交历史 |
| `git checkout <name>` |  | 切换到指定分支或提交 |
| `git checkout -b <name>` |  | 创建并切换到新分支 |
|  | `<name>^` | 从节点向上移动 HEAD |
|  | `<name>~<num>` | 从节点向上移动 n 次 HEAD |
| `git revert <commit>` |  | 创建一个新提交，反向撤销指定提交的修改 |
| `git reset <commit>` |  | 移动当前分支指针，并按参数决定如何处理修改 |
|  | `--soft` | 保留暂存更改 |
|  | `--hard` | 同时重置暂存区和工作区，会丢弃未提交修改 |
|  | `--mixed` | 保留工作区，重置暂存区 |
| `git cherry-pick <commit1> <commit2> ....` |  | 复制粘贴你想要的 commit |
| `git tag <tag> <commit>` |  | 增加 tag |
| `git describe <branch>` |  | 在链上查找到最近的 tag |
| `<remote name>/<branch name>` |  | 远端跟踪分支，例如 `origin/main` |
| `git fetch` |  | 下载远端的新提交和引用，但不修改当前工作区 |
| `git pull` |  | 获取远端更新并合并到当前分支 |
|  | `--rebase` | 先 fetch 再 rebase |
| `git push` |  | 从本地到云端 |

`git fakeTeamwork` 是 Learn Git Branching 为模拟远端协作提供的教学命令，并不是真实 Git 中的命令。

当然，我们 Git 的 commit 命名也存在着规范。

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
