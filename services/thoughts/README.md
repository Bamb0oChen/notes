# 随想后端

笔记站的「随想」页在站内写作、发布、保存草稿、修改和删除。阅读公开，不需要登录；所有写入、草稿列表均需后端签发的作者会话。正文当前是保留换行的纯文本，不执行 HTML，也不解析 Markdown。

## 发布前必须完成

1. 在自己的服务器部署此目录的服务，并通过独立 HTTPS 域名反向代理到 `127.0.0.1:8770`。服务没有预设任何现有服务器，也不会修改其他服务。
   `nginx.example.conf` 提供独立虚拟主机示例，需要自行填域名/证书并合并进现有配置，不能直接覆盖主配置。
2. 在 GitHub 创建 OAuth App。主页填笔记地址，Authorization callback URL 填 `https://你的API域名/auth/callback`。不需要 repo 权限、PAT 或 Device Flow。
3. 从 `.env.example` 复制为 `.env`，填入 OAuth Client ID / Secret、完整前端随想 URL、完整回调 URL。不要提交 `.env`。
4. 保持 `THOUGHTS_OWNER_ID=247085583`，这是当前通过 GitHub API 核实的 `Bamb0oChen` 数字 ID。后端不信任前端传入的用户名，也不以可修改的 login 字符串授予权限。
5. 在此目录运行 `docker compose up -d --build`。
6. 将根目录 `mkdocs.yml` 中 `extra.thoughts_api` 设置为 `https://你的API域名`，重新构建并部署笔记站。
7. 真实验收：你的 GitHub 登录能发帖；另一个 GitHub 账号不能发布；无痕窗口看不到草稿；重启服务后已发布内容仍在。

未配置 API 时，页面显示明确的「服务尚未连接」，不会展示假帖子或模拟登录。真实 GitHub OAuth 验收需以上配置完成。

## 安全与运行

- GitHub Authorization Code + S256 PKCE + 一次性 state（10 分钟）。后端读取 `/user` 验证数字账号 ID。
- OAuth 完成后使用 60 秒一次性交接码返回原页面，必须携带原浏览器 sessionStorage 中的校验串才能兑换。回调目标固定，不能传任意 return URL。
- GitHub access token 仅在服务端请求身份时使用，不传入前端、不存数据库。站点随机会话有效 12 小时，数据库只存 SHA-256；退出会撤销。
- 站点会话存于当前标签页 sessionStorage，避免第三方 Cookie 限制；正文用 textContent 渲染。仍需保持笔记域名及所有脚本可信，以防同源 XSS 窃取会话。
- CORS 仅允许配置的前端 origin；CORS 不是鉴权，所有写接口另行检查会话。
- 反向代理设置 `client_max_body_size 128k`，`/auth/start` 建议每 IP 每分钟 10 次；不要在日志记录 OAuth 回调 query（含 code）。容器默认禁用访问日志。
- 编辑框会暂存到此浏览器 localStorage（未加密）。共享电脑不要写敏感内容；退出不会清理暂存。服务端草稿只有作者可读。
- 已发布帖子编辑保存为草稿即撤下；删除需要确认，无法从 UI 恢复。版本检查阻止旧页面覆盖更新；列表使用游标分页。
- SQLite 持久化于 `thoughts-data` volume。不要运行 `docker compose down -v`。定期用 SQLite backup API 创建备份（WAL 模式不要只复制一个正在写入的 db 文件），备份也包含私有草稿，请限制权限。

## 本地测试

```powershell
uv run --with fastapi --with httpx --with pytest python -m pytest services/thoughts/test_app.py -q
```

浏览器回归：在 `localhost:8769` 运行 MkDocs 构建后的静态站，安装 Playwright，执行 `node services/thoughts/test_browser.cjs`；也可用 `PLAYWRIGHT_MODULE` 指定已有 Playwright 模块路径。脚本通过浏览器请求拦截注入临时数据，测试编辑/发布/删除/暂存恢复/移动端和主题，不写实际数据库、不代替真实 OAuth 验收。

本地启动（在本目录；无 OAuth 配置时公开读取可用，登录返回 503）：

```powershell
uv run --with fastapi --with httpx --with uvicorn python -m uvicorn app:app --host 127.0.0.1 --port 8770 --no-access-log
```

生产不要使用本地默认 URL。多副本部署需先换共享数据库，当前按单实例设计。

OAuth 流程依据 [GitHub 官方文档](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)。
