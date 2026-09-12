# 笔记站第一轮排查与修复

日期：2026-09-12。范围：Markdown、构建产物中的图片/正文链接、粘贴配置、空白页和发布检查。

## 排查结果

- 扫描 163 篇 Markdown；原构建生成 164 个 HTML 文件（含 404 页）。
- 按页面去重后检查 504 个图片引用、3291 个正文链接。
- 发现 14 个失效页面链接、5 个失效锚点。没有发现本地图片缺失、大小写不匹配或图片使用本机绝对路径。
- 9 个外链图片地址使用带站点 Referer 的 GET Range 请求，均返回 206 与 image/png 或 image/jpeg 内容类型。此结果验证资源可访问，不等于浏览器完整显示验收。
- 发现 6 个内容为空的 Markdown 页面。

## 已完成修复

| 文件 | 问题 | 处理 |
| --- | --- | --- |
| `docs/英文学习/CET-6/索引.md` | 10 个链接仍带旧的 English/CET-6 前缀；1 个文件名误写为 transition | 改为同目录相对链接，修正为 translation_and_writing8.md |
| `docs/计算机科学/Cursh Course CS/索引.md` | 两个“待更新”条目链接到不存在的页面 | 保留原文字，去掉失效链接 |
| `docs/计算机科学/Stanford CS224n/CS224N详细笔记.md` | pybasis.md 不存在 | 核对同目录 NumPy/PyTorch 笔记后，链接至 python进阶.md |
| `docs/计算机科学/MIT Missing Semester/LECTURE 4 debugging & profilling.md` | 手写目录的 5 个中文锚点不存在 | 在对应段落前添加显式锚点，保留目录和正文文字 |
| `mkdocs.yml` | 空白页随自动导航进入网站 | 排除以下 6 页，保留原文件 |
| `.github/workflows/deploy.yml`、`mkdocs.yml` | 失效链接告警不阻止发布 | 使用严格构建，并将锚点校验提升为告警 |

暂不发布的空白页：

- 数学基础/二元微积分/5.二类曲线积分和曲面积分.md
- 数学基础/概率论与数理统计/第9章 区间估计和假设检验.md
- 计算机科学/ZJU HPC101/Lecture 7 CUDA基础.md
- 计算机科学/ZJU HPC101/Lecture 8 机器学习基础.md
- 计算机科学/ZJU HPC101/Lecture 9 机器学习高级话题.md
- 计算机科学/ZJU HPC101/华为ICT架构学习.md

以后写完这些页面，应从 `exclude_docs` 清单中移除对应条目。

## 配置核对

笔记仓库的 Paste Image 配置为 `${projectRoot}/docs/images`，相对路径基准为 `${currentFileDir}`；父级 asserts 工作区对应配置为 `${projectRoot}/notes-main/docs/images`。两种打开方式都有匹配配置，本轮无需修改。

现有 `.venv` 仍指向另一用户目录中的 Python 3.14，无法启动。本次使用独立临时环境进行验证，没有替换或删除原环境。验证版本为 MkDocs 1.6.1、Material 9.7.7。

保留用户未提交的 `docs/images/2026-09-12-17-44-42.png`，不纳入本次提交。

## 修复后验证

- `mkdocs build --strict` 通过，无文档链接/锚点告警。
- 生成 158 个 HTML 文件（157 个内容页与 404 页），空白页不再生成。
- 再次核对 504 个图片引用和 3289 个正文链接：本地文件及锚点问题为 0。
- `git diff --check` 通过。

## 后续施工建议

1. 在浏览器中实测 Missing Semester、CSAPP、CS224n、六级索引的图片、公式和手机横向溢出；当前检查尚未覆盖视觉与交互验收。
2. `英文学习/CET-6/word1.md`、`word2.md` 与 `计算机科学/Stanford CS224n/python进阶.md` 含有 `[cite_start]`、`[cite: ...]` 原始引用标记。后续核对原始资料，决定补真实引用还是清理展示标记，本轮不更改这些正文。
3. 构建依赖当前只有版本下限。后续可记录完整依赖锁定，并单独维护升级流程。

本轮不校订知识内容、不补写空白章节；线上部署结果与浏览器视觉检查需要与本地构建结果分开记录。
