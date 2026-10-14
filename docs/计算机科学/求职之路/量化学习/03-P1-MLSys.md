# P1：MLSys

CSAPP 尚未完成不妨碍尝试 HW0，但课程要求的 Python、C++、线性代数、微积分、概率与机器学习基础需要逐项补齐。

## CMU：先理解深度学习框架

[课程官网](https://dlsyscourse.org/) · [官方 GitHub](https://github.com/dlsyscourse)

- [ ] [HW0](https://github.com/dlsyscourse/hw0)：独立完成基础诊断、Softmax 与梯度实现；遇到知识缺口先补。
- [ ] [HW1](https://github.com/dlsyscourse/hw1)：计算图、自动微分、梯度验证。
- [ ] [HW2](https://github.com/dlsyscourse/hw2)：网络模块、优化器、训练流程。
- [ ] **HW3**：NDArray、CPU / CUDA 后端；先补缓存、数据布局和 GPU 并行基础。
- [ ] **HW4（后续）**：卷积、RNN 等模型实现。

官网目前为 2026 版，录像含 2022 版。HW3 / HW4 的可访问官方材料入口尚未确认，开始前从对应版本课程获取，不使用猜测链接。

## Stanford CS336：模型与系统优化

[Spring 2025 课程、讲义与视频](https://cs336.stanford.edu/spring2025/)

- [ ] [A1 Basics](https://github.com/stanford-cs336/assignment1-basics)：tokenizer、Transformer、优化器与小型训练基线。
- [ ] [A2 Systems](https://github.com/stanford-cs336/assignment2-systems)：benchmark、profiling、注意力优化和并行训练实验。

跟随 2025 课程时选择对应 `spring2025` 分支。先确认 GPU / 多卡需求；只有 CPU 时先完成支持的部分，未运行的实验明确标记。

## 推进标准

- [ ] 独立解释前向、反向、参数更新与训练 / 评估区别。
- [ ] 用测试验证算子与梯度。
- [ ] 建立测量基线，固定输入、精度、环境，处理 GPU 同步和预热。
- [ ] 用证据判断计算、访存或调度瓶颈。
- [ ] 任何优化同时检查正确性、性能、显存与数值变化。
