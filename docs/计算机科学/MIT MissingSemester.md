这一块不止有missing semester的过程

在后期的学习中有关bash unix git相关的底层知识都放在这里

![Learn Git Branching](https://learngitbranching.js.org/?demo=&locale=zh_CN)

全流程学习大概5小时

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