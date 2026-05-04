首先我们先学习一下调试中必备的语法表达式——正则表达式

- `.`：除换行符之外的“任意单个字符”
- `*`：匹配前面字符零次或多次
- `+`：匹配前面字符一次或多次
- `[abc]`：匹配 a、b 和 c 中的任意一个
- `(RX1|RX2)`：任何能够匹配 RX1 或 RX2 的结果
- `^`：行首
- `$`：行尾

正则表达式的使用能够延长语义，帮助我们找到自己想要的信息

例如`\.*Disconnected from\`可用于查找所有的断联消息

这段 `sed` 命令的目的是：**从日志行中删除（清空）匹配特定模式的 SSH 登录失败记录**，而保留所有不匹配该模式的行。

当然，如果我们想要更精准的匹配，我们可以增长正则表达式

```bash
| sed -E 's/.*Disconnected from (invalid |authenticating )?user .* [^ ]+ port [0-9]+( \[preauth\])?$//'
```

```bash
sed -E 's/.../ //'
```

- `-E`：使用扩展正则表达式（避免写大量反斜杠）。
- `s/...//`：将匹配到的内容**替换为空字符串**，即删除整行。

| 部分 | 含义 |
|------|------|
| `.*` | 跳过行开头的任意内容（比如时间戳、主机名） |
| `Disconnected from ` | 固定文本 |
| `(invalid \|authenticating )?` | 可选地出现 `invalid ` 或 `authenticating `（SSH 日志中的两种断开前缀） |
| `user .*` | 匹配 `user` + 任意用户名 |
| `[^ ]+` | 一个不含空格的字段（通常是客户端 IP 地址） |
| `port [0-9]+` | 固定 `port` + 数字端口号 |
| `( \[preauth\])?` | 可选地出现 ` [preauth]`（表示认证前断开） |
| `$` | 行尾 |

**会被删除的行（整行变空）：**
```
sshd[12345]: Disconnected from invalid user admin 192.168.1.100 port 54321 [preauth]
sshd[12346]: Disconnected from authenticating user root 10.0.0.1 port 22
```

**不会被删除的行：**
```
sshd[12347]: Accepted password for root from 192.168.1.101 port 22
Disconnected from user something（格式不匹配）
```

以下是从 **perf 数据解读** 开始的完整总结文档，已整理为可直接查阅的 Markdown 格式：

## Perf 性能分析完整指南

