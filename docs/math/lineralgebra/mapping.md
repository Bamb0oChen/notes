# 矩阵计算和向量映射
在深度学习中，全连接层的权重矩阵实际上就是一种线性映射，通过对输入数据的线性组合生成新的表示。

## 核空间
线性映射的核空间（Null Space），又称零空间，是指所有被映射到零向量的原始向量所构成的集合。形式上，对于线性映射$T:V \to W$
，核空间定义为：
$Null(T) = \{v \in V|T(v) = 0\}$

核空间描述的是线性映射「失去」信息的部分。举例来说，假设一个变换将某些方向上的特征完全压缩为零，那么这些方向就构成了核空间。在应用上，核空间的维数与非零输出部分的维数之间满足著名的秩 - 零度定理（Rank-Nullity Theorem）：
$dim(V) = dim(Null(T)) + dim(Range(T))$

## 像空间

其中`Range`指的是线性映射 T 从 V 中的向量变换得到的向量的集合，可以称作`值域`、`像空间`或者`列空间`，下一节会介绍到。这一定理为我们理解数据降维提供了理论支撑。

从物理视角来看，核空间可以对应于某一系统的静止状态。例如，在电路网络中，节点导纳矩阵的某些特定组合可能会使节点电压变为零，这一现象正是核空间的直观体现。通过这种映射关系，我们能够直观地理解当某些输入信息被「丢失」时，系统可能呈现的零响应态。

人话：
核空间就是和原有向量正交的部分，在映射中会产生0向量导致向量丢失，所以要避免
而像空间就是能被映射的
谱半径就是最大的特征值绝对值，反映了最强的映射能力

## 解决问题 Xavier 的数据处理判断
```py
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np

# 设置随机种子保证可重复性
torch.manual_seed(42)
np.random.seed(42)

# 设备配置
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 数据加载与预处理
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])
train_dataset = torchvision.datasets.MNIST(
    root='./data',
    train=True,
    download=True,
    transform=transform
)
train_loader = torch.utils.data.DataLoader(
    dataset=train_dataset,
    batch_size=128,
    shuffle=True
)

# 定义较深的全连接神经网络模型（使用4个隐藏层）
class DeepFCNet(nn.Module):
    def __init__(self, input_dim=784, hidden_dim=256, output_dim=10, num_hidden=4):
        super(DeepFCNet, self).__init__()
        layers = []
        # 第一层
        layers.append(nn.Linear(input_dim, hidden_dim))
        layers.append(nn.ReLU())
        # 中间的隐藏层
        for _ in range(num_hidden-1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.ReLU())
        # 输出层
        layers.append(nn.Linear(hidden_dim, output_dim))
        self.layers = nn.Sequential(*layers)
    
    def forward(self, x):
        x = x.view(x.size(0), -1)  # 展平图像
        x = self.layers(x)
        return x

# 初始化方法定义
def xavier_init(m):
    if isinstance(m, nn.Linear):
        nn.init.xavier_normal_(m.weight)
        nn.init.zeros_(m.bias)

def normal_init(m):
    if isinstance(m, nn.Linear):
        # 注意：这里使用的随机正态分布初始化标准差是固定值，
        # 可能和网络规模不匹配，从而更容易出现梯度不稳定问题
        nn.init.normal_(m.weight, mean=0.0, std=0.1)
        nn.init.zeros_(m.bias)

# 训练函数（包含梯度记录）
def train_model(init_method, train_loader, num_epochs=5):
    # 使用较深的模型
    model = DeepFCNet().to(device)
    model.apply(init_method)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01)
    
    # 用于记录各层梯度的统计信息，统计所有全连接层参数的梯度
    gradient_stats = {
        'steps': [],
        'mean': [],
        'std': [],
        'losses': []
    }
    
    model.train()
    step_counter = 0
    for epoch in range(num_epochs):
        for i, (images, labels) in enumerate(train_loader):
            images = images.to(device)
            labels = labels.to(device)
            # 前向传播
            outputs = model(images)
            loss = criterion(outputs, labels)
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            
            # 每隔一定步数记录梯度统计信息
            if step_counter % 50 == 0:
                all_grads = []
                # 遍历网络中所有全连接层，收集其梯度
                for module in model.modules():
                    if isinstance(module, nn.Linear) and module.weight.grad is not None:
                        all_grads.append(module.weight.grad.cpu().detach().numpy())
                if all_grads:                    
                    grads_concat = np.concatenate([g.flatten() for g in all_grads])
                    gradient_stats['steps'].append(step_counter)
                    gradient_stats['mean'].append(np.abs(grads_concat).mean())
                    gradient_stats['std'].append(grads_concat.std())
                    gradient_stats['losses'].append(loss.item())
            
            # 参数更新
            optimizer.step()
            step_counter += 1
    return gradient_stats

# 分别训练两种初始化模型

print("Training Xavier Initialized Model…")
xavier_stats = train_model(xavier_init, train_loader)

print("\nTraining Normal Initialized Model…")
normal_stats = train_model(normal_init, train_loader)

# 可视化结果
plt.figure(figsize=(15, 5))

# 1. 梯度均值对比
plt.subplot(1, 3, 1)
plt.plot(xavier_stats['steps'], xavier_stats['mean'], label='Xavier', marker='o')
plt.plot(normal_stats['steps'], normal_stats['mean'], label='Normal', marker='o')
plt.xlabel('Training Steps')
plt.ylabel('Gradient Absolute Mean')
plt.title('Gradient Mean Comparison')
plt.legend()

# 2. 梯度标准差对比
plt.subplot(1, 3, 2)
plt.plot(xavier_stats['steps'], xavier_stats['std'], label='Xavier', marker='o')
plt.plot(normal_stats['steps'], normal_stats['std'], label='Normal', marker='o')
plt.xlabel('Training Steps')
plt.ylabel('Gradient STD')
plt.title('Gradient STD Comparison')
plt.legend()

# 3. 损失曲线对比
plt.subplot(1, 3, 3)
plt.plot(xavier_stats['steps'], xavier_stats['losses'], label='Xavier', marker='o')
plt.plot(normal_stats['steps'], normal_stats['losses'], label='Normal', marker='o')
plt.xlabel('Training Steps')
plt.ylabel('Loss Value')
plt.title('Training Loss Comparison')
plt.legend()

plt.tight_layout()
plt.savefig('initialization_comparison.png', dpi=150)
plt.show()
```