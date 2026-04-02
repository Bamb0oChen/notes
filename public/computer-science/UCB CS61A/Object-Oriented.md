# 面向对象的编程
## 面向对象是什么
核心思想————封包：数据抽象并捆绑信息
    面向对象编程的理念是，你考虑你的程序以及它执行的所有计算，不是作为一个长长的信息列表，然后是在该列表上操作的函数，而是一堆不同的对象彼此交互。The idea behind object-oriented programming is that you think about your program and allof the computation that itperforms not as one long list of information and then functionsoperating on that list, but instead a bunch of different objects that interact with each other

---

## 入门面向对象
1. 类
   定义了对象活动的方式
2. 对象
   是类中的具体物品，类是他的形式
3. 方法
    方法与函数的区别在于，函数通常在全局框架中定义，可以在任何值上调用，而方法特定于特定对象。And what makes methods different from functions is that a function is typically defined in theglobal frame, and it can be called on any value, whereas a method is specific to a particular object

## 面向对象的代码构造
```python
class Account:
'''
init is a special method name for the function that constructs an Account instance
'''
def__init__(self,account_holder):
    self.balance = 0
    self.holder = account_holder
'''
self is the instance of the Account class on which deposit was invoked: a.deposit(10)
'''
def deposit(self, amount):
    self.balance = self.balance + amount
    return self.balance
def withdraw(self, amount):
    if amount > self.balance:
        return 'Insufficient funds'
    self.balance = self.balance - amount
    return self.balance
```

# 类

类本质上和结构体有点像
但是和一般的结构体不一样，类需要自己定义行为，一个类涵盖了相关的行为
