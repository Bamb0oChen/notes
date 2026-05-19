# 前言
（Agent开发时请忽略****框选部分）
****
我一直觉得，现当代的学习和传统的学习方式有了翻天覆地的变化，人类的历史从教育诞生开始经历了工业化，信息化，和人工智能的迅猛发展，但是我们的教育架构仍然停留在工业化的教育流水线，仅在一些形式上体现出信息化的感觉——小测变成了线上，讲义变成了回放，板书变成了PPT；但是最本质的一套从来没有发生任何的变化——绩点，分数，以及围绕着加分的各种比赛和活动

与此同时，人类寻求安逸的本性又让AI的使用成为了一种普遍的情况，水课上学生用AI生成的课件讲述AI的危害，老师用AI批改来节省效率，这一切形成了一种可笑而又可悲的闭环

学习的本质真的如此吗？考试的本质是什么？当面对着试题复习的人拿到了远超每天去上课的人的分数，当AI能几分钟内总结出教授都不会给出的讲义和复习方案，当半学期的内容能在三天内被突击完，我们是否需要用另一种视角去审视我们的教育？

很多时候我们的教育被分数解构，把学习的结果当成了学习的本质，这本质上也是一种被分数的异化

我一直信奉着效率至上，这些笔记大多都是在复习的过程中为了加深记忆而留下的思想痕迹——当然杂谈文章不是——希望也能帮到你的学习
****



## 基本架构

本仓库是一个基于 **MkDocs + Material for MkDocs** 的个人学习笔记站点。

目标：
- 约束“每个目录放什么、谁是源文件、谁是构建产物”
- 统一构建/预览/发布流程
- 统一 Markdown 基本格式（标题、链接、数学公式、资源文件）
- 方便后续 Agent 在不破坏站点结构的前提下增量开发

---

## 1. 目录结构规范（最重要）

> 结论：**`docs/` 是唯一内容源目录**；`site/` 是构建产物；不要手改构建产物。

| 路径 | 类型 | 说明 | 规则 |
|---|---|---|---|
| `mkdocs.yml` | 配置 | MkDocs 站点配置（主题/插件/MathJax/评论等） | 修改需谨慎，优先保持“最小可用” |
| `requirements-mkdocs.txt` | 依赖 | 构建站点所需 Python 包 | `pip install -r requirements-mkdocs.txt` |
| `docs/` | **源** | 所有可渲染的 Markdown、图片、PDF 等资源 | **所有页面/资源都应落在这里** |
| `docs/index.md` | **源** | 首页 | 推荐只放总入口、更新日志 |
| `docs/assets/` | **源** | 站点静态资源（CSS/JS/PDF） | 仅存放静态文件，不放正文笔记 |
| `docs/assets/stylesheets/` | 源 | 自定义 CSS（Material 变量覆写等） | 不要在 Markdown 里写大量 style |
| `docs/assets/javascripts/` | 源 | 自定义 JS（含 MathJax 配置） | 保持轻量，避免引入复杂前端框架 |
| `docs/assets/pdfs/` | 源 | PDF 论文/资料 | 文件名尽量简洁；中文名允许 |
| `docs/images/` | 源 | 图片资源（可按主题再分子目录） | 统一引用相对路径 |
| `overrides/` | 源 | Material 主题覆盖（Jinja2 模板） | 仅做必要覆盖，避免大改主题 |
| `overrides/partials/comments.html` | 源 | Giscus 评论区模板 | 与 `mkdocs.yml -> extra.giscus` 配合 |
| `scripts/` | 工具 | 迁移/修复脚本（辅助维护） | 脚本可改，但需写清用途 |
| `site/` | **产物** | `mkdocs build` 输出（静态站） | **不要手改**；必要时可删除再构建 |
| `.venv/` | 本地 | Python 虚拟环境 | 不提交（已在 `.gitignore`） |
| `node_modules/`、`package-lock.json` | 遗留 | 早期 Vite/Vue 相关（已忽略） | 当前站点不依赖 Node 构建 |

---

## 2. 构建与本地预览

### 2.1 Python 环境（Windows / PowerShell）

建议使用仓库内虚拟环境：

```powershell
python -m venv .venv
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .\.venv\Scripts\Activate.ps1)
pip install -r requirements-mkdocs.txt
```

### 2.2 本地预览（开发）

```powershell
mkdocs serve
```

然后浏览器打开命令行输出的本地地址（默认 `http://127.0.0.1:8000/`）。

### 2.3 构建静态站（产出 `site/`）

```powershell
mkdocs build
```

说明：
- `site/` 可重复生成；构建前后 diff 不应包含手工编辑 `site/` 的改动。

---

## 3. 发布逻辑（GitHub Pages）

当前 `mkdocs.yml` 中已设置：
- `site_url: https://Bamb0oChen.github.io/notes/`

