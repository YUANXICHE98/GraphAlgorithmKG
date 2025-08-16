#!/usr/bin/env python3
"""
按Schema重新组织输出结构
确保输入混乱，输出规范，边界清晰
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

def reorganize_by_schema():
    """按Schema重新组织输出结构"""
    
    print("🎯 按Schema重新组织输出结构")
    print("📋 目标: 输入混乱，输出规范，边界清晰")
    print("=" * 80)
    
    results_path = Path("results")
    
    # 1. 新的Schema分类结构
    schema_structure = {
        "general": {
            "name": "通用知识图谱",
            "schema_files": ["schema_config.yaml", "../schema_config.yaml"],
            "description": "企业架构、框架、算法等通用概念"
        },
        "spatiotemporal": {
            "name": "时空知识图谱", 
            "schema_files": ["spatiotemporal_schema.yaml"],
            "description": "时空概念、事件、DO-DA-F结构"
        },
        "mixed": {
            "name": "混合类型",
            "schema_files": [],
            "description": "无法明确分类或多Schema混合的结果"
        }
    }
    
    print("📁 创建按Schema分类的目录结构:")
    
    # 创建新的目录结构
    for schema_key, schema_info in schema_structure.items():
        schema_dir = results_path / "outputs" / "by_schema" / schema_key
        
        # 创建子目录
        subdirs = [
            "knowledge_graphs",  # 最终KG文件
            "sessions",         # 该Schema的会话记录
            "analysis",         # 分析报告
            "exports",          # 导出文件
            "statistics"        # 统计信息
        ]
        
        for subdir in subdirs:
            (schema_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        print(f"   ✅ {schema_key}: {schema_info['name']}")
        print(f"      📝 {schema_info['description']}")
        
        # 创建Schema说明文件
        schema_readme = schema_dir / "README.md"
        readme_content = f"""# {schema_info['name']}

## 📋 Schema描述
{schema_info['description']}

## 📁 目录结构
- `knowledge_graphs/`: 最终的知识图谱JSON文件
- `sessions/`: 该Schema的处理会话记录
- `analysis/`: 质量分析和统计报告
- `exports/`: 各种格式的导出文件
- `statistics/`: 性能和质量统计

## 🎯 输出规范
- 所有实体类型必须符合对应Schema定义
- 所有关系类型必须在Schema关系列表中
- 文件命名格式: `{{session_id}}_{{schema_type}}_{{file_type}}.{{ext}}`

## 📊 质量要求
- 实体推断准确率 > 80%
- 关系抽取准确率 > 75%
- Schema一致性 = 100%
"""
        
        with open(schema_readme, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    # 2. 分析现有文件并重新分类
    print(f"\n📦 分析和重新分类现有文件:")
    
    # 分析知识图谱文件
    kg_path = results_path / "outputs" / "knowledge_graphs"
    if kg_path.exists():
        kg_files = list(kg_path.glob("*.json"))
        
        for kg_file in kg_files:
            try:
                with open(kg_file, 'r', encoding='utf-8') as f:
                    kg_data = json.load(f)
                
                # 根据metadata中的schema判断分类
                schema_used = kg_data.get('metadata', {}).get('schema', '')
                schema_category = classify_schema(schema_used)
                
                # 生成新的文件名
                session_id = extract_session_id(kg_file.name)
                new_filename = f"{session_id}_{schema_category}_knowledge_graph.json"
                
                # 移动到对应目录
                target_dir = results_path / "outputs" / "by_schema" / schema_category / "knowledge_graphs"
                target_file = target_dir / new_filename
                
                shutil.copy2(kg_file, target_file)
                print(f"   📄 {kg_file.name} -> {schema_category}/{new_filename}")
                
            except Exception as e:
                print(f"   ❌ 处理文件失败 {kg_file.name}: {e}")
    
    # 分析会话文件
    sessions_path = results_path / "sessions"
    if sessions_path.exists():
        for session_dir in sessions_path.iterdir():
            if session_dir.is_dir() and session_dir.name != "latest":
                try:
                    # 读取会话元数据
                    metadata_file = session_dir / "session_metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                        
                        schema_used = session_data.get('schema_used', '')
                        schema_category = classify_schema(schema_used)
                        
                        # 复制整个会话目录
                        target_session_dir = results_path / "outputs" / "by_schema" / schema_category / "sessions" / session_dir.name
                        
                        if not target_session_dir.exists():
                            shutil.copytree(session_dir, target_session_dir)
                            print(f"   📁 会话 {session_dir.name} -> {schema_category}/sessions/")
                
                except Exception as e:
                    print(f"   ❌ 处理会话失败 {session_dir.name}: {e}")
    
    # 3. 生成分类统计报告
    print(f"\n📊 生成分类统计报告:")
    
    classification_stats = {}
    
    for schema_key, schema_info in schema_structure.items():
        schema_dir = results_path / "outputs" / "by_schema" / schema_key
        
        # 统计各类文件数量
        kg_count = len(list((schema_dir / "knowledge_graphs").glob("*.json")))
        session_count = len(list((schema_dir / "sessions").iterdir()))
        
        classification_stats[schema_key] = {
            "name": schema_info["name"],
            "knowledge_graphs": kg_count,
            "sessions": session_count,
            "description": schema_info["description"]
        }
        
        print(f"   📋 {schema_info['name']}: {kg_count} 个KG, {session_count} 个会话")
    
    # 保存统计报告
    stats_file = results_path / "outputs" / "schema_classification_report.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump({
            "classification_time": datetime.now().isoformat(),
            "total_schemas": len(schema_structure),
            "statistics": classification_stats,
            "file_naming_convention": {
                "knowledge_graphs": "{session_id}_{schema_type}_knowledge_graph.json",
                "analysis": "{session_id}_{schema_type}_analysis.json",
                "exports": "{session_id}_{schema_type}_{format}.{ext}"
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 统计报告保存到: {stats_file}")
    
    # 4. 创建边界说明文档
    boundary_doc = results_path / "SCHEMA_BOUNDARIES.md"
    boundary_content = """# Schema边界和输出规范

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
"""
    
    with open(boundary_doc, 'w', encoding='utf-8') as f:
        f.write(boundary_content)
    
    print(f"   📝 边界说明文档: {boundary_doc}")
    
    print(f"\n✅ Schema分类重组完成!")
    return classification_stats

def classify_schema(schema_path: str) -> str:
    """根据schema路径分类"""
    if not schema_path:
        return "mixed"
    
    schema_path_lower = schema_path.lower()
    
    if "schema_config" in schema_path_lower or "general" in schema_path_lower:
        return "general"
    elif "spatiotemporal" in schema_path_lower or "spatial" in schema_path_lower:
        return "spatiotemporal"
    else:
        return "mixed"

def extract_session_id(filename: str) -> str:
    """从文件名提取会话ID"""
    # 尝试提取时间戳格式的会话ID
    parts = filename.split('_')
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{parts[0]}_{parts[1]}"
    
    # 如果没有找到，使用文件名前缀
    return filename.split('.')[0]

if __name__ == "__main__":
    reorganize_by_schema()
