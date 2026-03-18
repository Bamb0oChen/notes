这门课作为cs338的先修课，我预计使用10小时学完，所以就不进行详细的分级了

**主要的思想**：梯度，优化，pytorch，词向量，前馈神经网络，循环网络

1. 独热向量（one-hot vectors）：词向量组只包含一个1元素，可以用点积直接反映出在莫格维度上的相关度情况

## word2vec 
从大量文本开始，实现文本的向量化1，其中的本质就是在固定的context窗口（大小为m）进行遍历，使得当前词出现时周边词的条件概率最高，即：

$$
Likelihood = L(\theta) = \prod_{t=1}^{T}\prod_{-m\le j\le m (j \neq 0)} P(w_{t+j}|w_t;\theta)
$$
但是又两个问题
1.不符合下降的原则
2.连乘很容易导致数据爆炸

所以优化成
$$
J(\theta)=-\frac{1}{T} \log L(\theta)=-\frac{1}{T} \sum_{t=1}^{T} \sum_{\substack{m \leq j \leq m \\ j \neq 0}} \log P\left(w_{t+j} \mid w_{t} ; \theta\right)
$$
1. 增加了负号
2. 用了取对的方式

有点像CNN也是用窗口去进行计算
```text
G老师给了我证明
    你觉得像，主要是因为这几点“表面结构一致”：

（1）都有参数矩阵

Word2Vec：embedding matrix（𝑉,𝑈）

CNN：卷积核（filters）

✔ 都是在学“特征表示”

（2）都有“局部窗口”

Word2Vec：context window（±m）

CNN：receptive field（卷积窗口）

✔ 都是在利用“局部信息”

（3）都用梯度下降优化

都在最小化 loss

都在反向传播更新参数

不同点：
4. 本质区别（重点）
（1）有没有“空间结构”

CNN：

输入是有结构的（图像）

卷积利用空间局部性 + 平移不变性

Word2Vec：

输入是离散 token（one-hot）

没有空间结构

“窗口”只是人为定义的上下文

👉 本质不同：

CNN 是 结构建模，Word2Vec 是 统计共现建模

（2）计算方式

CNN：
y=W∗x（卷积）

Word2Vec：
score=u·v（点积）

👉 一个是局部加权求和（卷积）
👉 一个是向量相似度（内积）

（3）目标函数

CNN（分类）：
P(y∣x)

Word2Vec：
P(context word∣center word)
👉 Word2Vec 本质是：
语言模型的简化版（只看局部条件概率）
```
所以我们现在的概率这样计算
$$
P(o|c) = \frac{exp(u_0^T v_c)}{\sum_{W \in V}exp(u_0^T v_c)}
$$
也就是大名鼎鼎的softmax：
$$
softmax(x_i)=\frac{exp(x_i)}{\sum_{j=1}^n exp(x_i)} = p_i 
$$

然后，只要对这个函数取关于w的偏导，就能成功的从原来的函数中提取出关于w下降或上升的趋势，接着就是机器学习的任务了

不同的取样模型？
词袋（word-bag）模型：选取所有上下文出现过的词然后做词向量乘法
跳字（skip-words）模型：就是上面的词框技术
负采样（negative sampling）:用少量随机负样本，把原本的全词表预测问题转化为二分类任务，从而高效学习词向量。