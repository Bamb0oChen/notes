# Basic_Structures.md

## 1. 基础容器对比 (List, Tuple, Array)

在 CS61A 和算法面试中，选择正确的容器决定了程序的性能和代码的简洁度。

### 1.1 核心特性对照表

| 结构 | Python 实现 | 可变性 (Mutable) | 典型应用场景 | 性能特点 |
| :--- | :--- | :--- | :--- | :--- |
| **数组/列表** | `list` | **是** | 动态扩容、频繁增删尾部 | 随机访问 $O(1)$，头部增删 $O(n)$ |
| **元组** | `tuple` | **否** | 函数返回多值、作为字典键 | 比 list 更轻量，内存开销小 |
| **字典** | `dict` | **是** | 键值映射、快速查找 | 平均查找/插入 $O(1)$ |
| **集合** | `set` | **是** | 去重、判断是否存在 | 判断元素是否存在 $O(1)$ |

### 1.2 关键差异：List vs. Tuple
* **切片产生新对象**：无论 `list` 还是 `tuple`，切片操作 `a[:]` 都会产生一个新容器（浅拷贝）。
* **不可变性保障**：由于 `tuple` 不可变，它在多线程或函数传递中更安全，且可以用作 `dict` 的 `key`，而 `list` 不行。

# Linked_Lists.md

## 2. 链表 (Linked Lists)

CS61A 中通常定义 `Link` 类来模拟递归链表。

### 2.1 递归定义
链表要么是空的（`Link.empty`），要么是一个包含 `first` 和 `rest`（另一个链表）的节点。

```python
class Link:
    empty = ()
    def __init__(self, first, rest=empty):
        self.first = first
        self.rest = rest
```
# 02_Linked_List_Advanced.md

## 2.2 链表遍历与解题套路

在 CS61A 中，链表的操作通常分为**递归**和**迭代**两种风格。

| 模式 | 逻辑说明 | 代码模板示例 |
| :--- | :--- | :--- |
| **递归遍历** | 检查是否为空，处理 `first`，递归 `rest` | `if lnk is Link.empty: return ...` |
| **迭代遍历** | 使用 `while` 循环不断移动指针 | `while lnk is not Link.empty: lnk = lnk.rest` |
| **原地修改** | 直接改变节点的 `rest` 指针 | `lnk.rest = lnk.rest.rest` (跳过/删除节点) |



### 2.3 核心解题策略

1.  **递归分治**：
    处理链表问题 = `处理当前节点 (lnk.first)` + `递归处理剩余部分 (lnk.rest)`。
2.  **哨兵节点 (Sentinel)**：
    在涉及插入或删除头节点的操作时，先创建一个 `p = Link(None, original_lnk)`。
    * **理由**：这样原链表的头节点就变成了“中间节点”，处理逻辑统一，最后返回 `p.rest` 即可。
3.  **注意隐式赋值**：
    `lnk.rest.first` 是访问下一个节点的值；`lnk.rest = ...` 是修改指针指向。
# 03_Tree_Structure.md

## 3. 树结构初步 (Trees)

CS61A 的树（Multi-way Tree）通常由一个标签（label）和一组子树（branches）组成。

### 3.1 树的类定义 (Standard Class)
```python
class Tree:
    def __init__(self, label, branches=[]):
        self.label = label
        for b in branches:
            assert isinstance(b, Tree) # 确保子树也是 Tree 实例
        self.branches = list(branches)

    def is_leaf(self):
        return not self.branches
```
# 03_Tree_Traversal_Advanced.md

## 3.2 树递归 (Tree Recursion) 深度解析

树的递归解决思路通常遵循：**“处理当前节点（Root）+ 递归处理子树（Branches）+ 汇总结果”**。

### 3.2.1 路径查找与 Yield 模式 (重点)
当题目要求你找到从根节点到叶子节点的所有路径时，使用生成器（Generator）和 `yield` 是最优雅的方案。

**核心逻辑公式：**
1. **Base Case**: 如果当前节点满足结束条件（如到达叶子），`yield` 当前节点。
2. **Recursive Step**: 遍历子树，从子树返回的每一条“子路径”中，把当前节点拼在最前面。

```python
def find_all_paths(t):
    """返回从根到所有叶子的路径生成器"""
    # 1. 如果是叶子节点，这就是路径的终点
    if t.is_leaf():
        yield [t.label]
    
    # 2. 否则，遍历每一棵子树
    for b in t.branches:
        # 3. 递归获取子树中产生的所有路径
        for path in find_all_paths(b):
            # 4. 将当前节点 label 拼接到子路径的最前面
            yield [t.label] + path
```
# 03_Tree_Algorithm_Templates.md

### 3.2.2 树的常见算法模板对照表

在 CS61A 的考试中，树的问题通常可以归类为以下几种模式。掌握这些模板能帮你快速写出 Base Case 和递归逻辑。

