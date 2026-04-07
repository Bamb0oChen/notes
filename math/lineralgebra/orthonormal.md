# 线性方程组和正交化

在实际问题中，尤其是在机器学习领域，我们常常会遇到**超定系统**，即方程数量多于未知数的情况。此时一般不存在能够同时满足所有方程的精确解，最小二乘法便成为求解问题误差最小近似解的有效手段。

对于超定系统$Ax = b$，最小二乘法的目标是找到
$$
x^* = arg min_x\frac{1}{2}||Ax - b||^2
$$
求最小值的必要条件是目标函数的一阶导数（梯度）为零，即
$$
\bigtriangledown J(x) = A^{T}(Ax - b) = 0
$$
这就引出了所谓的正规方程（Normal Equation）：
$$
A^T Ax= A^T b
$$
在满足适当条件（例如
非奇异）的情况下，这一方程组有唯一的解，给出目标函数的极小值点。

## 问题解决：糖尿病线性回归预测

```py
from sklearn.datasets import load_diabetes
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import numpy as np

# 加载数据集
diabetes = load_diabetes()
X, y = diabetes.data, diabetes.target

# 数据标准化
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 添加偏置项
X_b = np.c_[np.ones((X.shape[0], 1)), X_scaled]

# 划分训练集/测试集 (80:20)
X_train, X_test, y_train, y_test = train_test_split(
    X_b, y, test_size=0.2, random_state=42
)
## 测试工具：
from sklearn.metrics import mean_squared_error, r2_score

def evaluate_model(theta, X, y_true):
    y_pred = X @ theta
    mse = mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return mse, r2
## 可视化工具：
import matplotlib.pyplot as plt

def plot(theta):
    plt.figure(figsize=(10,5))
    # 真实值 vs 预测值散点图
    plt.subplot(1,2,1)
    y_pred = X_test @ theta
    plt.scatter(y_test, y_pred, alpha=0.6)
    plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
    plt.xlabel("True Values")
    plt.ylabel("Predictions")
    
    # 残差分布图
    plt.subplot(1,2,2)
    residuals = y_test - y_pred
    plt.hist(residuals, bins=30, edgecolor='k')
    plt.xlabel("Residuals")
    plt.ylabel("Frequency")
    
    plt.tight_layout()
    plt.show()
```