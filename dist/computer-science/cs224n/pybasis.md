# CS224N NumPy 与 PyTorch 知识点总结

## 一、 NumPy 核心知识点

[cite_start]NumPy 是一个针对矩阵和向量计算进行优化的库，它通过使用 C/C++ 子例程和高效的数据结构，使得计算性能比标准 Python 列表快 5 到 100 倍 [cite: 47, 48]。

### 1. 基础数据类型：`np.ndarray`
* [cite_start]**创建方式**：使用构造函数 `np.array()` [cite: 48]。
* **形状 (Shape)**：
    * [cite_start]1-D 向量：例如 `(3,)` [cite: 49]。
    * [cite_start]行向量：例如 `(1, 3)` [cite: 49]。
    * [cite_start]矩阵：例如 `(2, 2)` [cite: 49]。
    * [cite_start]**注意**：形状 `(N,)`、`(1, N)` 和 `(N, 1)` 在 NumPy 中是不等的 [cite: 50]。

### 2. 数组操作
* [cite_start]**缩减操作 (Reductions)**：如 `np.sum`、`np.mean`、`np.max` 等 [cite: 51]。
    * [cite_start]可以指定轴 (`axis`) 进行缩减，例如 `axis=1` 表示沿着行方向压缩 [cite: 51]。
    * [cite_start]`keepdims=True` 可保留原始维度，防止维度塌陷 [cite: 51]。
* [cite_start]**算术运算**：中缀运算符（如 `+`, `-`, `*`, `**`, `/`）均为**逐元素 (element-wise)** 运算 [cite: 52, 53]。
* **矩阵/向量乘法**：
    * [cite_start]**点积**：`np.dot(u, v)` [cite: 54]。
    * [cite_start]**矩阵乘法**：推荐使用 `np.matmul(A, B)` 或 `A @ B` [cite: 54]。
    * [cite_start]**逐元素乘法 (Hadamard Product)**：直接使用 `A * B` [cite: 54]。
* [cite_start]**转置**：使用 `x.T` [cite: 55]。

### 3. 索引与切片 (Indexing)
* [cite_start]支持布尔索引，例如 `x[x > 0.5]` [cite: 55]。
* [cite_start]可以使用 `np.newaxis` 增加新维度 [cite: 55]。
* [cite_start]使用 ndarray 或范围进行索引会保留被选部分的维度 [cite: 55]。

### 4. 广播机制 (Broadcasting)
* [cite_start]**基本原则**：当对两个数组进行操作时，NumPy 会从最右侧（末尾）维度开始逐一比较它们的形状 [cite: 58, 59]。
* **兼容条件**：两个维度兼容需满足以下之一：
    1. [cite_start]维度大小相等 [cite: 59, 63]。
    2. [cite_start]其中一个维度的大小为 1（该维度会被自动重复以匹配另一方）[cite: 59, 63]。
* [cite_start]**技巧**：如果遇到广播错误，应首先打印 `array.shape` 检查维度是否匹配 [cite: 56, 77]。

### 5. 性能优化
* [cite_start]**避免显式循环**：在 NumPy 中应极力避免对索引或轴使用 `for` 循环，这会导致 10-100 倍的性能下降 [cite: 66, 67]。尽可能使用向量化操作。

---

## 二、 PyTorch 基础

[cite_start]在 CS224N 的后续作业中，PyTorch 是核心工具 [cite: 42]。

### 1. 模型类 (Model Classes)
* [cite_start]**基类**：所有的神经网络模块都必须继承自 `torch.nn.Module` [cite: 42]。
* **结构**：
    * [cite_start]`__init__` 方法：用于初始化网络层 [cite: 43]。
    * [cite_start]`forward` 方法：定义模型的前向传播逻辑 [cite: 43]。

### 2. 深度学习框架背景
* [cite_start]Python 是 PyTorch 和 TensorFlow 等主流深度学习框架的首选语言 [cite: 5, 131]。
* [cite_start]这些框架通常利用 Python 的易用性，同时在底层运行高度优化的 C/C++ 子例程以实现高速运算 [cite: 161]。

---

## 三、 实用调试工具与技巧
* [cite_start]**形状检查**：使用 `array.shape` 查看 NumPy 数组或张量的维度 [cite: 76]。
* [cite_start]**数据类型检查**：使用 `array.dtype` 检查数据类型（如精度问题）[cite: 76]。
* [cite_start]**断点调试**：在代码中插入 `import pdb; pdb.set_trace()` 启动交互式调试 [cite: 76]。
* [cite_start]**常见错误**：`ValueError` 通常是由广播机制或矩阵乘法中的维度不匹配引起的 [cite: 77]。