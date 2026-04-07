# 第一步：预处理数据
为了预处理数据集，我们需要将文本转换为模型能够理解的数字。在 第二章 我们已经学习过。这是通过一个 Tokenizer 完成的，我们可以向 Tokenizer 输入一个句子或一个句子列表。以下代码表示对每对句子中的所有第一句和所有第二句进行 tokenize：

```py
from transformers import AutoTokenizer

checkpoint = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
tokenized_sentences_1 = tokenizer(raw_datasets["train"]["sentence1"])
tokenized_sentences_2 = tokenizer(raw_datasets["train"]["sentence2"])
```
不过在将两句话传递给模型，预测这两句话是否是同义之前，我们需要给这两句话依次进行适当的预处理。Tokenizer 不仅仅可以输入单个句子，还可以输入一组句子，并按照 BERT 模型所需要的输入进行处理：

```py
inputs = tokenizer("This is the first sentence.", "This is the second one.")
inputs
Copied
{
    "input_ids": [
        101,
        2023,
        2003,
        1996,
        2034,
        6251,
        1012,
        102,
        2023,
        2003,
        1996,
        2117,
        2028,
        1012,
        102,
    ],
    "token_type_ids": [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1],
    "attention_mask": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
}
```
我们在 第二章 讨论了 输入词id(input_ids) 和 注意力遮罩(attention_mask) ，但尚未讨论 token类型ID(token_type_ids) 。在本例中， token类型ID(token_type_ids) 的作用就是告诉模型输入的哪一部分是第一句，哪一部分是第二句。
# 第二步：使用trainer微调
## Training
### 1. 定义 TrainingArguments

`TrainingArguments` 是微调过程中非常重要的配置对象，它包含了训练过程中所需的超参数。最重要的参数包括：
- output_dir：指定保存模型和中间检查点的位置。
- evaluation_strategy：指定评估策略，是在每个 epoch 结束时评估，还是每隔一定步数评估。
- learning_rate：定义学习率。
- per_device_train_batch_size：定义每个设备上的训练批量大小。
- per_device_eval_batch_size：定义每个设备上的评估批量大小。
- num_train_epochs：定义训练的 epoch 数。
例如，如果你希望每个 epoch 结束时评估模型的性能，可以设置：
```py
from transformers import TrainingArguments

training_args = TrainingArguments(
    "test-trainer",                  # 模型保存路径
    evaluation_strategy="epoch",     # 每个 epoch 结束时评估模型
    learning_rate=5e-5,              # 学习率
    per_device_train_batch_size=16,  # 每个设备的训练批量大小
    per_device_eval_batch_size=64,   # 每个设备的评估批量大小
    num_train_epochs=3,              # 训练的 epoch 数量
    weight_decay=0.01                # 权重衰减
)
```
### 2. 加载预训练模型

我们使用 `AutoModelForSequenceClassification` 来加载预训练模型。在这个步骤中，除了加载预训练的模型参数外，还会根据任务的需要初始化一个新的分类头（head），这部分头部用于适应我们特定的任务，比如句子分类任务。
```py
from transformers import AutoModelForSequenceClassification

model = AutoModelForSequenceClassification.from_pretrained(checkpoint, num_labels=2)
```
`checkpoint` 是预训练模型的路径（例如，"bert-base-uncased"）。
`num_labels` 是分类任务的标签数量。在这个例子中，num_labels=2 表示这是一个二分类任务（如 MRPC 数据集中的“相似/不相似”分类）。
### 3. 定义 Trainer
Trainer 是 Hugging Face 提供的一个高级 API，它集成了训练、验证和推理的所有常用操作。通过 Trainer，我们将模型、数据集、训练参数等配置传入其中，方便进行训练和评估。
```py
from transformers import Trainer

trainer = Trainer(
    model,                                # 加载的预训练模型
    training_args,                        # 训练参数
    train_dataset=tokenized_datasets["train"],  # 训练数据集
    eval_dataset=tokenized_datasets["validation"],  # 验证数据集
    tokenizer=tokenizer,                   # 用于tokenizing数据的tokenizer
)
```
### 4. 开始训练

一旦定义好 Trainer，就可以调用 trainer.train() 来开始微调模型。训练过程会自动完成以下操作：

数据预处理（tokenize、padding）。

前向传播、反向传播和优化。

每隔一定的步数（logging_steps）报告损失。

每个 epoch 结束时（如果设置了 evaluation_strategy="epoch"）进行验证评估。
```py
trainer.train()
```
### 5. 评估模型

微调完成后，我们可以通过调用 trainer.evaluate() 来评估模型在验证集上的表现。如果你设置了 evaluation_strategy，模型会在训练过程中定期进行评估，并输出损失和其他指标（如准确率）。

如果需要计算更具体的指标（如准确率和 F1 分数），你可以定义一个 compute_metrics 函数，它会在评估时使用：
```py
import numpy as np
import evaluate

def compute_metrics(eval_preds):
    metric = evaluate.load("glue", "mrpc")  # 加载MRPC数据集的评估指标
    logits, labels = eval_preds
    predictions = np.argmax(logits, axis=-1)  # 获取预测结果
    return metric.compute(predictions=predictions, references=labels)
```
然后在 Trainer 中传递给 compute_metrics 参数：
```py
trainer = Trainer(
    model,
    training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,  # 传入自定义评估函数
)
```
### 6. 训练的输出

训练过程中，你将获得以下内容：

训练损失：表示模型在训练集上的表现。

验证损失和指标：评估模型在验证集上的表现（通过 compute_metrics 函数计算）。
```py
# 输出的日志包括训练损失和评估指标
trainer.train()  # 开始训练
```
### 7. 保存模型
训练完成后，你可以使用 trainer.save_model() 保存微调后的模型，以便以后使用或推理
```py
trainer.save_model("path_to_save_model")  # 保存微调后的模型
```
```py
#完整的微调代码
from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments, DataCollatorWithPadding
import evaluate
import numpy as np

# 定义 training_args
training_args = TrainingArguments(
    "test-trainer", 
    evaluation_strategy="epoch",  
    learning_rate=5e-5, 
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    num_train_epochs=3,
    weight_decay=0.01
)

# 加载预训练模型
model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=2)

# 数据加载和 tokenization (tokenized_datasets 是你处理过的数据)
data_collator = DataCollatorWithPadding(tokenizer)

# 定义 compute_metrics 函数
def compute_metrics(eval_preds):
    metric = evaluate.load("glue", "mrpc")
    logits, labels = eval_preds
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

# 初始化 Trainer
trainer = Trainer(
    model,
    training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
    data_collator=data_collator
)

# 开始训练
trainer.train()
```