| 任务类型 | 核心逻辑 (Recursive Step) | 示例代码片段 |
| :--- | :--- | :--- |
| **求和/计数** | 当前值 + 子树结果之和 | `t.label + sum([solve(b) for b in t.branches])` |
| **高度/深度** | 1 + 子树中最深的高度 | `1 + max([solve(b) for b in t.branches], default=0)` |
| **映射修改** | 返回一个新的 Tree 对象 | `Tree(fn(t.label), [solve(b) for b in t.branches])` |
| **查找叶子** | 只有当没有 branches 时处理 | `if t.is_leaf(): return [t.label]` |
| **过滤分支** | 仅保留满足条件的子树 | `[solve(b) for b in t.branches if cond(b)]` |



---

## 3.3 树的解题避坑指南

1.  **空分支与 `max()`**: 
    在计算 `max(branches)` 时，如果树是叶子节点，其 `branches` 为空，直接调用 `max()` 会报错。**务必使用 `default` 参数**：`max(..., default=0)`。
2.  **原地修改 vs. 返回新树**:
    * `t.label = new_val`: 原地修改（Mutation）。
    * `return Tree(new_val, ...)`: 返回新对象（Functional），原树不变。
3.  **子树不是列表**: 
    `t.branches` 是一个**列表**，但列表里的每个元素 `b` 都是一个 **`Tree` 实例**。不要直接在 `t.branches` 上调用树的方法。

# 04_Linked_List_Advanced.md

## 4. 链表进阶 (Linked Lists)

CS61A 的链表通常由 `Link` 类实现，其结构是递归的：`Link(first, rest)`。

### 4.1 遍历套路：递归 vs. 迭代



| 模式 | 适用场景 | 核心代码结构 |
| :--- | :--- | :--- |
| **递归 (Recursive)** | 结构转换、过滤、反转 | `if lnk is Link.empty: return ...` <br> `return Link(lnk.first, solve(lnk.rest))` |
| **迭代 (Iterative)** | 原地修改、查找、排序 | `curr = lnk` <br> `while curr is not Link.empty: ...; curr = curr.rest` |

### 4.2 核心解题策略

#### 1. 哨兵节点 (Sentinel/Dummy Node)
这是处理链表“插入”或“删除”最强大的技巧。创建一个指向头部的假节点，可以避免处理“空链表”或“修改头节点”的特殊情况。
```python
def delete_all(lnk, x):
    """删除链表中所有值为 x 的节点"""
    sentinel = Link(0, lnk)
    curr = sentinel
    while curr.rest is not Link.empty:
        if curr.rest.first == x:
            curr.rest = curr.rest.rest # 跳过该节点
        else:
            curr = curr.rest
    return sentinel.rest
```
#### 2. 原地突变 (In-place Mutation)
如果题目要求修改原链表，关键在于操作 `lnk.rest = ...`。记住：修改 `lnk.first` 只改值，修改 `lnk.rest` 才是改结构。

#### 3. 递归合并
处理两个有序链表合并等问题时，递归非常简洁：
`Link(min_val, merge(remaining_part))。`



# 05_General_Structures_Comparison.md

## 5. 基础结构对比 (Tuples, Lists, Arrays)

Python 容器的选择直接影响 $O(n)$ 复杂度和内存开销。

### 5.1 核心特性对照表

| 特性 | List (列表) | Tuple (元组) | Array (C风格数组) |
| :--- | :--- | :--- | :--- |
| **可变性** | **Mutable** (可变) | **Immutable** (不可变) | Mutable (可变) |
| **底层实现** | 指针数组 (Dynamic) | 静态指针数组 | 连续内存块 (Typed) |
| **Hashable** | 否 | **是** (可用作 Dict Key) | 否 |
| **典型应用** | 频繁增删的容器 | 函数返回多值、常量定义 | 大规模数值运算 |

### 5.2 性能与复杂度 ($O$ Notation)

| 操作 | List / Tuple | Linked List (Link) |
| :--- | :--- | :--- |
| **索引访问 `obj[i]`** | $O(1)$ | $O(n)$ |
| **头部插入/删除** | $O(n)$ | **$O(1)$** |
| **尾部插入/删除** | $O(1)$ (仅限 List) | $O(n)$ |
| **长度获取 `len()`** | $O(1)$ | $O(n)$ (需遍历) |

### 5.3 为什么 CS61A 强调 Tuple？
在递归和函数式编程中，使用 `tuple` 代替 `list` 可以防止**意料之外的突变 (Side Effects)**。由于元组不可变，你可以放心地将其作为缓存（Memoization）的键，记录已经计算过的递归结果。

> **考试总结**：
> * 如果你需要“改”：用 `List` 或 `Link` (Mutation)。
> * 如果你需要“稳”：用 `Tuple` (Functional)。
> * 如果你需要“快”：查询用 `Dict/Set`，头部操作用 `Link`。