## 目录
1. [Perf 数据解读](#perf-数据解读)
2. [火焰图生成](#火焰图生成)
3. [火焰图查看方法](#火焰图查看方法)
4. [测试程序编写](#测试程序编写)
5. [常见问题速查](#常见问题速查)

---

## Perf 数据解读

### 示例输出

```bash
Performance counter stats for 'ls':

              9.23 msec task-clock                #    0.554 CPUs utilized
                 2      context-switches          #  216.731 /sec
                 0      cpu-migrations            #    0.000 /sec
               103      page-faults               #   11.162 K/sec
           7372572      cycles                    #    0.799 GHz
           5197634      stalled-cycles-frontend   #   70.50% frontend cycles idle
           2974103      instructions              #    0.40  insn per cycle
                                                  #    1.75  stalled cycles per insn
            683454      branches                  #   74.063 M/sec
            103287      branch-misses             #   15.11% of all branches

       0.016666486 seconds time elapsed
```

### 核心指标详解

#### 1. 时间相关指标

| 指标 | 含义 | 解读 |
|------|------|------|
| **task-clock** | 任务实际占用的 CPU 时间 | 9.23ms 表示 CPU 真正花在执行上的时间 |
| **CPUs utilized** | CPU 利用率 | 0.554 = task-clock(9.23ms) / 总耗时(16.67ms)，<1 表示有等待 |
| **time elapsed** | 墙钟时间（总耗时） | 程序从开始到结束的真实时间 |

#### 2. 系统调度指标

| 指标 | 含义 | 正常范围 |
|------|------|----------|
| **context-switches** | 上下文切换次数 | 轻量级命令应很少 |
| **cpu-migrations** | CPU 迁移次数 | 理想为 0 |
| **page-faults** | 缺页异常次数 | minor faults 正常，major faults 应避免 |

**缺页异常说明：**
- **Minor faults**：页已在内存，只是未建立映射（正常）
- **Major faults**：需要从磁盘读取页（性能杀手）

#### 3. CPU 执行指标

| 指标 | 含义 | 计算公式 |
|------|------|----------|
| **cycles** | CPU 时钟周期数 | 737万次 "心跳" |
| **instructions** | 执行的指令数 | 297万条指令 |
| **IPC** | 每周期指令数 | instructions / cycles = 0.40 |

**IPC 评估标准：**
- **IPC > 1.0**：良好，CPU 效率高
- **IPC 0.5-1.0**：一般，有优化空间
- **IPC < 0.5**：较差，大量等待（内存/IO 密集）

#### 4. 流水线停顿指标

| 指标 | 含义 | 解读 |
|------|------|------|
| **stalled-cycles-frontend** | 前端停顿周期 | 70.50% 表示 CPU 大量时间在等待取指 |
| **stalled cycles per insn** | 每指令停顿周期 | 1.75 = 每执行 1 条指令要等 1.75 个周期 |

**停顿原因：**
- 缓存未命中
- 内存访问延迟
- 分支预测错误

#### 5. 分支预测指标

| 指标 | 含义 | 评估 |
|------|------|------|
| **branches** | 分支指令总数 | 68万次 if/else、循环 |
| **branch-misses** | 分支预测失败次数 | 15.11% 偏高（理想 <5%） |

**分支预测失败的影响：**
- 导致流水线清空
- 浪费多个时钟周期
- 常见于不规则的数据模式

### 性能评估总结

基于示例数据：

| 指标 | 值 | 评价 | 原因分析 |
|------|-----|------|----------|
| CPU 利用率 | 55.4% | ⚠️ 一般 | 有等待时间 |
| IPC | 0.40 | 🔴 偏低 | 内存密集型 |
| 分支预测失败 | 15.11% | 🔴 偏高 | 数据模式不规则 |
| 前端停顿 | 70.5% | 🔴 很高 | 等待内存/IO |

**结论**：`ls` 是 **I/O 和内存密集型** 命令，瓶颈在内存访问和文件系统，而非 CPU 计算能力。

---

- 火焰图生成

### 安装 FlameGraph 脚本

```bash
git clone https://github.com/brendangregg/FlameGraph.git
```

### 基本命令流程

```bash
# 步骤1：录制性能数据
sudo perf record -g -F 99 ./my_program

# 步骤2：生成火焰图
sudo perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > flamegraph.svg

# 步骤3：查看结果
explorer.exe .   # 在 Windows 中打开文件夹
```

### perf record 常用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-g` | 记录调用栈 | `perf record -g ./prog` |
| `-F 99` | 采样频率 99Hz | `perf record -F 99 ./prog` |
| `--call-graph dwarf` | DWARF 调用栈（更准） | `perf record --call-graph dwarf ./prog` |
| `-p PID` | 录制指定进程 | `perf record -p 1234 -g` |
| `-a` | 录制整个系统 | `perf record -a -g sleep 10` |
| `--sleep N` | 录制 N 秒 | `perf record -p 1234 --sleep 30` |

### 常见错误及解决

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `failed to open perf.data` | 未录制数据 | 先执行 `perf record` |
| `Stack count is low (0)` | 采样点太少 | 增加 `-F` 或循环运行程序 |
| `Invalid field requested` | 参数语法错误 | 简化命令：`perf script \| ...` |

---

- 火焰图查看方法

### 火焰图结构

```
Y轴（深度）
    ↑
    │  ┌────┐  ┌──┐     ← 顶层：当前运行的函数
    │  │ E │  │ F│
    │ ┌┴────┴┐ │  │
    │ │  C   │ │D │     ← 中层：调用者
    │ └┬─────┘└──┘
    │  │  A   │  B       ← 底层：调用链起点
    │  └──────┴───┘
    └──────────────────→ X轴（宽度）
                              main
```

### 坐标轴含义

| 轴 | 含义 | 重要性 |
|----|------|--------|
| **X轴（横向）** | 采样数量 / CPU 时间占比 | ⭐⭐⭐ 最重要！宽度越宽 = 占用越多 |
| **Y轴（纵向）** | 调用栈深度 | ⭐⭐ 越高说明调用层级越深 |

### 颜色含义

- **颜色仅用于区分不同函数**，不表示热度
- **宽度才是热度的真正指标**
- 在 `perf report` 中：红色=热点，绿色=冷门

### 交互式操作（浏览器中打开 SVG）

| 操作 | 效果 |
|------|------|
| 鼠标悬停 | 显示函数名、采样数、占比百分比 |
| 点击方块 | 放大该函数，聚焦其调用链 |
| 右键 → Zoom Out | 恢复原始视图 |
| Ctrl+F | 搜索特定函数（会高亮显示） |

### 火焰图形状诊断

| 形状 | 特征 | 问题诊断 | 优化方向 |
|------|------|----------|----------|
| 🔴 **平顶山** | 单个函数占 >30% 宽度 | 该函数是性能瓶颈 | 重点优化此函数 |
| 🟡 **宝塔形** | 调用层级 >50 层 | 递归过深或循环嵌套 | 减少递归深度，改用迭代 |
| 🟢 **草原形** | 大量细条且高度一致 | 函数粒度过细，调用频繁 | 考虑函数内联 |
| ⚪ **悬崖形** | 调用链突然中断 | 递归溢出或栈损坏 | 检查递归边界条件 |

### Children vs Self 指标（perf report）

```
Samples: 225 of event 'cycles'
 
Children   Self    Command    Symbol
  5.89%    0.00%   factor     [k] do_mmap        ← 调用者
  5.74%    5.46%   find       [k] kmem_cache_alloc ← 真正的热点
```

| 指标 | 含义 | 如何判断 |
|------|------|----------|
| **Children** | 自身 + 所有子函数时间 | 高值说明该函数及其调用链耗时多 |
| **Self** | 仅函数自身指令时间 | **高值 = 真正的热点函数** |

**关键结论：**
- Self 高 + Children 也高 = 函数本身就是热点（需优化）
- Children 高但 Self 为 0 = 函数是调度者（实际工作在子函数）

### 实际案例解读

基于用户数据的分析结果：

| 热点函数 | Self | 含义 | 建议 |
|----------|------|------|------|
| `kmem_cache_alloc` | 5.46% | 内存分配频繁 | 复用内存对象 |
| `legitimize_path` | 5.33% | 路径验证开销 | 缓存路径结果 |
| `srso_alias_safe_ret` | 5.34% | WSL2 虚拟化开销 | 减少系统调用 |
| `exc_page_fault` | 4.81% | 缺页异常频繁 | 扩大内存映射 |

### 查看火焰图的三个步骤

1. **找最宽的横条** → 定位 CPU 热点
2. **向上看调用链** → 找到调用的源头
3. **悬停查看详情** → 确认函数名和占比

### Bash 测试脚本（轻量级）

```bash
#!/bin/bash

# 递归函数
fib() {
    if [ $1 -le 1 ]; then echo $1
    else echo $(( $(fib $(($1-1))) + $(fib $(($1-2))) ))
    fi
}

# 主循环
for i in {1..50}; do
    echo "Iteration $i"
    find /usr -name "*.so" 2>/dev/null | head -5
    factor 1234567890 2>/dev/null
    fib 15 > /dev/null
done

echo "Test completed!"
```

---

- 常见问题速查

### 安装问题

| 问题 | 解决方案 |
|------|----------|
| `perf: command not found` | `sudo apt install linux-tools-generic` |
| `WARNING: perf not found for kernel` | 复制通用版 perf 到 `/usr/local/bin/` |
| `dpkg: error processing archive` | `sudo dpkg -i --force-overwrite` |

### 运行问题

| 问题 | 解决方案 |
|------|----------|
| `failed to open perf.data` | 先执行 `sudo perf record` |
| `Stack count is low (0)` | 加 `-F 999` 或用循环多次运行 |
| `Invalid field requested` | 去掉复杂 `-F` 参数，用最简单命令 |
| `flamegraph.pl: command not found` | `git clone` FlameGraph 仓库 |

### 查看问题

| 问题 | 解决方案 |
|------|----------|
| 如何在 WSL 打开 SVG | `explorer.exe .` 然后双击 |
| 找不到火焰图脚本 | 确保在正确目录执行 `./FlameGraph/` |

---

- 快速参考命令

```bash
# 完整的一键测试流程（Bash 脚本）
cat > test.sh << 'EOF'
#!/bin/bash
fib() { if [ $1 -le 1 ]; then echo $1; else echo $(( $(fib $(($1-1))) + $(fib $(($1-2))) )); fi; }
for i in {1..10}; do find /usr -name "*.so" 2>/dev/null | head -3; factor 1234567890 2>/dev/null; fib 10 >/dev/null; done
EOF
chmod +x test.sh

# 录制
sudo perf record -g -F 99 ./test.sh

# 生成火焰图
sudo perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > flame.svg

# 查看报告
sudo perf report -g graph --stdio | head -50

# 打开文件夹
explorer.exe .
```

*适用环境：WSL2 / Ubuntu / Linux perf*
