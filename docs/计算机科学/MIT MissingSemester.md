这一块不止有[missing semester](https://missing-semester-cn.github.io/)的过程

在后期的学习中有关bash unix git相关的底层知识都放在这里

## LECTURE 1-2 bash shell

* **参数与通配符**：通过 `flag` 调节行为，通过 `globbing`（如 `*`, `{}`）高效批量操作。
* **流与重定向**：利用 `stdin` / `stdout` / `stderr` 和管道 `|` 实现数据流转，使用 `>` / `<` 等符号控制数据去向。
* **环境变量**：用于子进程通信与配置传递（`export`）。
* **返回码**：Shell 通过返回码（0 为成功，非 0 为失败）进行逻辑判断（`&&` / `||`）。
* **信号与控制**：通过信号（如 `SIGINT`）管理进程生命周期。

---

### 命令行环境快查单

| 指令/模式 | 拓展/参数 | 作用 |
| :--- | :--- | :--- |
| **参数/通配符** | | |
| `cmd -a` | `flags` | 修改程序行为（单字符用 `-`，长名称用 `--`） |
| `*.py` | `*` | 匹配任意字符（零个或多个） |
| `{a,b}.txt` | `{}` | 模式展开（生成 `a.txt` 和 `b.txt`） |
| `cmd --` | `--` | 终止选项解析，后面全视为位置参数 |
| **流与重定向** | | |
| `cmd1 \| cmd2` | `\|` | 管道：将 cmd1 输出作为 cmd2 输入 |
| `cmd > file` | `>` | 将标准输出（stdout）覆盖写入文件 |
| `cmd >> file` | `>>` | 将标准输出（stdout）追加写入文件 |
| `cmd 2> file` | `2>` | 将错误输出（stderr）重定向到文件 |
| `cmd &> file` | `&>` | 将 stdout 和 stderr 同时重定向到文件 |
| `cmd < file` | `<` | 将文件内容作为输入（stdin） |
| `cmd > /dev/null` | `/dev/null` | 丢弃输出（常用于静默执行） |
| **环境变量** | | |
| `foo=bar` | `=` | 定义局部变量（仅当前 shell） |
| `export VAR=val` | `export` | 设置环境变量（子进程可继承） |
| `printenv` | | 查看当前环境变量 |
| `unset VAR` | | 删除变量 |
| **返回码与逻辑** | | |
| `$?` | | 获取上一条命令的返回码（0=成功） |
| `cmd1 && cmd2` | `&&` | 仅当 cmd1 成功时，运行 cmd2 |
| `cmd1 \|\| cmd2` | `\|\|` | 仅当 cmd1 失败时，运行 cmd2 |
| **信号与任务** | | |
| `Ctrl+C` | `SIGINT` | 中断当前前台进程 |
| `Ctrl+Z` | `SIGTSTP` | 挂起当前进程 |
| `bg` | | 将挂起的任务放入后台运行 |
| `jobs` | | 查看当前 Shell 启动的后台任务 |
| `kill -9 <PID>` | `-9` | 强制终止进程 |

## LECTURE 3 Vim

学习资源：

[vimgolf](https://www.vimgolf.com/)

像一个高尔夫球手一样用最少的步数实现vim的效果！

[vim中文用户手册](https://yianwillis.github.io/vimcdoc/doc/usr_toc.html)

用中文理解vim!

* **Vim 的哲学：** 区别于常见的“非模式化编辑器”（如 VS Code、Notepad），Vim 是一个模式化编辑器。这意味着键盘不再仅仅是用来输入字符的，而是作为一种操作“语言”来控制光标移动和文本处理。
* **模式（Modes）：** * **Normal（普通模式）：** 默认模式，用于移动光标、删除、复制等操作。
    * **Insert（插入模式）：** 用于输入文本。
    * **Visual（可视模式）：** 用于选区操作。
    * **Command-line（命令行模式）：** 用于执行存盘、退出等高级指令。
* **“语法化”编辑：** Vim 的编辑命令可看作一种语言。指令由“动词”（如 `d` 删除，`c` 修改）+ “名词/移动”（如 `w` 单词，`$` 行尾）组成。通过组合这些指令，你可以极其高效地进行文本重构。
* **LSP（Language Server Protocol）：** 现代编辑器的核心，实现了代码补全、定义跳转等 IDE 级功能与编辑器的解耦，使得 Vim 等轻量级编辑器也能拥有强大的智能感知能力。

---

### 开发环境与工具（Vim 核心）快查单

| 指令 | 作用 |
|---|---|
| `<ESC>` |从任何模式返回普通模式 |
| `i` |进入插入模式 (Insert) |
| `o` / `O` |在下方/上方插入新行 |
| `h`, `j`, `k`, `l` |左, 下, 上, 右移动光标 |
| `w` / `e` |移动到下一个单词的开头/结尾 |
| `0` / `$` |移动到行首 / 行尾 |
| `G` |跳转到文件末尾 |
| `gg` |跳转到文件开头 |
| `x` |删除当前字符 |
| `d{motion}` |删除某一段（例 `dw` 删除单词, `dd` 删除整行） |
| `c{motion}` |修改某一段（例 `cw` 修改单词，进入插入模式） |
| `u` |撤销上次操作 |
| `<Ctrl> + r` |重做 (Redo) |
| `v` |进入可视模式（字符选择） |
| `V` |进入可视行模式（整行选择） |
| `Ctrl + v` |进入可视块模式（矩形选择） |
| `:` |进入命令行模式 |
| `:w` |保存文件 |
| `:q` |退出编辑器 |
| `:q!` |强制退出（不保存） |

## LECTURE 4 debugging & profilling



## LECTURE 5 git

学习资料：

[Learn Git Branching](https://learngitbranching.js.org/?demo=&locale=zh_CN)

用游戏来解决git，全流程学习大概5小时

|指令|拓展|作用|
|---|---|---|
|git commit||基础提交|
|git rebase||将提交链转移到某此提交|
||-i|打开可视化界面|
|git checkout <name>|-b|创建并转移到分支中|
||<name>^|从节点向上移动HEAD|
||<name>~<num>|从节点向上移动n次HEAD|
|git revert <branch>||重新创建一个新提交，覆盖原先的提交|
|git reset <name>||更改提交为未提交状态|
||--soft|保留暂存更改|
||--hard|删除暂存更改|
||--mixed|保留工作区，重置暂存区|
|git cherry-pick <commit1> <commit2> ....||复制粘贴你想要的commit|
|git tag <tag> <commit>||增加tag|
|git describe <branch>||在链上查找到最近的tag|
|<remote name>/<branch name>||仓库/分支|
|git fetch||下载未同步的操作|
|git pull||fetch和merge的缩写|
||-rebase|先fetch再rebase|
|git fakeTeamwork||在远端仓库做一次提交|
||<name> <nums>|指定次数|
|git push||从本地到云端|