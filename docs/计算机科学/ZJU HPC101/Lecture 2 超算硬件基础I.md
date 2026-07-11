## Abstraction

注意，我们这里所说的其实不是摘要，而是 抽象 这一种编程思想

抽象的本质就是下层的内容不会影响到上层，这点我们可以从晶体管到CPU的变化中发现

## 计算机组成

这一部分我会在CS 15213中更新（当然现在在我们的[服务器搭建](../服务器搭建与运维/1.%20服务器硬件搭建.md)中也有相关的内容）

首先先贴一张总结
![](../../images/sys.png)

### CPU

CPU的很多参数我在之前都已经提到过了（主频睿频），当然我们学这门课肯定是要以更底层的视角去看待我们的计算机系统

首先，让我们来宏观地看一下一个CPU die
![](../../images/Intel_Core_i9-13900K-Die_Shot.jpg)

我们可以看见，这个die中具有核心，以及分布在核心周围的缓存

整个内存大概可以分成四个部分

#### ① P-Core（性能核）

图中最大的蓝色区域，而每一个 P-Core 都包括：

```text
P-Core
│
├── 执行单元
├── 分支预测
├── 解码器
├── OoO（乱序执行）
├── Load Store
└── L2 Cache（注意，L2缓存私有，每个核一个）
```
---

#### ② E-Core（能效核）

右边灰蓝色区域

E-Core一般以集群的方式存在，共享一个L2

这种架构使得我们的核心面积能够更小，实现功耗降低和读取速率增加

---

#### ③ L3 Cache

图中的紫色：

Intel 会把 L3 切成很多 Slice，但是注意，L3缓存是共享的，不同核之间都通过L3来交换数据

---

#### ④ Compute Fabric（紫色长条）

一条总线就像一个高铁，连接P-Core，E-Core，L3，GPU，Memory Controller，PCIe（所以PCIE很快啊）

总体上，我们这样来看待一个cpu die

```text
                CPU Die
──────────────────────────────────────
        DDR PHY（连接内存）
──────────────────────────────────────
 Memory Controller + PCIe + DMI
──────────────────────────────────────
        Compute Fabric（互连）
──────────────────────────────────────
 8×P-Core      16×E-Core      GPU
──────────────────────────────────────
       Media Engine / Display
```
### Memory Hierarchy 存储层级
计算机中的存储其实有很多，这个地方我们首先来看看所有储存的层级架构

![](../../images/memory%20hierachy.png)

其中，寄存器就处在我们的核心里面，然后是核心外的L1 L2 L3 然后再到我们外部的内存磁盘，最后是一些云端存储

在win和linux上，我们分别可以用这两种方法来实现我们的Lx大小查找

![](../../images/cacheinwin.png)

![](../../images/cacheinlin.png)

### OS (Operating System)

我们现在有很多的操作系统

win(get) linux(get) debian macOS(get) iOS(get) Ubuntu(get) HarmonyOS Android

这些操作系统在主机的运行中主要起到一个资源分配的作用

例如下面这段代码
![](../../images/OS1.png)

当一个事件输入的时候，我们通过检测事件的类别来为事件分配不同的处理方式，这就是内核（kernel）的最基础思想

#### Trap

Trap简单来说就是CPU停下当前程序，转去处理操作系统的代码

Trap可以分为两种 中断（Interrupt） 和 异常（Expection）

|           | Interrupt | Exception |
| --------- | --------- | --------- |
| 来源        | CPU 外部    | CPU 内部    |
| 是否和当前指令有关 | 无关        | 有关        |
| 是否可以预测    | 不可以       | 可以        |
| 什么时候发生    | 随时        | 执行某条指令时   |

Interrupt是因为外界输入的信息阻断了现在CPU的进程

Interrupts: external asynchronous events（外部的异步事件）

比如你在玩游戏，但是你鼠标动了，这个时候CPU就要停下某条处理游戏的线程去除磷你鼠标的移动反馈

而Exceptions是啥呢 unusual condition occurring at instruction run time

就是说cpu自己检测到了这条指令不对导致的中断（比如除法器中除数为0）

接下来让我们看看下面这张图

![](../../images/kernel.png)

这张图就是我刚刚说的，程序在执行的过程中会因为exception而中断去处理别的事

但是从cpu的角度看，我怎么知道谁是kernel谁是user（现在cpu要处理谁）

所以我们在cpu中引入了一个mode用来存放某状态的快照，通过这个快照的绑定和织影来区分cpu不同的工作态

你可能会问，为什么要区分，cpu本质不就是在处理机器码吗？这还能有不同？

当然，你不希望一个user权限的程序能给你系统删了，这也是所谓普通程序不能控制硬件的原因

而trap就是让用户程序合法进入内核的过程

![](../../images/mode.png)

上面这张图就很明显了

###