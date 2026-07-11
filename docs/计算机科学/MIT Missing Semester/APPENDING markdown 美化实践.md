放几个我平时不常用的md美化语法

## <font color="red">颜色</font>

<font color="orange" size=5>这是个字号为5的橙色文字</font>

具体实现

```text
<font color="orange" size=5>这是个字号为5的橙色文字</font>
```

## <span style="background-color: red;">背景</span>

```text
<span style="background-color: yellow;">这是黄色背景</span>
<span style="background-color: #d4fc79;">这是薄荷绿背景</span>
```

## <center>居中</center>

```text
<!-- 居中 -->
<center>这是居中的标题</center>

<!-- 更通用的方式（div 对齐） -->
<div align="center">
  <h2>居中标题</h2>
  <img src="url" width="200">
</div>

<div align="right">右对齐文字</div>
```

## 容器

```text
<!-- 彩色左侧边框 -->
<blockquote style="border-left: 4px solid #FF6B6B; background: #fff5f5; padding: 10px 20px;">
  这是一个粉色警示框
</blockquote>

<!-- 绿色提示框 -->
<blockquote style="border-left: 4px solid #51CF66; background: #f0fff4; padding: 10px 20px;">
  ✅ 成功提示
</blockquote>
```

## 展开

<details>
  <summary><b>点击展开查看答案</b></summary>
  这里是隐藏的内容，点击上方标题即可展开。
  <br>可以包含多行文字和代码。
</details>

实现

```text
<details>
  <summary><b>点击展开查看答案</b></summary>
  这里是隐藏的内容，点击上方标题即可展开。
  <br>可以包含多行文字和代码。
</details>
```

