# 向量空间和数据表示
    在学习本章前，默认你已经掌握了线性代数的相关内容（向量空间，特征值，特征向量）
我们将以一个经典的机器学习问题——MNIST 手写数字图像的处理为例，讨论高维数据在实际问题中遇到的「维度灾难」以及我们如何借助数学工具有效应对这一挑战。

MNIST 数据集是机器学习领域中一个广泛使用的标准数据集，由大量手写数字构成，其每幅图像通常为 28×28 的灰度图像，即每幅图像可以被看作 784 维（28 × 28 = 784）的向量。这种高维表示虽然在一定程度上保留了图像的细节信息，但也给数据处理带来了不少问题。

## MNIST数据集
在实际应用中，由于图像的每个像素往往存在高度冗余的信息，直接在 784 维空间中进行处理往往让计算量骤增，称为「维度灾难」。其主要表现为：

- 高维空间中数据点间距离的直观意义失效，数据稀疏性增加，传统的欧氏距离等度量手段不再适用。因为所有点之间的差异趋于相同，导致距离度量失去了区分度；
- 模型在高维空间下容易陷入维数过多所带来的数据噪声和计算不稳定性；
- 模型在训练时易于过拟合，同时训练复杂度和存储需求显著增加。模型不仅需要捕捉数据的主要结构，还需要处理高维空间中各种冗余信息，增加了有效模型构建的难度。
因此，从数据压缩和降维的角度出发，有效地提取图像中的主要特征、去除冗余信息，是机器学习中十分重要的一步。

## 解决问题：算法——PAC降维

主成分分析（PCA）是机器学习中最常用的降维算法之一，其核心思想在于：

1. 找到数据中方差最大的几个方向，这些方向通常包含了数据中大部分的有效信息；
2. 将原始数据投影到这些方向上，从而降低数据维数，同时尽可能保留数据的变异信息。
具体操作流程如下：

1. 对原始数据进行均值归一化处理；
2. 计算数据的协方差矩阵，协方差矩阵反映了数据各个维度之间的相关性；

协方差矩阵$C$的计算公式为：

$\frac{1}{N -1}{\textstyle \sum_{i = 1}^{N}} (x_i - \bar{x})(x_i - \bar{x})^T$

其中
$N$为样本数量，
$x_i$为第$i$个样本向量，
$\bar{x}$为样本均值向量；

- 对协方差矩阵进行特征值分解，找到相应的特征向量；
- 按照特征值从大到小排序，选取前$k$个特征向量构成投影矩阵；
- 利用投影矩阵将高维数据映射$k$维空间中，得到降维后的数据表示。
- 这种方法直接利用向量空间中基和维度的概念，将数据的主要「方向」提取出来，从而构造出一个新的特征空间。算法上看，PCA 不仅能够在一定程度上缓解「维度灾难」，还为后续的聚类、分类等任务提供了更简洁、更有效的数据表示。

    为什么要取特征值？
    在前面的学习中，我们知道特征向量是一种在矩阵变化后保持方向不变的向量，这反映了矩阵的特征。与此同时，我们同样可以从特征值中发现矩阵对这个方向的“加长能力”，这反映了矩阵在这个方向的权重

## 代码：PCA 对 MNIST 数据进行降维
下面给出基于 sklearn 中 PCA 接口的具体代码实现：
```py
"""
1. 数据预处理：对MNIST图像数据进行展平（将28×28的二维图像转换成784维向量），并进行标准化。
2. 计算协方差矩阵，通过样本均值归一化后的数据构造协方差矩阵。
3. 对协方差矩阵进行特征值分解，选取前 k 个特征向量构成投影矩阵。
4. 将原始数据投影到低维空间，得到降维结果。
"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from torchvision import datasets, transforms

# 下载MNIST数据集（这里只使用测试集的一部分）
transform = transforms.Compose([transforms.ToTensor()])
mnist_test = datasets.MNIST(root='./data', train=False, download=True, transform=transform)

# 提取部分数据进行试验：例如选择前2000个样本证明算法思路
num_samples = 2000
data = mnist_test.data[:num_samples].numpy().reshape(num_samples, -1).astype(np.float32)
labels = mnist_test.targets[:num_samples].numpy()

# 数据标准化：扣除均值，使得每个特征的均值为0
data_mean = np.mean(data, axis=0)
data_centered = data - data_mean

# PCA降维至二维
pca = PCA(n_components=2)
data_pca = pca.fit_transform(data_centered)

# 可视化结果（二维散点图）
plt.figure(figsize=(8,6))
# 分别取第一主成分和第二主成分作为x/y坐标
scatter = plt.scatter(data_pca[:, 0], data_pca[:, 1], c=labels, cmap='viridis', s=15)
plt.legend(*scatter.legend_elements(), title="Digits")
plt.title("MNIST数据PCA降维到二维")
plt.xlabel("主成分1")
plt.ylabel("主成分2")
plt.show()
```