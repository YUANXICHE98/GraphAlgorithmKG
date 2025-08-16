# Schema边界和输出规范

## 🎯 核心原则
**输入混乱，输出规范** - 无论输入文档多么混乱，输出必须严格符合对应Schema

## 📋 Schema分类边界

### 1. 通用知识图谱 (general)
- **适用场景**: 企业架构、系统框架、算法模型
- **核心实体**: Framework, Algorithm, Paradigm, Task, Technique
- **核心关系**: is_instance_of, implements, uses_paradigm, has_algorithm
- **输出要求**: 所有实体必须是架构或技术概念

### 2. 时空知识图谱 (spatiotemporal)  
- **适用场景**: 时空事件、DO-DA-F结构、水利系统
- **核心实体**: TemporalEntity, SpatialEntity, Event, Action, Condition, Outcome
- **核心关系**: hasStartTime, locatedAt, hasCondition, resultsIn
- **输出要求**: 必须包含时间或空间维度

### 3. 混合类型 (mixed)
- **适用场景**: 无法明确分类或包含多种Schema元素
- **处理方式**: 人工审核后重新分类
- **输出要求**: 标注混合原因和建议分类

## 🔧 质量控制检查点

### 检查点1: Schema一致性
- [ ] 所有实体类型在Schema中定义
- [ ] 所有关系类型在Schema中定义  
- [ ] 实体-关系组合符合Schema约束

### 检查点2: 语义正确性
- [ ] 实体名称语义合理
- [ ] 关系方向正确
- [ ] 三元组逻辑一致

### 检查点3: 完整性
- [ ] 重要概念未遗漏
- [ ] 关系网络连通
- [ ] 元数据完整

## 📁 文件命名规范

```
{session_id}_{schema_type}_{file_type}.{ext}

示例:
- 20250816_110515_general_knowledge_graph.json
- 20250816_110516_spatiotemporal_analysis.json
- 20250816_110517_mixed_export.csv
```

## 🚨 边界违规处理

1. **实体类型不匹配**: 自动重新推断或标记为Unknown
2. **关系类型不存在**: 映射到最相近的合法关系或丢弃
3. **Schema混合**: 自动分类到mixed类别，等待人工审核

## 📊 质量指标

- **Schema一致性**: 100% (强制要求)
- **实体推断准确率**: >80%
- **关系抽取准确率**: >75%
- **处理速度**: <5s/文档
