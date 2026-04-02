# 01_Slicing.md

## 1. 序列切片 (Slicing)
**标准格式：** `sequence[start:stop:step]`
**核心逻辑：** 左闭右开 `[start, stop)`

| 语法 | 说明 | 示例 (`a = [0, 1, 2, 3, 4]`) | 结果 |
| :--- | :--- | :--- | :--- |
| `a[1:3]` | 基础范围 | `a[1:3]` | `[1, 2]` |
| `a[:2]` | 从头开始 | `a[:2]` | `[0, 1]` |
| `a[2:]` | 取到末尾 | `a[2:]` | `[2, 3, 4]` |
| `a[-1]` | 末尾索引 | `a[-1]` | `4` |
| `a[-3:]` | 最后三个 | `a[-3:]` | `[2, 3, 4]` |
| `a[::-1]` | **序列反转** | `a[::-1]` | `[4, 3, 2, 1, 0]` |
| `a[::2]` | 步长取值 | `a[::2]` | `[0, 2, 4]` |
| `a[:]` | 浅拷贝 | `b = a[:]` | 创建新列表对象 |
# 02_Functional_Programming.md

## 2. 函数式编程与算法语法

### 2.1 列表推导式 (List Comprehension)
```python
# [expression for item in iterable if condition]
nums = [1, 2, 3, 4, 5, 6]

# 基础过滤与转换
evens_squared = [x**2 for x in nums if x % 2 == 0] # [4, 16, 36]

# 嵌套循环 (等同于双重 for 嵌套)
pairs = [(i, j) for i in range(2) for j in range(2)]
# [(0, 0), (0, 1), (1, 0), (1, 1)]
```
### 2.2Lamba表达式
```python
# lambda 参数: 表达式 (隐式返回)
f = lambda x, y: x + y
res = (lambda x: x * x)(5) # 25
```

### 2.3 高阶函数映射

| 函数 | 说明 | 示例 |
| :--- | :--- | :--- |
| `map(f, it)` | 应用 f 到每个元素 | `list(map(abs, [-1, 2]))` -> `[1, 2]` |
| `filter(f, it)` | 保留 f 为 True 的元素 | `list(filter(lambda x: x>0, [-1, 1]))` -> `[1]` |
| `zip(it1, it2)` | 并行迭代打包 | `list(zip('AB', [1, 2]))` -> `[('A',1), ('B',2)]` |
| `reduce(f, it)` | 归约计算 | `reduce(lambda x,y: x+y, [1,2,3])` -> `6` |

# 03_File_Handling.md

## 3. 文件操作 (File I/O)

### 3.1 模式对照表
| 模式 | 描述 | 注意事项 |
| :--- | :--- | :--- |
| `'r'` | 读取 (Read) | 默认模式，文件不存在报错 |
| `'w'` | 写入 (Write) | 文件存在则清空，不存在则创建 |
| `'a'` | 追加 (Append) | 在文件末尾写入 |
| `'r+'` | 读写 | 不会清空文件，可同时进行读写 |

### 3.2 核心代码模板
```python
# 推荐写法：使用 with 自动关闭文件
with open('data.txt', 'r', encoding='utf-8') as f:
    # 方式A: 一次性读取全文
    content = f.read()
    
    # 方式B: 逐行读取到列表
    lines = f.readlines()
    
    # 方式C: 迭代器读取 (处理超大文件最优)
    for line in f:
        process(line.strip()) # strip() 去除换行符

# 写入
with open('out.txt', 'w') as f:
    f.write("Text\n")
    f.writelines(["Line1\n", "Line2\n"])
```

# 04_Data_Structures.md

## 4. 高效数据结构 (Dict & Set)

### 4.1 字典 (Dictionary) - $O(1)$ 复杂度
| 方法 | 说明 |
| :--- | :--- |
| `d.get(k, default)` | 安全取值，key 不存在时不报错而是返回默认值 |
| `d.items()` | 遍历键值对 `for k, v in d.items():` |
| `d.keys() / d.values()` | 获取所有键 / 获取所有值 |
| `d.pop(k)` | 删除键 k 并返回对应的值 |
| `d.setdefault(k, v)` | key 不存在则设置默认值 v |

### 4.2 集合 (Set) - 去重与运算
* **定义**：`s = {1, 2, 3}` 或 `set(iterable)`
* **运算**：
    * 交集：`s1 & s2`
    * 并集：`s1 | s2`
    * 差集：`s1 - s2`
    * 对称差：`s1 ^ s2`


# 05_Scope_And_State.md

## 5. 作用域与状态管理 (CS61A 重点)

### 5.1 nonlocal 关键字
用于在闭包（嵌套函数）中修改外部非全局变量。
```python
def make_counter():
    count = 0
    def counter():
        nonlocal count  # 必须声明，否则 count += 1 会报 UnboundLocalError
        count += 1
        return count
    return counter
```
### 5.2关键字
在函数内部修改局部变量
```python
x = 10
def modify():
    global x
    x = 20
```
### 递归限制
Python 默认递归深度约为 1000 层。
```python
import sys
sys.setrecursionlimit(2000) # 手动提升递归深度限制
```

# 06_Builtin_Algorithms.md

## 6. 算法必备内置函数