建议发布流程（不强制，按你的 CI 实际情况调整）：
1. 本地 `mkdocs build` 确保无报错
2. 将生成的 `site/` 推送到 GitHub Pages 对应分支/目录（常见是 `gh-pages` 分支）

如果你后续要接入 GitHub Actions 自动发布，建议再新增：
- `.github/workflows/xxx.yml`（统一用 Python 安装依赖 + `mkdocs build` + 发布）

---

## 4. 内容组织规范（给 Agent 的“写入规则”）

### 4.1 页面与目录

- **每一类内容一个顶层目录**（例如 `docs/计算机科学/`、`docs/数学基础/`、`docs/英文学习/` 等）。
- 每个目录建议提供一个入口页：
  - 优先命名为 `index.md`（推荐）
  - 若历史原因存在 `README.md`，可以通过脚本生成对应 `index.md`（见 6.2）。
- 文件命名：
  - 允许中文文件名
  - 尽量稳定，避免频繁重命名（会影响站内链接与评论映射路径）

### 4.2 论文（PDF）收录规范

- PDF 统一放在：`docs/assets/pdfs/`
- 为某一组论文建立入口页（例：`docs/计算机科学/论文精选/index.md`），用列表链接到 PDF。

在 Markdown 中链接 PDF（推荐相对路径）：

```md
- [Transformer（PDF）](../../assets/pdfs/Transformer.pdf)
```

### 4.3 图片与其它资源

- 图片建议放：`docs/images/`（或更细的子目录）
- 资源引用一律使用相对路径，避免硬编码域名。

---

## 5. Markdown 基本格式约定

### 5.1 标题层级

- 每个页面**只出现一个** `# 一级标题`
- 章节从 `##` 开始

### 5.2 代码块

- 使用 fenced code block：

```md
```python
print("hello")
```
```

- 行内代码使用反引号：`like this`

### 5.3 数学公式（MathJax 3 + arithmatex）

本仓库已启用：
- `pymdownx.arithmatex`（MkDocs 端）
- `docs/assets/javascripts/extra.js` 中的 MathJax 配置

约定：
- 行内公式：`$ ... $`
- 块级公式：

```md
$$
...
$$
```

常见坑：
- 避免写成 `$a$$b$`（会导致解析混乱）；需要时写 `$a$ $b$`
- 尽量不要让单个 `$...$` 跨多行

---

## 6. 维护脚本（scripts/）

### 6.1 `scripts/fix_math_dollars.py`

用途：保守修复 Markdown 中常见的 `$` 分隔符问题（只改空白/换行，不改公式内容），避免 MathJax 解析失败。

用法：

```powershell
python scripts/fix_math_dollars.py --check
python scripts/fix_math_dollars.py
```

默认会处理 `docs/**/*.md`，并跳过 `docs/assets/**`。

### 6.2 `scripts/mkdocs_migrate.py`

用途：从旧目录（默认 `public/`）迁移到 `docs/`（复制，不修改源），并为包含 `README.md` 的目录生成 `index.md`。

用法：

```powershell
python scripts/mkdocs_migrate.py --dry-run
python scripts/mkdocs_migrate.py
python scripts/mkdocs_migrate.py --src public --dst docs --backup
```

### 6.3 `scripts/copy-manifest.cjs`（遗留）

用途：早期 Vite 构建时复制 `manifest.json`，当前 MkDocs 站点一般不需要。

---

## 7. 主题与评论

- 主题：Material for MkDocs（深色/浅色双方案）
- 自定义 CSS：`docs/assets/stylesheets/extra.css`
- 自定义 JS（含 MathJax）：`docs/assets/javascripts/extra.js`
- 评论（Giscus）：
  - 配置在 `mkdocs.yml -> extra.giscus`
  - 模板覆盖在 `overrides/partials/comments.html`

注意：Giscus 的 `mapping: pathname` 会将“页面路径”作为映射键，因此：
- 不建议频繁重命名/移动页面
- 若确需调整路径，考虑接受历史评论无法自动迁移的影响

---

## 8. Agent 工作清单（改动前自检）

1. 只改 `docs/`、`mkdocs.yml`、`overrides/`、`scripts/` 这类源文件；不要手改 `site/`
2. 新增内容必须落到正确目录，并在对应目录的 `index.md` 里补入口链接
3. 若页面包含大量公式，优先运行一次 `python scripts/fix_math_dollars.py --check`
4. 本地 `mkdocs build` 保证退出码为 0

---

## 9. 常用命令速查

```powershell
# 进入 venv
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .\.venv\Scripts\Activate.ps1)

# 安装依赖
pip install -r requirements-mkdocs.txt

# 本地预览
mkdocs serve

# 构建
mkdocs build

# 数学公式分隔符检查/修复
python scripts/fix_math_dollars.py --check
python scripts/fix_math_dollars.py
```
