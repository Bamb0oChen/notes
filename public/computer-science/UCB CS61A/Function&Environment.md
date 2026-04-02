# Environment and Function
## 纯函数与非纯函数
纯函数`Pure functions`：只有输入（参数），只有输出（返回值）。比如内置函数 `abs`：
```python
    >>> abs(-2)
    2
```
可以把它想象成一台小机器：丢进去一个数，吐出来另一个数。

纯函数的特性是：除了返回值之外没有别的副作用，而且同样的参数永远返回完全相同的结果。

非纯函数`Non-pure functions`：除了返回值之外，调用它们还会产生副作用`side effect`，也就是改变解释器或计算机的某种状态。最常见的副作用就是用 print 在屏幕上额外输出内容：
```python
>>> print(1, 2, 3)
1 2 3
```
虽然 print 和 abs 在交互式环境里看起来差不多，但它们的工作方式完全不同。print 返回的值永远是 None —— Python 里代表“空”的特殊值。交互式解释器不会主动打印 None 值，所以上面例子中看到的 1 2 3，其实是 print 在执行过程中主动打印出来的`副作用`，而不是它的返回值。

# Function Currying 
## Currying(函数科林化):
Transfroming a multi-argument inti a single-arguement, higher-order function
