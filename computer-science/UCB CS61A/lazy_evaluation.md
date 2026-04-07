## 惰性求值核心：及早 vs 延迟 (Eager vs. Lazy)

在 CS61A 中，理解计算发生的“时机”至关重要。

### 1. 核心定义对照

| 概念 | 英文名称 | 行为描述 | Python 例子 |
| :--- | :--- | :--- | :--- |
| **及早求值** | Eager Evaluation | 表达式作为参数传递或赋值时，**立即**计算出结果。 | `abs(-5)`, `x = 1 + 2` |
| **惰性求值** | Lazy Evaluation | 表达式被定义时不计算，直到其结果**被真正需要**时才计算。 | `yield`, `lambda`, `Stream` |

### 2. 短路逻辑 (Short-Circuiting)
Python 的逻辑运算符是内置的惰性机制。如果左边的值已经能确定最终结果，右边的代码永远不会运行。

* **`A and B`**: 若 `A` 为 `False`，`B` 不被执行。
* **`A or B`**: 若 `A` 为 `True`，`B` 不被执行。

```python
def crash():
    return 1 / 0  # 运行必报错

# 示例：
False and crash()  # 结果为 False，不会报错（因为 crash 没被调用）
True or crash()   # 结果为 True，不会报错
```
# Generators_and_Iterators.md

## 生成器与迭代器：Python 的惰性工具

生成器（Generators）是 Python 实现惰性调用的最常用手段，它允许你处理“无限”的数据流而不会撑爆内存。

### 1. 生成器对象 (Generator Objects)
当一个函数包含 `yield` 时，调用该函数**不会**执行函数体，而是返回一个生成器对象。

| 操作 | 效果 | 说明 |
| :--- | :--- | :--- |
| `g = my_gen()` | **创建** | 此时函数体一行代码都没走。 |
| `next(g)` | **推进** | 函数执行到下一个 `yield` 处并“暂停”，返回 yield 后面的值。 |
| `for x in g` | **消耗** | 循环会自动不断调用 `next(g)` 直到函数结束。 |

### 2. 惰性内置函数
在 Python 3 中，许多处理集合的函数都是惰性的（返回迭代器）。

| 函数 | 行为 | 强制求值方法 |
| :--- | :--- | :--- |
| `range(n)` | 不产生列表，只在循环时产生数 | `list(range(n))` |
| `map(f, s)` | 只有访问元素时才对元素应用 `f` | `list(map(...))` |
| `filter(f, s)` | 只有访问元素时才进行布尔判定 | `tuple(filter(...))` |
| `zip(a, b)` | 只有访问时才将元素配对 | `for x, y in zip(a, b):` |
# CS61A_Streams.md

## 流 (Streams)：延迟调用的递归实现

`Stream` 是 CS61A 特有的抽象数据类型，本质上是一个“只有第一个元素被计算出来的链表”。

### 1. Stream 的结构
一个 Stream 实例通常有两个属性：
* **`first`**: 已经计算出的当前值。
* **`rest`**: 一个**延迟求值**的表达式（通常封装在 `lambda` 或函数中）。



### 2. Stream vs. Link 对比表

| 特性 | Link (普通链表) | Stream (流) |
| :--- | :--- | :--- |
| **计算时机** | 递归创建时全部算出 | 只有访问 `.rest` 时才计算下一项 |
| **内存占用** | 随长度线性增加 | 初始占用极低，按需增长 |
| **无限序列** | 不可能（会死循环或 OOM） | **可以**（如所有质数的流） |

### 3. 实现逻辑（简化版）
```python
class Stream:
    def __init__(self, first, compute_rest=lambda: Stream.empty):
        self.first = first
        self._compute_rest = compute_rest
        self._rest = None

    @property
    def rest(self):
        # 只有在访问 s.rest 时，compute_rest 函数才会被调用
        if self._compute_rest is not None:
            self._rest = self._compute_rest()
            self._compute_rest = None # 记忆化：防止重复计算
        return self._rest
```
# Lazy_Memoization_Tips.md

## 记忆化与环境图技巧

### 1. 记忆化 (Memoization)
惰性调用常配合记忆化使用。其核心逻辑是：**第一次计算时保存结果，之后直接返回保存的值。**

| 步骤 | 行为 |
| :--- | :--- |
| **首次访问** | 执行计算函数 -> 存储结果 -> 返回结果 |
| **二次访问** | 检查缓存 -> 发现已有值 -> 直接返回 |

### 2. 环境图 (Environment Diagram) 考试避坑指南

在画环境图时，如何判断一段代码是否产生了“Lazy”效果？

* **看到 `lambda`：** 只要这个 lambda 没被加上 `()` 调用，它里面的代码（包括 `print`）绝对不会出现在环境图中。
* **看到 `yield`：** 调用该函数时，只会在当前 Frame 创建一个生成器对象，函数内部的 Frame 不会立即展开，直到 `next()` 被调用。
* **函数参数：** Python 默认是 **Eager** 的。如果你写 `f(g(x))`，`g(x)` 会先运行，结果再传给 `f`。除非 `f` 接收的是一个函数名（如 `f(g)`）。

> **CS61A 黄金总结**：
> 凡是看到 **`lambda: ...`** 或者 **`def ...`** 这种将表达式封装在函数里的行为，都是在手动制造一个“延迟求值单元”（通常称为 **Thunk**）。