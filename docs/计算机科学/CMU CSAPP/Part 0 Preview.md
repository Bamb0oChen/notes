# Part 0 Preview

> 课程地图：CMU 15-213 Introduction to Computer Systems（CSAPP）。
> 版本：**2015 Fall，教材 CS:APP 第 3 版**。现有笔记未注明学期，本文先以此版本为准；其他学期或视频合集的编号可能不同。
> 核对日期：2026-09-08。下文 Lecture 编号按官网正式授课顺序编排，不计 Recitation、考试和假期；笔记文件的 Part 编号不等于 Lecture 编号。

## 1. 先看整体路线

数据表示 → 汇编与机器级程序 → 优化与缓存 → 链接、进程与信号 → 虚拟内存与分配器 → 网络与并发。

**实验顺序：Data → Bomb → Attack → Cache → Shell → Malloc → Proxy。**

Lecture 是主课；Recitation 是习题课/实验辅导。实验通常跨多节课，不是一节 Lecture 对应一个 Lab。

## 2. Lecture 与教材、Lab 对照

下表的实验关联是按知识依赖整理的学习指引；官方发布与截止时间见下一节。章节号均指 CS:APP 第 3 版。

| Lecture | 主题（中文 / 官网标题） | 阅读章节 | 关联 Lab / 学习用途 |
| --- | --- | --- | --- |
| 01 | 课程概览 / Overview | 1 | 建立系统全貌 |
| 02 | 位、字节与整数（一）/ Bits, Bytes, and Ints: Part 1 | 2.1 | Data：位运算与数据表示 |
| 03 | 位、字节与整数（二）/ Bits, Bytes, and Ints: Part 2 | 2.2–2.3 | Data：整数表示、转换和运算 |
| 04 | 浮点数 / Floating Point | 2.4 | Data：浮点部分 |
| 05 | 机器级编程：基础 / Machine Prog: Basics | 3.1–3.5 | Bomb：读懂指令与寄存器 |
| 06 | 机器级编程：控制流 / Machine Prog: Control | 3.6 | Bomb：条件、分支与循环 |
| 07 | 机器级编程：过程 / Machine Prog: Procedures | 3.7 | Bomb、Attack：函数调用与栈 |
| 08 | 机器级编程：数据 / Machine Prog: Data | 3.8–3.9 | Bomb：数组、结构体与地址计算 |
| 09 | 机器级编程：进阶 / Machine Prog: Advanced | 3.10 | Attack：越界访问与栈相关知识 |
| 10 | 程序优化 / Code Optimization | 5 | Cache 的优化思维基础 |
| 11 | 存储层次 / The Memory Hierarchy | 6.1–6.3 | Cache：局部性与存储层次 |
| 12 | 高速缓存 / Cache Memories | 6.4–6.7 | Cache：缓存映射与命中/缺失 |
| 13 | 链接 / Linking | 7 | 理解目标文件、符号与程序构建 |
| 14 | 异常控制流：异常与进程 / ECF: Exceptions & Processes | 8.1–8.4 | Shell：进程创建、执行与回收 |
| 15 | 异常控制流：信号 / ECF: Signals | 8.5–8.8 | Shell：信号与进程控制 |
| 16 | 系统级 I/O / System Level I/O | 10 | Shell、Proxy：文件描述符与 I/O |
| 17 | 虚拟内存：概念 / Virtual Memory: Concepts | 9.1–9.6 | Malloc 的内存模型基础 |
| 18 | 虚拟内存：系统 / Virtual Memory: Systems | 9.7–9.8 | Malloc：地址空间与内存映射 |
| 19 | 动态内存分配：基础 / Storage Allocation: Basic | 9.9 | Malloc：分配器基本组织 |
| 20 | 动态内存分配：进阶 / Storage Allocation: Advanced | 9.9–9.11 | Malloc：分配策略与内存管理 |
| 21 | 网络编程（一）/ Network Programming: Part 1 | 11.1–11.4 | Proxy：网络与套接字基础 |
| 22 | 网络编程（二）/ Network Programming: Part 2 | 11.5–11.6 | Proxy：客户端/服务器与 HTTP |
| 23 | 并发编程 / Concurrent Programming | 12.1–12.3 | Proxy：并发服务模型 |
| 24 | 同步：基础 / Synchronization: Basic | 12.4、12.5.1–3 | Proxy：共享数据与同步 |
| 25 | 同步：进阶 / Synchronization: Advanced | 12.5.4–5、12.7 | Proxy：进一步理解并发正确性 |
| 26 | 线程级并行 / Thread-Level Parallelism | 12.6 | 并行性能与扩展知识 |
| 27 | 计算的未来 / The Future of Computing | 官网未列阅读章节 | 课程收尾与拓展 |

