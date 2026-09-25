# 随想后端 · 密码管理

> 已停用：笔记站现使用 Markdown 静态卡片，不再加载此服务。下文仅保留旧方案说明；当前写作流程见仓库根目录“随想写作说明.md”。

公开帖子所有人可读；输入管理密码后，才能在笔记网页里发布、编辑、删除和查看草稿。正文是保留换行的纯文本，不执行 HTML，也不解析 Markdown。

不再需要 GitHub OAuth、Client Secret 或回调配置。**知道管理密码的人就具有完整管理权限**，不是按 GitHub 账号区分权限。请只由本人保管密码。

## 部署

1. 在校内服务器或自己的服务器运行本服务。已有可用的校内 HTTPS 地址可以复用，不必另外购买域名；访问者的浏览器必须能连接这个 API。GitHub Pages 仅托管网页，不转发 API，也不能穿透校内网络。
2. 复制本目录的 `.env.example` 为 `.env`（已被 Git 忽略）。
3. 在可信电脑/服务器上执行 `python passwords.py`，交互输入两次至少 16 字符的随机管理密码。把输出的一行散列配置保存到服务器 `.env`。**保留输出的单引号**，避免 Docker Compose 把散列中的美元符号当变量。不要把明文密码写进命令、网页、Git 或聊天。
4. 设置 `THOUGHTS_FRONTEND_URL` 为实际随想页面的完整 URL；它确定唯一允许的浏览器来源。默认示例指向线上笔记。
5. 运行 `docker compose up -d --build`。SQLite 使用已有 `thoughts-data` volume；这次升级保留所有帖子，不重建数据库。
6. 使用 HTTPS 反向代理接入 `127.0.0.1:8770`。`nginx.example.conf` 是独立虚拟主机示例，按实际入口/证书合并，不能覆盖现有 Nginx 主配置。可以使用已有 HTTPS 入口，不强制新域名。
7. 设置根目录 `mkdocs.yml` 的 `extra.thoughts_api` 为 API 地址，重新构建并部署笔记。未设置时页面仍显示“服务尚未连接”，不会模拟成功。
8. 真实验收：无痕窗口无需密码可读公开帖子、不能读草稿或写入；管理密码可解锁；退出后只读；重启服务后帖子仍在。

Docker 环境也可先构建再交互生成散列（不需要安装宿主 Python）：

```sh
docker build -t notes-thoughts .
docker run --rm -it --entrypoint python notes-thoughts passwords.py
```

## 更换密码与退出

重新执行 `passwords.py`，替换 `.env` 中的散列，然后运行 `docker compose up -d --force-recreate`。不要只执行 restart：容器需要重新读取环境配置。

新的散列会使所有旧会话失效，之前 OAuth 会话也不能用于密码管理。退出按钮撤销当前会话；未退出的会话最长有效 12 小时。没有默认密码、网页重置入口或后门；忘记密码时通过服务器重新配置。

## 安全与运行

- 密码散列使用带随机盐的 scrypt（N=131072、r=8、p=1、32 字节输出），依据 [OWASP 密码存储建议](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)。不存明文，也不用快速 SHA-256 直接散列密码。单次验证约需 128 MiB 工作内存，应给服务预留足够内存。
- API 验证密码后签发随机会话。数据库只存会话令牌的 SHA-256 和凭据指纹；密码修改、会话过期或退出后，服务端拒绝所有管理请求。
- 每来源 15 分钟最多 5 次登录尝试，全局最多 30 次（成功也计入），SQLite 持久化限速，重启不能清空限制。单进程同一时间只做一次 scrypt 验证；高并发尝试返回 429。
- 默认不手工信任 X-Forwarded-For。容器经过代理时可能把所有人计作同一来源，限制会偏保守；若需要区分真实来源，只将 Uvicorn 的可信代理列表配置为确切的 Nginx 地址，绝不能设为通配符，并确保代理覆盖来自客户端的转发头。应用全局限制始终保留。
- Nginx 还应限制请求体和登录频率。不要记录请求体、Authorization 或密码，容器默认禁用访问日志。公网必须使用 HTTPS，不能从 HTTPS 笔记页直连 HTTP 后端。
- 密码不会写入浏览器 localStorage/sessionStorage；会话令牌存于当前标签页 sessionStorage，解决跨站 Cookie 限制。浏览器密码管理器可以按你的设置保存密码。本站脚本必须可信，防止同源 XSS 窃取会话。
- CORS 仅允许配置的前端 origin；CORS 不是鉴权，写入和草稿接口始终校验会话。
- 编辑框暂存于此浏览器 localStorage（未加密），退出时保留以免丢稿。共享电脑勿写敏感内容；需要清除时删除该站点的本地数据。服务器草稿不对匿名用户提供。
- 已发布帖子保存为草稿即撤下；删除需要确认。版本检查防止旧页面覆盖更新，列表采用游标分页。
- SQLite 持久化在 `thoughts-data` volume。不要运行 `docker compose down -v`。定期用 SQLite backup API 备份；WAL 模式不要只复制正在写入的 db 文件。备份包含草稿和会话数据，必须限制权限。
- 当前按单实例设计；不要直接扩成多副本或多 worker，需先评估全局验证并发、数据库和限速。

## 本地测试

从仓库根目录运行：

```powershell
uv run --with fastapi --with httpx --with pytest python -m pytest services/thoughts/test_app.py -q
```

浏览器回归：在 `localhost:8769` 运行 MkDocs 构建后的静态站，安装 Playwright，执行 `node services/thoughts/test_browser.cjs`。可以用 `PLAYWRIGHT_MODULE` 指定已有模块。脚本仅拦截浏览器请求注入临时数据，不写真实数据库，也不代替部署后的验收。

本地启动（在本目录；无密码配置时可公开读取，登录返回 503）：

```powershell
uv run --with fastapi --with uvicorn python -m uvicorn app:app --host 127.0.0.1 --port 8770 --no-access-log
```

本地带密码测试需要把散列设置为进程环境变量 `THOUGHTS_PASSWORD_HASH`；Uvicorn 不会自动读取 Compose 的 .env。生产不要使用本地默认前端 URL。
