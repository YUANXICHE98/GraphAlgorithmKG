# Training 目录说明

## 📁 目录结构

```
training/
├── data/                       # 训练数据
│   ├── raw/                   # 从results/sessions收集的原始数据
│   ├── processed/             # 预处理后的训练数据
│   └── splits/                # 训练/验证/测试数据分割
├── models/                     # 训练好的模型
│   ├── schema_classifier/     # Schema分类模型
│   ├── entity_inferer/        # 实体推断模型
│   ├── relation_extractor/    # 关系抽取模型
│   └── entity_merger/         # 实体合并模型
├── experiments/                # 实验记录
│   ├── logs/                  # 训练日志
│   ├── checkpoints/           # 模型检查点
│   └── metrics/               # 训练指标和评估结果
├── configs/                    # 训练配置文件
└── scripts/                    # 训练脚本和工具
```

## 🎯 数据流

### 1. 数据收集
```
results/sessions/ → training/data/raw/
```
- 从完成的处理会话中收集训练样本
- 按模型类型分类存储

### 2. 数据预处理
```
training/data/raw/ → training/data/processed/
```
- 清洗和标准化数据
- 特征工程
- 质量过滤

### 3. 数据分割
```
training/data/processed/ → training/data/splits/
```
- 训练集 (70%)
- 验证集 (20%)
- 测试集 (10%)

### 4. 模型训练
```
training/data/splits/ → training/models/
```
- 使用配置文件中的超参数
- 保存最佳模型和检查点

## 🚀 使用方法

### 收集训练数据
```python
from training.base_trainer import training_data_manager

# 收集Schema分类数据
schema_data = training_data_manager.collect_schema_training_data()

# 收集实体推断数据
entity_data = training_data_manager.collect_entity_training_data()
```

### 训练模型
```python
from training.schema_classifier_trainer import train_schema_classifier
from training.entity_inferer_trainer import train_entity_inferer

# 训练Schema分类器
result = train_schema_classifier()

# 训练实体推断器
result = train_entity_inferer()
```

### 使用训练好的模型
```python
# 加载模型
from training.schema_classifier_trainer import SchemaClassifierTrainer

trainer = SchemaClassifierTrainer(config)
trainer.load_model("training/models/schema_classifier/latest.pkl")

# 预测
result = trainer.predict_schema("文档内容")
```

## 📊 模型性能跟踪

### 指标记录
- 训练/验证准确率
- 损失函数值
- 特征重要性
- 混淆矩阵

### 实验管理
- 每次训练自动记录超参数
- 模型版本控制
- 性能对比分析

## 🔧 配置文件

### default_config.json
- 所有模型的默认超参数
- 训练流程配置
- 输出路径设置

### data_collection_config.json
- 数据收集规则
- 质量过滤条件
- 数据分割比例

## 📈 持续改进

### 数据增强
- 定期从新的会话中收集数据
- 主动学习策略
- 困难样本挖掘

### 模型优化
- 超参数调优
- 特征工程改进
- 模型架构升级

### 评估和监控
- 定期评估模型性能
- 生产环境监控
- A/B测试对比
