# LECTURE 6：打包与交付代码（Packaging and Shipping Code）

来源：The Missing Semester 2026 新增课程「Shipping Code」
- https://missing-semester-cn.github.io/2026/shipping-code/

这讲试图解决一个高频痛点：**为什么代码在我的电脑上能跑，但在别人的电脑上不行？**

核心抽象是两件事：
- 你要交付的“东西”到底是什么（artifact，产物）？
- 它对运行环境做了哪些假设（Python 版本、系统库、CPU/GPU、配置、外部服务等）？

---

## 0. 一句话框架

把“能运行的源代码”变成“可分发、可复现、可部署的产物”，并明确：
- 依赖与环境（Dependencies & Environments）
- 产物与打包（Artifacts & Packaging）
- 发布与版本（Releases & Versioning）
- 可复现（Reproducibility）
- 虚拟机与容器（VMs & Containers）
- 配置（Configuration）
- 服务与编排（Services & Orchestration）
- 发布渠道（Publishing）

---

## 1. 依赖与环境：从“装包”到“隔离冲突”

### 1.1 依赖是什么

以 Python 为例，`import requests` 之所以会失败，通常不是代码问题，而是：
- 依赖未安装
- 安装到了另一个 Python/环境里

包管理器要做的不只是“下载一个包”，还包括：
- 解析并安装传递依赖（dependencies of dependencies）
- 选择与你平台匹配的产物（比如 `.whl`）

### 1.2 依赖冲突（dependency hell）与 venv

当多个包对同一依赖要求不兼容时，就会出现冲突。解决思路通常是：
- **每个项目一个环境**（把依赖隔离起来）

创建并启用虚拟环境（示例）：

```bash
python -m venv .venv
source .venv/bin/activate
which python
which pip
```

Windows PowerShell 通常是：

```powershell
python -m venv .venv
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .\.venv\Scripts\Activate.ps1)
```

### 1.3 `uv`：更快的 pip / venv / 多版本 Python

课程强推 `uv`（Astral 出品，Rust 写的），核心价值：
- `uv pip ...` 的接口与 `pip` 接近，但**速度快很多**
- 能用 `uv venv --python 3.12 ...` 直接创建指定 Python 版本的环境

示例：

```bash
uv pip install requests
uv venv --python 3.12 venv312
```

> 实用建议：做通用脚本/后端/服务端，优先 `uv`；需要复杂系统级依赖（CUDA、非 Python 库）时，`conda` 仍然常见。

---

## 2. 产物（artifact）与打包：从“目录里能跑”到“装哪都能跑”

### 2.1 Source vs Artifact

- **源代码**：开发者阅读/修改的内容
- **产物（artifact）**：给别人安装/部署的东西

在 Python 里，常见产物是：
- Wheel：`.whl`（更像“可安装的二进制包”，即使里面多数是纯 Python 文件）
- Source distribution：`.tar.gz`（源码包，可能需要本地构建）

### 2.2 `pyproject.toml`（推荐） vs `requirements.txt`

`requirements.txt` 适合“列依赖”，但它不是完整的项目清单：
- 不包含项目元信息（名称、版本、描述、入口脚本等）

`pyproject.toml` 是现代标准（PEP 517/621），能同时表达：
- 项目元数据
- 依赖
- 构建系统
- 命令行入口（安装后直接运行一个命令）

最小示例（节选）：

