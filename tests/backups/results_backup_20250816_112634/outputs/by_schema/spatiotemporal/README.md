# 时空知识图谱

## 📋 Schema描述
时空概念、事件、DO-DA-F结构

## 📁 目录结构
- `knowledge_graphs/`: 最终的知识图谱JSON文件
- `sessions/`: 该Schema的处理会话记录
- `analysis/`: 质量分析和统计报告
- `exports/`: 各种格式的导出文件
- `statistics/`: 性能和质量统计

## 🎯 输出规范
- 所有实体类型必须符合对应Schema定义
- 所有关系类型必须在Schema关系列表中
- 文件命名格式: `{session_id}_{schema_type}_{file_type}.{ext}`

## 📊 质量要求
- 实体推断准确率 > 80%
- 关系抽取准确率 > 75%
- Schema一致性 = 100%