来源：[CMU 2015 Fall 官方课表](https://www.cs.cmu.edu/afs/cs/academic/class/15213-f15/www/schedule.html)。课表提供各节课的 PDF、PPTX、示例代码及录像入口。官网特意将第 10 章 I/O 提前，以满足实验依赖，因此不要机械地按教材章节顺序看课。

## 3. 什么时候开始做哪个 Lab？

“官方发布”是当年教学安排；“自学建议”是本文按知识依赖整理的建议，不是额外的官方要求。日期均为 **2015 年**。

| Lab | 官方发布 → 截止 | 官方发布对应课程 | 自学建议的开做节点 | 对应实验辅导 |
| --- | --- | --- | --- | --- |
| L1 Data Lab | 09-03 → 09-17 | Lecture 02 | 学完 02–03 开始整数部分；04 后做浮点部分 | Recitation 3：数据表示、Data Lab；另有 Linux Boot Camp |
| L2 Bomb Lab | 09-17 → 09-29 | Lecture 06 | 05–06 后开始，结合 07–08 继续推进 | Recitation 4：Bomb Lab |
| L3 Attack Lab | 09-29 → 10-08 | Lecture 09 | 学完 05–09，重点确认调用栈与返回地址 | Recitation 5：Attack Lab 与栈 |
| L4 Cache Lab | 10-08 → 10-15 | Lecture 12 | 学完 11–12 后开始；优化时回看 10 | Recitation 7：Cache Lab 与分块 |
| L5 Shell Lab（tshlab） | 10-22 → 11-03 | Lecture 16 | 学完 14–16 后开始 | Recitation 9：Shell、进程、信号与 I/O |
| L6 Malloc Lab | 11-03 → 11-19 | Lecture 19 | 19 后做基础实现，20 后再完善策略 | Recitation 11：Malloc；12：Malloc 调试 |
| L7 Proxy Lab | 11-19 → 12-08 | Lecture 24 | 先掌握 16、21–22 做基本代理，再结合 23–25 完善并发与同步 | Recitation 13：Proxy；14：同步 |

官方依据：[实验安排与截止日期](https://www.cs.cmu.edu/afs/cs/academic/class/15213-f15/www/assignments.html)、[Lecture / Recitation 课表](https://www.cs.cmu.edu/afs/cs/academic/class/15213-f15/www/schedule.html)。当年的截止时间是日期当天 23:59，仅用于理解课程节奏，不作为现在的自学期限。

## 4. 自学时的检查点

- **Data 前后**：能解释补码、符号扩展、移位、溢出与浮点编码。
- **Bomb / Attack 前后**：能用反汇编和调试器追踪控制流、参数、栈帧与内存地址。
- **Cache 前后**：能拆分地址中的标记、组索引、块内偏移，并解释局部性对性能的影响。
- **Shell 前后**：能解释进程创建/回收、信号处理及其竞争条件。
- **Malloc 前后**：能说明块布局、空闲块组织、分割与合并，并检查堆的一致性。
- **Proxy 前后**：能说明请求转发、I/O、并发访问和共享缓存同步之间的关系。

这些检查点是自学建议；具体任务、限制和评分应以所使用实验包的 writeup 为准。

## 5. 版本与资源提醒

- 本学期正式安排是上面的 **7 个 Lab**；课表没有安排 Architecture Lab，也没有单独的第 4 章处理器体系结构 Lecture。不要把其他版本的实验清单直接混进这份课程进度。
- 某些视频合集可能省略最后的拓展课或重新拆分视频。对照时优先认课程标题，不要只认集数。
- 官网历史课程使用 Autolab 发放和提交实验。本文核对的是课程安排，并未确认所有历史实验包、录像及校内提交入口现在都能访问。

### 官方入口

- [课程首页：CMU 15-213 Fall 2015](https://www.cs.cmu.edu/afs/cs/academic/class/15213-f15/www/index.html)
- [完整课表、讲义、代码与录像入口](https://www.cs.cmu.edu/afs/cs/academic/class/15213-f15/www/schedule.html)
- [实验清单与当年时间安排](https://www.cs.cmu.edu/afs/cs/academic/class/15213-f15/www/assignments.html)