```toml
[project]
name = "greeting"
version = "0.1.0"
dependencies = ["typer>=0.9"]

[project.scripts]
greet = "greeting:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

补充理解：可以把它看作 **“描述性文档（config）”** 与 **“执行指令（script）”** 的分工。
- `pyproject.toml` 负责描述“项目是什么/依赖什么/如何构建/暴露哪些入口”
- 安装器（`pip`/`uv`）负责执行“解析依赖、下载、构建、安装”的流程

#### 2.2.1 TOML 文件是怎么架构的？

TOML（Tom's Obvious, Minimal Language）的设计目标是：**人类可读**，并且能很自然地映射到“字典/哈希表”。

在 `pyproject.toml` 里你会经常看到三种结构：
- **表（tables）**：用 `[project]` 这种 `[ ]` 表示（可以理解成大字典的一个 key）
- **键值对**：`key = "value"`，值可以是字符串/数字/布尔/数组等
- **层级表（nested tables）**：用点号表达层级，比如 `[tool.uv]`

一个典型骨架（再次用“像字典一样读取”来理解）：

```toml
[project]
name = "my-app"
version = "0.1.0"
dependencies = [
	"requests>=2.0",
	"flask",
]

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
```

#### 2.2.2 为什么 `requirements.txt` 能“直接安装”？

`requirements.txt` 本身并不“会安装”，它只是一个**安装清单**；真正执行安装的是 `pip`/`uv`，而它们内部已经内置了完整的协议与默认行为：

1. 解析：逐行读取 `requests==2.28.1` 这种“包名 + 版本约束”
2. 寻址：默认去 PyPI 索引查找对应版本的可用产物
3. 依赖解析：递归解析整棵依赖树，寻找一组不冲突的版本组合
4. 安装：优先下载 wheel（`.whl`）直接安装；没有 wheel 才可能走源码构建（`.tar.gz`）

#### 2.2.3 深度对比：`pyproject.toml` vs `requirements.txt`

| 维度 | `requirements.txt` | `pyproject.toml` |
| :--- | :--- | :--- |
| 本质 | 安装清单：告诉安装器“装什么” | 项目定义：项目元数据 + 依赖 + 构建系统 + 工具配置 |
| 结构 | 逐行列表（弱结构） | 结构化配置（强结构） |
| 标准性 | 约定俗成 | PEP 517/621 标准 |
| 常见场景 | 部署/环境复刻（尤其是应用） | 正式项目/库/应用的一体化配置中心 |

实用落地：
- 小脚本：`requirements.txt` 足够（但仍建议配合 venv）
- 正式项目：优先 `pyproject.toml`；再用 `uv lock` 生成 `uv.lock` 来获得可复现性

### 2.3 构建 wheel：`uv build`

```bash
uv build
ls dist/
```

把 `dist/*.whl` 交给别人后，对方只需：

```bash
uv pip install ./dist/greeting-0.1.0-py3-none-any.whl
greet Alice
```

### 2.4 平台差异：为什么有的 wheel 不能跨机器

文件名里的 tag 表示兼容范围：
- `py3-none-any`：几乎所有平台都能用（纯 Python 或已做成通用轮子）
- `cp312-...-win_amd64` / `manylinux_...` / `macosx_..._arm64`：与 Python 版本和 OS/架构强相关

当依赖涉及 CUDA / OpenSSL / 编译器等系统库时，“仅交付 wheel”不一定够。

---

## 3. 版本与发布：让升级可预期

### 3.1 语义化版本（SemVer）

`MAJOR.MINOR.PATCH` 的直觉：
- PATCH：只修 bug，保持兼容
- MINOR：新增功能，保持兼容
- MAJOR：破坏兼容，需要用户改代码

### 3.2 依赖版本约束写法（Python）

```toml
dependencies = [
	"requests==2.32.3",  # 精确版本（更可复现）
	"click>=8.0",        # 下限
	"numpy>=1.24,<2.0",  # 范围
	"pandas~=2.1.0",     # compatible release：>=2.1.0,<2.2.0
]
```

---

## 4. 可复现：锁文件、环境差异与回滚

### 4.1 为什么要 lockfile

如果只写 `requests>=2.0`，不同时间安装可能得到不同依赖组合。

`uv lock` 会生成 `uv.lock`，把解析结果（含哈希）固定下来。

```bash
uv lock
```

在 CI/生产环境里常见做法是“冻结安装”：

```bash
uv sync --frozen
```

### 4.2 Library vs App：锁定策略不同

- **库（library）**：更偏向写“兼容范围”，否则容易和下游项目冲突
- **应用/服务（app/service）**：更偏向锁死版本以确保可复现

### 4.3 升级会坏怎么办

即使有 CI，也可能遇到 dev/prod 不一致导致的线上问题。建议：
- 依赖升级要可追踪（版本、变更日志）
- 准备回滚（回到已知可用版本）

---

## 5. VM 与容器：当包管理器不够用

### 5.1 VM vs Container

- VM：带完整 OS，隔离更强，启动更重
- 容器：共享宿主机内核，更轻更快，但隔离弱于 VM

### 5.2 Docker 基本概念

- image：产物（artifact）
- container：运行中的实例

Dockerfile 每条指令会形成 layer；合理利用缓存能显著加速构建。

### 5.3 常见 Dockerfile 坑

- 使用过大的基础镜像（不必要的体积）
- `RUN` 分太碎导致 layer 太多
- 不清理 apt 缓存
- 把 secrets 写进镜像 layer（严重安全问题）

### 5.4 Builder pattern：直接复制 `uv` 二进制

课程给了一个很实用的思路：不在镜像里“从源码装 uv”，而是从官方镜像里把 uv 二进制拷出来。

---

## 6. 配置：代码与配置分离，秘密别进 Git

推荐模式：运行时注入配置，而不是写死在代码里。

### 6.1 环境变量

```python
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///local.db")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
API_KEY = os.environ["API_KEY"]  # 必填，缺失直接报错
```

### 6.2 配置文件

适合结构化配置（YAML/TOML/JSON），并可按 dev/staging/prod 切换。

---

## 7. 服务与编排：不把 Redis 打进你的应用镜像

很多应用需要数据库/缓存/队列等外部服务。

与其把 Redis 作为“你的应用依赖”去编译和打包，更常见的是：
- 每个服务各自一个容器
- 通过网络通信

Docker Compose 用一个 `docker-compose.yml` 定义多服务：

```yaml
services:
	web:
		build: .
		ports:
			- "8080:8080"
		environment:
			- REDIS_URL=redis://cache:6379
		depends_on:
			- cache

	cache:
		image: redis:7-alpine
		volumes:
			- redis_data:/data

volumes:
	redis_data:
```

要点：
- `cache` 这个服务名可以当作 DNS 主机名使用
- volumes 用于持久化数据

更进一步：
- 小规模生产可用 systemd 托管 `docker compose up -d`
- 更复杂的需求才考虑 Kubernetes（学习成本和运维成本都高）

---

## 8. 发布（Publishing）：把产物放到别人找得到的地方

常见渠道：
- GitHub Releases：挂载预编译二进制/wheel
- PyPI：Python 官方包仓库
- TestPyPI：发布流程演练用
- Docker Hub / GHCR：容器镜像仓库

`uv publish` 支持发布到 TestPyPI（示例）：

```bash
uv publish --publish-url https://test.pypi.org/legacy/
```

---

## 9. 一份可执行的“交付清单”（从个人项目到可交付）

1. 每个项目一个环境（`venv`/`uv venv`）
2. 依赖写进 `pyproject.toml`，并生成 lockfile（`uv lock`）
3. 本地/CI 使用冻结安装（`uv sync --frozen`）
4. 明确 artifact：wheel / docker image / 可执行文件 / 静态站点
5. 配置与 secrets 从代码剥离（环境变量/配置文件；秘密不进 git）
6. 发布前打 tag + 写 changelog（至少记录 breaking changes）
7. 需要系统依赖/跨机器一致性时，上 Docker/容器编排

---

## Exercises（原讲义习题方向）

1. 对比 venv 激活前后的环境变量（`printenv` + `diff`），理解 `$PATH` 如何变化
2. 用 `pyproject.toml` 做一个 Python 包：安装、生成 lockfile、检查内容
3. 安装 Docker，用 compose 在本地构建 Missing Semester 网站
4. 给一个简单 Python 应用写 Dockerfile，并用 compose 跑一个 Redis cache
5. 发布包到 TestPyPI，再构建 Docker 镜像并推送到 `ghcr.io`
6. 用 GitHub Pages 发布一个网站（可选：自定义域名）
