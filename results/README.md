# Results 目录结构说明

## 📁 目录结构

```
results/
├── sessions/           # 处理会话记录
│   ├── YYYYMMDD_HHMMSS/   # 按时间戳命名的会话目录
│   │   ├── 01_document_input.json      # 文档输入
│   │   ├── 02_schema_detection.json    # Schema检测结果
│   │   ├── 03_triple_extraction.json   # 三元组抽取结果
│   │   ├── 04_entity_inference.json    # 实体推断结果
│   │   ├── 05_final_kg.json           # 最终知识图谱
│   │   └── session_metadata.json      # 会话元数据
│   └── latest -> YYYYMMDD_HHMMSS/     # 指向最新会话的软链接
├── outputs/            # 最终输出文件
│   ├── knowledge_graphs/   # 知识图谱JSON文件
│   ├── analysis/          # 分析报告
│   └── exports/           # 各种格式的导出文件
│       ├── *.csv          # CSV格式
│       ├── *.json         # JSON格式
│       ├── *.gexf         # Gephi格式
│       ├── *.graphml      # GraphML格式
│       └── visualizations/ # 可视化文件
├── cache/              # 缓存数据
│   ├── entities/       # 实体推断缓存
│   └── schemas/        # Schema检测缓存
└── backups/            # 历史备份文件
    └── *.pkl           # 序列化备份
```

## 📋 文件说明

### 会话文件 (sessions/)
- 每个会话包含完整的处理流程记录
- 文件按处理顺序编号 (01, 02, 03...)
- 可以追溯任何阶段的中间结果

### 输出文件 (outputs/)
- `knowledge_graphs/`: 最终的知识图谱JSON文件
- `analysis/`: 处理分析和统计报告
- `exports/`: 各种格式的导出文件，便于其他工具使用

### 缓存文件 (cache/)
- 提高重复处理的效率
- 实体推断和Schema检测的缓存结果

### 备份文件 (backups/)
- 历史版本的序列化备份
- 用于恢复和版本对比
