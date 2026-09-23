[视频资料](https://www.bilibili.com/video/BV16KsnzKEVU/?spm_id_from=333.1387.collection.video_card.click&vd_source=d29a21e1671c0e8f0a10617e8e3990f6)

CUDA这个部分是我在后面才写的，这个地方我刚好又学了一遍

为什么我们要采用gpu优化其实我在前面已经说过了，这个地方我们重新来看一下cuda的实际操作搭建

首先我们需要先下载我们的cuda插件，注意你的显卡适配和相系统版本

进入我们的编程部分，首先我们要引入我们的代码库，一般是

```c
#include "cuda_runtime.h"
#include "device_launch_parameters.h"

#include <stdio.h>
```
接下来我们要将我们的指针指向我们的显卡
```c
int a[] = {1,2,3};
int b[] = {4,5,6};
int c[sizeof(a) / sizeof(int)] = {0};

int* cudaA = 0;
int* cudaB = 0;
int* cudaC = 0;
```

在有了接口以后，我们要分配我们的计算空间

```c
cudaMalloc(&cudaA, sizeof(a));
cudaMalloc(&cudaA, sizeof(b));
cudaMalloc(&cudaA, sizeof(c));

cudaMemcpy(cudaA, a, sizeof(a), cudaMemcpyHostToDevice);
cudaMemcpy(cudaB, b, sizeof(b), cudaMemcpyHostToDevice);
```
接下来我们要开始我们的计算
首先我们要做好一个双精度全局函数，让编译器做好准备，提前编译
```c
__global__ void vectorAdd(int* a, int* b, int* c)
{
    int i = threadIdx.x;
    c[i] = a[i] + b[i]
}
```

接着我们就要实例化调用了

```c
vectorAdd <<< 1, sizeof(a) / sizeof(int)>>> (cudaA, cudaB, cudaC);
```
这句话就是CPU告诉我们的gpu：我们现在有一个块，他的占用位数/线程是sizeof(a) / sizeof(int)，现在用后面的三个数去调用它

最后，我们要把内容写回主机

```c
cudaMemcpy(c, cudaC, sizeof(c), cudaMemcpyDeviceToHost);

return;
```
