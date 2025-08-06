# Neo4j集成设置指南（更新版）

## 🚀 快速开始

### 1. 确保Neo4j数据库运行
- Neo4j地址: `localhost:7474`
- 用户名: `neo4j`  
- 密码: `yuanxi98` ⚠️ **已从yuanxi更新为yuanxi98**

### 2. 安装Neo4j驱动
```bash
# 在你的TKG conda环境中运行
conda activate TKG
pip install neo4j>=5.0.0
```

### 3. 测试连接
```bash
python test_neo4j_operations.py
```

## 📊 主要操作

### 📤 导出Neo4j数据库内容
```bash
# 导出当前数据库到文件
python dynamic_main.py --export-from-neo4j

# 导出到指定目录
python dynamic_main.py --export-from-neo4j --neo4j-export-dir my_backup
```

### 📥 导入数据到Neo4j
```bash
# 从dynamic_kg_storage导入到Neo4j
python dynamic_main.py --import-to-neo4j

# 清空现有数据并导入
python dynamic_main.py --import-to-neo4j --neo4j-clear

# 指定storage路径
python dynamic_main.py --import-to-neo4j --storage-path my_storage
```

### 🔄 完整数据迁移流程
```bash
# 1. 备份现有数据库
python dynamic_main.py --export-from-neo4j --neo4j-export-dir backup_$(date +%Y%m%d)

# 2. 处理新的三元组数据
python dynamic_main.py data/graph_algorithm_triples.csv

# 3. 将处理好的数据导入Neo4j
python dynamic_main.py --import-to-neo4j --neo4j-clear
```

## 🔍 Neo4j浏览和查询

### 浏览器访问
- 打开浏览器访问: http://localhost:7474
- 使用用户名 `neo4j` 和密码 `yuanxi98` 登录

### 常用Cypher查询

#### 1. 查看所有实体类型
```cypher
MATCH (n:Entity) 
RETURN n.type as entity_type, count(n) as count 
ORDER BY count DESC
```

#### 2. 查看所有算法实体
```cypher
MATCH (n:Entity) 
WHERE n.type = 'Algorithm' 
RETURN n.name, n.description
```

#### 3. 查看MINERVA的所有关系
```cypher
MATCH (e:Entity {name: 'MINERVA'})-[r:RELATED]-(other:Entity)
RETURN e.name, r.type, other.name, r.confidence
```

#### 4. 查找使用Sequential_Decision范式的所有算法
```cypher
MATCH (paradigm:Entity {name: 'Sequential_Decision'})<-[r:RELATED {type: 'uses_paradigm'}]-(algorithm:Entity)
RETURN algorithm.name, algorithm.type, r.confidence
```

#### 5. 按置信度查询高质量关系
```cypher
MATCH ()-[r:RELATED]->() 
WHERE r.confidence >= 0.8
RETURN r.type, avg(r.confidence) as avg_confidence, count(*) as count
ORDER BY count DESC
```

#### 6. 可视化子图（以MINERVA为中心）
```cypher
MATCH (center:Entity {name: 'MINERVA'})-[r:RELATED*1..2]-(connected:Entity)
RETURN center, r, connected
LIMIT 50
```

## 📊 数据结构

### 实体节点 (Entity)
- `name`: 实体名称
- `type`: 实体类型 (Algorithm, Paradigm, Technique, Framework, Task, Metric, Boolean)
- `description`: 描述
- `confidence`: 置信度
- `created_at`: 创建时间
- `attributes`: JSON格式的额外属性

### 关系边 (RELATED)
- `type`: 关系类型 (uses_paradigm, implements, builds_on, 等)
- `confidence`: 置信度
- `source`: 数据来源

### 字面值属性
字面值（如百分比、布尔值）作为实体的直接属性存储：
- `is_graph_RL`: "True"/"False"
- `reduces_computation_by`: "90%"
- `maintains_accuracy`: "98%"

## 📁 导出文件格式

导出操作会生成以下文件：

```
neo4j_export/
├── entities.json          # JSON格式实体数据
├── relations.json         # JSON格式关系数据
├── entities.csv          # CSV格式实体数据
├── relations.csv         # CSV格式关系数据
└── triples.csv           # 三元组格式（与原始数据兼容）
```

### triples.csv 示例：
```csv
subject,predicate,object,confidence,source
MINERVA,is_instance_of,Algorithm,1.0,manual
MINERVA,uses_paradigm,Sequential_Decision,0.9,mapped
MINERVA,is_graph_RL,True,1.0,literal_property
```

## 🛠️ 高级功能

### 1. Python API使用
```python
from pipeline.neo4j_connector import Neo4jConnector, export_neo4j_to_files, import_storage_to_neo4j

# 连接测试
connector = Neo4jConnector(password="yuanxi98")
if connector.connect():
    stats = connector.get_graph_statistics()
    print(f"数据库统计: {stats}")
    connector.disconnect()

# 便捷导出
export_neo4j_to_files("my_export", password="yuanxi98")

# 便捷导入
import_storage_to_neo4j("dynamic_kg_storage", password="yuanxi98", clear_existing=True)
```

### 2. 批量操作
```python
from dynamic_main import DynamicKnowledgeGraphBuilder

builder = DynamicKnowledgeGraphBuilder()

# 导出storage到Neo4j
builder.import_storage_to_neo4j(password="yuanxi98", clear_existing=True)
```

### 3. 数据验证查询
```cypher
// 检查数据完整性
MATCH (n:Entity) 
WHERE n.name IS NULL OR n.type IS NULL
RETURN count(n) as invalid_entities

// 检查孤立节点
MATCH (n:Entity)
WHERE NOT (n)-[:RELATED]-()
RETURN n.name, n.type

// 统计置信度分布
MATCH ()-[r:RELATED]->()
RETURN 
  CASE 
    WHEN r.confidence >= 0.9 THEN 'High (0.9+)'
    WHEN r.confidence >= 0.7 THEN 'Medium (0.7-0.9)'
    ELSE 'Low (<0.7)'
  END as confidence_range,
  count(*) as count
```

## 🚨 注意事项

1. **密码变更**: 密码已从 `yuanxi` 更新为 `yuanxi98`
2. **数据备份**: 使用 `--neo4j-clear` 会删除Neo4j中的所有现有数据，务必先备份
3. **性能考虑**: 大量数据导入可能需要一些时间
4. **数据格式**: 导出的数据与dynamic_kg_storage格式完全兼容
5. **连接稳定性**: 确保Neo4j服务稳定运行，避免导入过程中断

## 🔗 相关链接

- [Neo4j Desktop](https://neo4j.com/download/)
- [Cypher查询语言](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Python驱动文档](https://neo4j.com/docs/api/python-driver/current/) 