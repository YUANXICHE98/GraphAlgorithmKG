#!/usr/bin/env python3
"""
重新整理results文件结构
创建清晰、有序的文件组织
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def reorganize_results():
    """重新整理results目录结构"""
    
    print("🧹 开始重新整理results文件结构")
    print("=" * 60)
    
    results_path = Path("results")
    
    # 1. 创建新的清晰结构
    new_structure = {
        "sessions": "处理会话的完整记录",
        "outputs": {
            "knowledge_graphs": "最终的知识图谱文件",
            "analysis": "分析报告",
            "exports": "导出的各种格式文件"
        },
        "cache": {
            "entities": "实体推断缓存",
            "schemas": "Schema检测缓存"
        },
        "backups": "历史备份文件"
    }
    
    print("📁 创建新的目录结构:")
    
    # 创建目录
    for key, value in new_structure.items():
        if isinstance(value, dict):
            for subkey, subdesc in value.items():
                dir_path = results_path / key / subkey
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ {key}/{subkey}: {subdesc}")
        else:
            dir_path = results_path / key
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {key}: {value}")
    
    # 2. 移动和整理现有文件
    print(f"\n📦 整理现有文件:")
    
    # 移动current目录下的文件到exports
    current_path = results_path / "current"
    if current_path.exists():
        exports_path = results_path / "outputs" / "exports"
        
        # 移动各种格式的导出文件
        export_files = [
            "entities.csv", "entities.json",
            "relations.csv", "relations.json", 
            "edges.txt", "statistics.json",
            "knowledge_graph.gexf", "knowledge_graph.graphml"
        ]
        
        for file_name in export_files:
            src_file = current_path / file_name
            if src_file.exists():
                dst_file = exports_path / file_name
                shutil.move(str(src_file), str(dst_file))
                print(f"   📄 移动: {file_name} -> outputs/exports/")
        
        # 移动备份文件
        backups_src = current_path / "backups"
        backups_dst = results_path / "backups"
        if backups_src.exists():
            if backups_dst.exists():
                # 合并备份文件
                for backup_file in backups_src.glob("*.pkl"):
                    dst_file = backups_dst / backup_file.name
                    if not dst_file.exists():
                        shutil.move(str(backup_file), str(dst_file))
                        print(f"   💾 移动备份: {backup_file.name}")
                shutil.rmtree(backups_src)
            else:
                shutil.move(str(backups_src), str(backups_dst))
                print(f"   💾 移动整个备份目录")
        
        # 移动可视化文件
        viz_src = current_path / "visualizations"
        viz_dst = exports_path / "visualizations"
        if viz_src.exists():
            shutil.move(str(viz_src), str(viz_dst))
            print(f"   🎨 移动可视化文件")
        
        # 删除空的current目录
        if current_path.exists() and not any(current_path.iterdir()):
            current_path.rmdir()
            print(f"   🗑️ 删除空的current目录")
    
    # 3. 清理空的会话目录
    sessions_path = results_path / "sessions"
    if sessions_path.exists():
        empty_sessions = []
        valid_sessions = []
        
        for session_dir in sessions_path.iterdir():
            if session_dir.is_dir() and session_dir.name != "latest":
                if not any(session_dir.iterdir()):
                    empty_sessions.append(session_dir.name)
                    session_dir.rmdir()
                else:
                    valid_sessions.append(session_dir.name)
        
        print(f"   🗑️ 删除空会话目录: {len(empty_sessions)} 个")
        print(f"   ✅ 保留有效会话: {len(valid_sessions)} 个")
        
        for session in valid_sessions:
            print(f"      - {session}")
    
    # 4. 检查outputs目录中的文件
    outputs_kg_path = results_path / "outputs" / "knowledge_graphs"
    if outputs_kg_path.exists():
        kg_files = list(outputs_kg_path.glob("*.json"))
        print(f"   📊 知识图谱文件: {len(kg_files)} 个")
        
        for kg_file in kg_files:
            file_size = kg_file.stat().st_size / 1024  # KB
            print(f"      - {kg_file.name}: {file_size:.1f} KB")
    
    outputs_analysis_path = results_path / "outputs" / "analysis"
    if outputs_analysis_path.exists():
        analysis_files = list(outputs_analysis_path.glob("*.json"))
        print(f"   📈 分析文件: {len(analysis_files)} 个")
        
        for analysis_file in analysis_files:
            file_size = analysis_file.stat().st_size / 1024  # KB
            print(f"      - {analysis_file.name}: {file_size:.1f} KB")
    
    # 5. 创建README文件说明结构
    readme_content = """# Results 目录结构说明

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
"""
    
    readme_path = results_path / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"\n📝 创建README.md说明文件")
    
    # 6. 生成结构报告
    print(f"\n📊 最终文件结构报告:")
    print_directory_tree(results_path)
    
    print(f"\n✅ 文件结构整理完成!")

def print_directory_tree(path, prefix="", max_depth=3, current_depth=0):
    """打印目录树结构"""
    if current_depth >= max_depth:
        return
    
    path = Path(path)
    if not path.exists():
        return
    
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        
        if item.is_file():
            size = item.stat().st_size / 1024  # KB
            print(f"{prefix}{current_prefix}{item.name} ({size:.1f} KB)")
        else:
            print(f"{prefix}{current_prefix}{item.name}/")
            
            if current_depth < max_depth - 1:
                next_prefix = prefix + ("    " if is_last else "│   ")
                print_directory_tree(item, next_prefix, max_depth, current_depth + 1)

if __name__ == "__main__":
    reorganize_results()
