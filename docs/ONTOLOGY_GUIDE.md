# 多领域知识图谱本体指南

本指南介绍系统支持的多种本体Schema及其使用方法。

## 支持的本体类型

### 1. 通用知识图谱本体
- **文件**: `ontology/schemas/general/schema_config.yaml`
- **领域**: 通用架构和框架概念
- **主要实体**: Algorithm, Framework, Task, Paradigm, Technique, Metric
- **应用场景**: 企业架构、系统框架、通用概念建模
- **测试准确率**: 88.9%

#### 实体类别
| 类别 | 说明 | 示例 |
|------|------|------|
| Paradigm | 解决问题的通用范式或决策框架 | Sequential_Decision, System_Architect, Operational_Planner |
| Algorithm | 具体算法或算法家族 | MINERVA, OV-1, SV-1, TV-1, Path_Ranking_Algorithm |
| Technique | 面向效率/性能的手段 | Pruning, Random_Walk, Approximate_Computing |
| Framework | 结合多种组件的体系/方法论 | DoDAF, Enterprise_Architecture, Operational_View, System_View |
| Task | 研究/应用任务 | Graph_Sparse_Reasoning, Relation_Prediction, Node_Classification |
| Metric | 衡量效果的指标 | Relation_Confidence, Compute_Reduction, Accuracy_Retention |

### 2. 时空本体
- **文件**: `ontology/schemas/spatiotemporal/spatiotemporal_schema.yaml`
- **领域**: 时空概念和DO-DA-F结构
- **主要实体**: TemporalEntity, SpatialEntity, Event, Action, Condition, Outcome
- **应用场景**: 水利系统、时空事件建模、DO-DA-F架构
- **测试准确率**: 85.7% (时空) / 66.7% (DO-DA-F)

#### 实体类别
| 类别 | 说明 | 示例 |
|------|------|------|
| TemporalEntity | 时间实体，表示时间点、时间段 | 2024-10-23 08:00, 4小时, 2024年夏季 |
| SpatialEntity | 空间实体，表示地理位置、空间区域 | 长江流域, 河流, 监测站 |
| Event | 事件实体，具有时空属性的动态过程 | 洪水事件, 降水过程, 监测事件 |
| Action | 动作实体，表示系统中的行为或操作（DO） | checkTemperature, monitorWaterLevel, executeFloodWarning |
| Condition | 条件实体，表示系统运行的前提条件（DA） | temperature > 30, sensor_status == normal |
| Outcome | 结果实体，表示动作执行后的结果（F） | turnOnAirConditioner, generateWaterLevelReport |
| MonitoringData | 监测数据实体 | 水位测量值, 降水量, 温度值 |
| MonitoringStation | 监测站实体 | 水文站, 气象站, 监测点 |

## 关系类型

### 1. 核心结构关系

| 关系 | 语义 | 主语类型 | 宾语类型 | 示例 |
|------|------|----------|----------|------|
| is_instance_of | 实例关系 | 任意 | Paradigm/Algorithm/Technique/Framework/Task/Metric | (MINERVA, is_instance_of, Algorithm) |
| has_algorithm | 任务拥有算法 | Task | Algorithm | (Graph_Sparse_Reasoning, has_algorithm, MINERVA) |
| implements | 技术实现算法 | Technique | Algorithm | (Pruning, implements, MINERVA) |
| implemented_by | 算法被技术实现 | Algorithm | Technique | (MINERVA, implemented_by, Pruning) |
| uses_paradigm | 使用范式 | Algorithm/Technique | Paradigm | (MINERVA, uses_paradigm, Sequential_Decision) |
| builds_on | 基于关系 | Framework/Technique/Algorithm | Framework/Technique/Algorithm | (GNN_RL, builds_on, Graph_Reinforcement_Learning) |

### 2. 性能与应用关系

| 关系 | 语义 | 主语类型 | 宾语类型 | 示例 |
|------|------|----------|----------|------|
| reduces_computation_by | 降低计算量（百分比） | Technique/Algorithm | Metric | (RL_Agent_Pruning_Strategy, reduces_computation_by, 90%) |
| maintains_accuracy | 保持准确性 | Technique/Algorithm | Metric | (RL_Agent_Pruning_Strategy, maintains_accuracy, 98%) |
| used_in | 应用场景 | Algorithm/Technique | Task | (Path_Ranking_Algorithm, used_in, Relation_Prediction) |
| calculates | 计算关系 | Algorithm | Metric | (PRA, calculates, Relation_Confidence) |
| explains | 解释关系 | Algorithm/Technique | 任意 | (Attention_Weights, explains, Decision_Path) |

### 3. 特征描述关系

| 关系 | 语义 | 主语类型 | 宾语类型 | 示例 |
|------|------|----------|----------|------|
| has_advantage | 具有优势 | Algorithm/Technique/Framework | 文本值 | (Path_Ranking_Algorithm, has_advantage, High_Explainability) |
| has_challenge | 面临挑战 | Algorithm/Technique/Framework | 文本值 | (Monte_Carlo_Tree_Search, has_challenge, High_Compute_Cost) |

### 4. 布尔属性关系

| 关系 | 语义 | 主语类型 | 宾语类型 | 示例 |
|------|------|----------|----------|------|
| is_graph_RL | 是否为图强化学习方法 | Algorithm/Technique | Boolean | (MINERVA, is_graph_RL, True) |
| is_sequential_decision | 是否涉及序贯决策 | Algorithm/Technique/Paradigm | Boolean | (Path_Ranking_Algorithm, is_sequential_decision, True) |
| uses_heuristic | 是否使用启发式方法 | Algorithm/Technique | Boolean | (Monte_Carlo_Tree_Search, uses_heuristic, True) |

## 本体更新特性

### 动态扩展机制
- **实体类型阈值**: 当新实体类型出现次数 ≥ 5 时自动添加
- **关系类型阈值**: 当新关系类型出现次数 ≥ 3 时自动添加
- **更新频率**: 每处理 100 个三元组检查一次
- **版本管理**: 每次更新自动递增版本号并记录变更

### 智能识别算法
- **关键词匹配**: 基于预定义关键词识别类型
- **模式匹配**: 使用正则表达式识别命名模式
- **别名支持**: 支持中英文别名映射
- **置信度评分**: 为映射结果提供置信度评估

### 配置持久化
- **JSON配置文件**: 本体配置存储在 `ontology/config/` 目录
- **版本历史**: 完整的版本变更记录
- **扩展配置**: 可调节的阈值和更新参数
- **增量更新**: 支持增量式本体扩展

## 使用示例

```python
# 创建动态本体管理器
from ontology.dynamic_schema import DynamicOntologyManager

ontology = DynamicOntologyManager()

# 处理三元组数据
result = ontology.process_triples([
    ("MINERVA", "is_instance_of", "Algorithm"),
    ("MINERVA", "uses_paradigm", "Sequential_Decision"),
    ("MINERVA", "is_graph_RL", "True")
])

# 查询本体信息
print(f"当前版本: {ontology.current_version}")
print(f"实体类型数量: {len(ontology.entity_types)}")
print(f"关系类型数量: {len(ontology.relation_types)}")
```

此更新版本完全支持88个三元组的处理，并具备自动学习和扩展能力。 