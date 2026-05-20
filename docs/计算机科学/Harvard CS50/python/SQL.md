![](../../../images/obsidian/cs50_python_SQL/img0001.png)
python csv模组的最优点就是能对列表进行强大的管理，能直接添加并引用列进行计数
![](../../../images/obsidian/cs50_python_SQL/img0002.png) 

有没有更快的解决方法
## SQL

（CRUD）
CREATE， INSERT
READ
UPDATE
DELETE， DROP

指令
sqlite3 xxxxx.db (database) (create a file)
.mode csv (shift to sql mode)
.import xxxxxx.xlxs
.quit (back)

能直接对文件进行操作
![](../../../images/obsidian/cs50_python_SQL/img0003.png)
注意其中的关键词
![](../../../images/obsidian/cs50_python_SQL/img0004.png)
LIKE语法，注意其中若有' use ''
![](../../../images/obsidian/cs50_python_SQL/img0005.png)
GROUP BY语法
![](../../../images/obsidian/cs50_python_SQL/img0006.png)

IMDb
![](../../../images/obsidian/cs50_python_SQL/img0007.png)
对于多行处理
![](../../../images/obsidian/cs50_python_SQL/img0008.png)
使用嵌套的方法
![](../../../images/obsidian/cs50_python_SQL/img0009.png)
同样，通过引入SQL模组（cs50）可以在py中实现终端中才能实现的功能

![](../../../images/obsidian/cs50_python_SQL/img0010.png)
用 .schema 来查找组内元素
一步步，我们慢慢增加SQL语句的功能
![](../../../images/obsidian/cs50_python_SQL/img0011.png)
从songs中选取name
![](../../../images/obsidian/cs50_python_SQL/img0012.png)
接着再加上顺序
![](../../../images/obsidian/cs50_python_SQL/img0013.png)
限制 降序 长度查找
![](../../../images/obsidian/cs50_python_SQL/img0014.png)
加上条件语句
![](../../../images/obsidian/cs50_python_SQL/img0015.png)
调用函数
![](../../../images/obsidian/cs50_python_SQL/img0016.png)
多层嵌套
![](../../../images/obsidian/cs50_python_SQL/img0017.png)
待输入/未定


![](../../../images/obsidian/cs50_python_SQL/img0018.png)
注意，取值的时候 = 只能对应一段值，多段值需要使用 IN
![](../../../images/obsidian/cs50_python_SQL/img0019.png)
大概就像这样，选取，组织表格，增加条件，选择打印顺序(限制)
注意，上面这种始终成立的条件会造成笛卡尔污染，使得程序卡死

![](../../../images/obsidian/cs50_python_SQL/img0020.png)![](../../../images/obsidian/cs50_python_SQL/img0021.png)
![](../../../images/obsidian/cs50_python_SQL/img0022.png)
![](../../../images/obsidian/cs50_python_SQL/img0023.png)
取钱的金额，id 和账户
![](../../../images/obsidian/cs50_python_SQL/img0024.png)
当天打的电话