| 函数 | 说明 | 示例 |
| :--- | :--- | :--- |
| `enumerate(it)` | 返回 `(index, value)` | `for i, v in enumerate(['a', 'b']):` |
| `sorted(it, key=f)` | 返回排序后的新列表 | `sorted(d, key=lambda x: d[x])` |
| `reversed(it)` | 返回反向迭代器 | `for x in reversed([1, 2, 3]):` |
| `all(it)` | 逻辑“与”：全部为 True 才返回 True | `all([True, True, False])` -> `False` |
| `any(it)` | 逻辑“或”：任一为 True 则返回 True | `any([0, 0, 1])` -> `True` |
| `min/max(it, key=f)` | 根据规则取最值 | `max(['a', 'abc'], key=len)` -> `'abc'` |
| `sum(it, start=0)` | 序列求和 | `sum([1, 2, 3])` -> `6` |

# 07_Dictionary_Advanced_Examples.md

### 7.2 进阶代码示例

#### 方案 A：使用 setdefault (内置方法)
```python
def group_by(s, fn):
    grouped = {}
    for i in s:
        # setdefault(key, default): 
        # 1. 若 key 不存在，将 key: [] 存入并返回 []
        # 2. 若 key 存在，直接返回对应的列表
        grouped.setdefault(fn(i), []).append(i)
    return grouped
```
#### 方案 B: 使用defaultdict
```python
from collections import defaultdict

def group_by(s, fn):
    # 初始化时指定 factory 函数为 list
    # 访问任何不存在的键都会自动创建一个新列表
    grouped = defaultdict(list) 
    for i in s:
        grouped[fn(i)].append(i)
    return dict(grouped)
```
# 08_Dictionary_Operations_Table.md

### 8.1 常见字典操作表

| 操作 | 语法 | 复杂度 | 备注 |
| :--- | :--- | :--- | :--- |
| **成员检查** | `key in d` | $O(1)$ | 检查的是键(key)而非值 |
| **安全取值** | `d.get(key, default)` | $O(1)$ | 避免 KeyError 的推荐做法 |
| **删除并返回** | `val = d.pop(key)` | $O(1)$ | 若键不存在可加默认值 `pop(k, def)` |
| **合并字典** | `d1.update(d2)` | $O(M)$ | 将 d2 的内容覆盖合并到 d1 |
| **视图获取** | `d.keys() / d.values()` | $O(1)$ | 返回的是动态视图，非列表 |
| **清空** | `d.clear()` | $O(1)$ | 原地清空所有项 |

> **CS61A 核心提示**：字典是**可变对象 (Mutable)**。在递归中传递字典时，所有递归层级共享同一个字典实例（除非显式使用 `.copy()`）。

# 09_Mutation_vs_Reassignment.md

## 9. 突变 (Mutation) vs. 重赋值 (Reassignment)

在 Python 中没有“指针”这个词，但所有变量本质上都是“标签（Label）”，指向内存中的对象。你看到的“指针效果”其实是引用（Reference）。
判断是否有“指针效果”，关键在于区分：你是修改了“标签指向的对象”（Mutation），还是把“标签撕下来贴到了新地方”（Reassignment）。
这是理解 Python 内存模型的关键。

### 9.1 核心区别

| 行为 | 操作示例 | 指针效果 (指向相同对象) | 内存说明 |
| :--- | :--- | :--- | :--- |
| **突变 (Mutation)** | `s.append(t)`, `s[0] = x` | **有** | 原地修改对象内容，所有指向该对象的变量都会看到变化。 |
| **重赋值 (Reassignment)** | `t = 0`, `s = [1, 2]` | **无** | 将变量名（标签）指向一个全新的对象，原对象不受影响。 |
| **浅拷贝 (Shallow Copy)** | `b = a[:]`, `a + [t]` | **部分有** | 创建一个新容器，但容器内的“子元素”依然指向原有的对象。 |

### 9.2 如何判断？

1. **看是否调用了改变对象的方法**：`append`, `extend`, `pop`, `insert` 都是在原地修改（指针指向没变，内容变了）。
2. **看是否存在 `=` 直接给变量名赋值**：`s = ...` 是让 `s` 离弃旧爱，寻找新欢。
3. **看索引赋值**：`s[0] = ...` 是突变。虽然有 `=`，但它是修改 `s` 这个容器内部的“指针”。


# 10_Environment_Diagram_Analysis.md

## 10. 环境图 (Environment Diagrams) 操作拆解

根据你提供的讲义图示，我们将操作归纳如下表：

### 10.1 操作结果对照表

| 操作类型 | 典型示例 | 对原对象 `s` 的影响 | 对 `t` 的指向影响 |
| :--- | :--- | :--- | :--- |
| **Append** | `s.append(t)` | `s` 内部增加一个“指针”指向 `t` 所在的对象。 | 无影响。但若随后 `t=0`，`s` 内部依然指向原来的列表。 |
| **Extend** | `s.extend(t)` | `s` 复制 `t` 中所有元素的“指针”放入自己内部。 | 无影响。`s` 和 `t` 现在共享元素的指向。 |
| **Addition** | `a = s + [t]` | **无影响**。创建一个全新的列表对象 `a`。 | 无影响。`a` 的最后一个元素指向 `t` 的对象。 |
| **Slicing** | `b = a[1:]` | **无影响**。创建一个全新的列表对象 `b`。 | **关键**：`b` 里的元素和 `a` 里的元素指向同一个对象。 |

### 10.2 为什么 `t = 0` 后 `s` 不变？
在图中第一行：
1. 执行 `s.append(t)`：`s` 的末尾存了一个地址，指向 `[5, 6]`。
2. 执行 `t = 0`：变量 `t` 这个标签被拨开了，指向了整数 `0`。
3. **结果**：`s` 里的地址没变，它依然死死地指向那个 `[5, 6]` 的列表对象。

> **CS61A 黄金定律**：赋值语句 `target = expr` 永远不会改变 `expr` 所指向的对象，它只改变 `target` 这个名字的指向。