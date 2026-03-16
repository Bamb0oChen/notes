# Jupyter 示例：情感分类（Transformer）

> 说明：Docsify 站点默认渲染 `.md`，不会直接渲染 `.ipynb`。  
> 本仓库已移除对应的 Notebook 文件（`AI/test.ipynb`），仅保留本页的代码示例。

## 代码

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# 使用预训练的模型
checkpoint = "distilbert-base-uncased-finetuned-sst-2-english"

# 加载 tokenizer 和 model
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForSequenceClassification.from_pretrained(checkpoint)

# 示例输入句子
raw_inputs = [
    "I love this course! It's amazing.",
    "This is the worst experience ever, I hate it!"
]

# 预处理文本，返回 PyTorch 张量
inputs = tokenizer(raw_inputs, padding=True, truncation=True, return_tensors="pt")
print(inputs)

# 获取模型的输出
outputs = model(**inputs)
logits = outputs.logits
print(logits)

# 使用 Softmax 计算概率
predictions = torch.nn.functional.softmax(logits, dim=-1)
print(predictions)

# 获取标签映射
print(model.config.id2label)

# 输出情感预测结果
for i, sentence in enumerate(raw_inputs):
    label = torch.argmax(predictions[i]).item()
    print(f"Sentence: {sentence}")
    print(f"Prediction: {model.config.id2label[label]}")
    print(f"Positive probability: {predictions[i][1]:.4f}, Negative probability: {predictions[i][0]:.4f}")
    print("---")
```

## 在本地运行（Jupyter）

- Notebook 文件：已移除（如需可自行新建 `.ipynb` 并复制本页代码）
- 网页展示页：`AI/test.md`
