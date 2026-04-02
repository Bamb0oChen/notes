# 01-methodology.md

## 方法论总纲（SICP 视角）

在 SICP 中，程序不是“求解步骤”，而是对某个数学对象的递归定义
（recursive specification）的直接表达。

写递归程序时，只回答三个问题：

- 研究对象是什么
- 基本情况是什么
- 递归情况下如何由更小的同类对象构成

程序结构必须与递归定义结构一一对应。
# 02-generator-role.md

## Generator 的角色与意义

返回列表的递归：
- 一次性枚举所有结果

Generator：
- 按递归结构逐个枚举结果（lazy enumeration）

Generator 的意义在于：
将“返回一个集合”
转化为“按递归定义顺序枚举集合元素”。

Generator 不是技巧，而是结构表达工具。
# 03-prefixes.md

## 经典案例一：prefixes(s)

### 研究对象

字符串 s 的所有前缀（prefixes）。

### 递归定义

- 若 s 为空串：没有前缀
- 若 s 非空：
  - s[:-1] 的所有前缀
  - 以及 s 本身

### 代码实现

```python
def prefixes(s):
    if s:                                   # s 非空（递归情况）
        yield from prefixes(s[:-1])         # 枚举 s[:-1] 的所有前缀
        yield s                             # 枚举当前字符串 s 本身
```

# 04-substrings.md

## 经典案例二：substrings(s)

### 研究对象

字符串 s 的所有子串（substrings）。

### 递归定义

- 若 s 为空串：没有子串
- 若 s 非空：
  - 所有以 s[0] 开头的子串
  - 以及 s[1:] 的所有子串

### 关键等价关系

任何以 s[0] 开头的子串，本质上都是 s 的一个前缀。

### 代码实现

```python
def substrings(s):
    if s:                                   # s 非空（递归情况）
        yield from prefixes(s)              # 枚举所有以 s[0] 开头的子串
        yield from substrings(s[1:])         # 枚举 s[1:] 的所有子串


```
# 05-partitions.md

## 经典案例三：partitions(n, m)

### 问题定义

partitions(n, m) 表示：
将整数 n 表示为若干个正整数之和，
且每个整数不超过 m，
枚举所有满足条件的划分方式。

### 递归分解

任何合法划分必然且只属于以下两类之一：
1. 使用了整数 m
2. 完全没有使用整数 m

### 代码实现

```python
def partitions(n, m):
    if n < 0 or m == 0:                      # 不存在合法划分
        return []

    exact_match = []
    if n == m:
        exact_match = [[m]]                  # 唯一划分：[m]

    with_m = [p + [m] for p in partitions(n - m, m)]
                                                # 至少使用一个 m 的划分

    without_m = partitions(n, m - 1)          # 完全不使用 m 的划分

    return exact_match + with_m + without_m   # 合并所有合法划分


```
# 06-correctness.md

## 判断递归 / Generator 是否正确的标准

在 CS61A / SICP 中：

- 不从运行过程理解递归
- 只从递归定义理解程序

判断标准：

- 每一条 yield / yield from
- 必须能对应递归定义中的某一条
- 若无法指回定义，该语句是结构性错误
# 07-training.md

## 重修训练流程（强制）

### 步骤一：先写递归定义（禁止写代码）

模板：
- 研究对象是：______
- 基本情况是：______
- 递归情况下，它由以下部分组成：
  1. ______
  2. ______

### 步骤二：逐条翻译成代码

- 一条定义对应一条 yield 或 yield from
- 禁止使用 append
- 禁止使用临时列表（除非问题定义本身要求）

### 步骤三：自检

只给出递归定义，
是否可以直接写出结构一致的代码？
