# Schema设计指南

## 🎯 设计理念

新的Schema系统采用**配置驱动**的设计理念：
- **单一数据源**: 所有Schema定义都在 `ontology/schema_config.yaml`
- **自动集成**: LLM Prompt自动从Schema生成
- **易于维护**: 修改Schema只需编辑一个YAML文件
- **版本管理**: 内置版本控制和变更追踪

## 📝 如何设计你的Schema

### 1. 复制并修改配置文件

```bash
# 复制现有配置作为模板
cp ontology/schema_config.yaml ontology/my_domain_schema.yaml
```

### 2. 修改元数据

```yaml
metadata:
  name: "你的领域知识图谱本体"
  version: "1.0.0"
  description: "描述你的领域"
  author: "你的名字"
```

### 3. 定义实体类型

```yaml
entity_types:
  YourEntityType:
    description: "实体类型的详细描述"
    examples: ["示例1", "示例2", "示例3"]  # 帮助LLM理解
    keywords: ["关键词1", "关键词2"]        # 用于自动识别
    patterns: ["正则表达式模式"]            # 更精确的识别
    aliases: ["别名1", "别名2"]            # 支持多语言
    color: "#FF6B6B"                     # 可视化颜色
```

### 4. 定义关系类型

```yaml
relation_types:
  your_relation:
    description: "关系的详细描述"
    examples: ["(实体1, your_relation, 实体2)"]
    subject_types: ["允许的主语类型"]
    object_types: ["允许的宾语类型"]
    aliases: ["关系别名"]
    is_symmetric: false                   # 是否对称
    inverse_relation: "反向关系名"         # 可选
```

### 5. 自定义LLM Prompt

```yaml
llm_prompts:
  extraction_system_prompt: |
    你的自定义系统提示词...
    {entity_types_description}  # 自动填充实体类型
    {relation_types_description}  # 自动填充关系类型
```

## 🚀 使用新Schema

### 1. 加载自定义Schema

```python
from ontology.dynamic_schema import DynamicOntologyManager

# 使用自定义Schema
ontology = DynamicOntologyManager("ontology/my_domain_schema.yaml")
```

### 2. 生成文档

```python
# 自动生成Schema参考文档
ontology.export_schema_documentation("docs/MY_SCHEMA_REFERENCE.md")
```

### 3. 测试Schema

```python
# 测试实体识别
entity_type = ontology._identify_entity_type("your_test_entity")
print(f"识别结果: {entity_type}")

# 测试三元组验证
validation = ontology.validate_triple("subject", "predicate", "object")
print(f"验证结果: {validation}")

# 获取LLM Prompt
prompts = ontology.get_llm_extraction_prompt("测试文本")
print(f"系统提示: {prompts['system']}")
```

## 💡 设计最佳实践

### 1. 实体类型设计
- **层次清晰**: 从抽象到具体
- **互斥完备**: 类型之间不重叠，覆盖完整
- **示例丰富**: 提供足够的示例帮助LLM理解

### 2. 关系类型设计
- **语义明确**: 关系含义清晰无歧义
- **约束合理**: 主语宾语类型约束要合理
- **对称性**: 正确设置对称关系和反向关系

### 3. 关键词和模式
- **关键词**: 常见的标识词汇
- **正则模式**: 精确的命名模式
- **别名**: 支持中英文和同义词

### 4. LLM Prompt优化
- **清晰指令**: 明确告诉LLM要做什么
- **示例驱动**: 提供好的示例
- **约束明确**: 说明Schema约束

## 🔧 调试和优化

### 1. 验证Schema完整性

```python
# 检查Schema加载
ontology = DynamicOntologyManager("your_schema.yaml")
summary = ontology.get_ontology_summary()
print(json.dumps(summary, indent=2, ensure_ascii=False))
```

### 2. 测试识别效果

```python
# 测试实体识别
test_entities = ["entity1", "entity2", "entity3"]
for entity in test_entities:
    entity_type = ontology._identify_entity_type(entity)
    print(f"{entity} -> {entity_type}")
```

### 3. 验证三元组

```python
# 测试三元组验证
test_triples = [
    ("subject1", "relation1", "object1"),
    ("subject2", "relation2", "object2")
]

for s, p, o in test_triples:
    validation = ontology.validate_triple(s, p, o)
    if not validation["valid"]:
        print(f"❌ {(s, p, o)}: {validation['issues']}")
        print(f"💡 建议: {validation['suggestions']}")
```

## 📊 Schema演进

### 版本管理
- 每次重大修改都要更新版本号
- 在 `metadata.description` 中记录变更说明
- 保留旧版本文件作为备份

### 动态扩展
- 系统会自动发现新的实体和关系类型
- 定期检查 `processing_stats` 中的待处理项
- 手动将有价值的新类型添加到Schema中

这样的设计让Schema管理变得简单而强大！🎉