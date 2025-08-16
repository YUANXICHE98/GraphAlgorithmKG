#!/usr/bin/env python3
"""
彻底清理results目录
消除重复文件，规范结构，添加CSV输出
"""

import os
import json
import shutil
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def cleanup_results_directory():
    """彻底清理results目录"""
    
    print("🧹 开始彻底清理results目录")
    print("🎯 目标: 消除重复，规范结构，添加多格式输出")
    print("=" * 80)
    
    results_path = Path("results")
    
    # 1. 备份当前results目录
    backup_path = Path(f"results_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    if results_path.exists():
        shutil.copytree(results_path, backup_path)
        print(f"💾 已备份到: {backup_path}")
    
    # 2. 创建新的清晰结构
    new_structure = {
        "sessions": "完整的处理会话记录",
        "knowledge_graphs": {
            "general": "通用知识图谱",
            "spatiotemporal": "时空知识图谱", 
            "mixed": "混合类型知识图谱"
        },
        "exports": {
            "json": "JSON格式导出",
            "csv": "CSV格式导出",
            "graphml": "GraphML格式导出",
            "gexf": "Gephi格式导出"
        },
        "analysis": "质量分析和统计报告",
        "cache": {
            "entities": "实体推断缓存",
            "schemas": "Schema检测缓存"
        },
        "backups": "历史备份文件"
    }
    
    print("📁 创建新的目录结构:")
    create_directory_structure(results_path, new_structure)
    
    # 3. 整理和去重知识图谱文件
    print(f"\n📦 整理知识图谱文件:")
    consolidate_knowledge_graphs(results_path)
    
    # 4. 生成多格式导出
    print(f"\n📤 生成多格式导出:")
    generate_multi_format_exports(results_path)
    
    # 5. 清理重复和无用文件
    print(f"\n🗑️ 清理重复和无用文件:")
    cleanup_duplicates_and_unused(results_path)
    
    # 6. 生成目录结构报告
    print(f"\n📊 生成最终结构报告:")
    generate_structure_report(results_path)
    
    print(f"\n✅ results目录清理完成!")

def create_directory_structure(base_path: Path, structure: Dict[str, Any], prefix: str = ""):
    """递归创建目录结构"""
    for key, value in structure.items():
        if isinstance(value, dict):
            # 创建子目录
            dir_path = base_path / key
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {prefix}{key}/")
            
            # 递归创建子结构
            create_directory_structure(dir_path, value, prefix + "  ")
        else:
            # 创建目录并添加说明
            dir_path = base_path / key
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {prefix}{key}: {value}")

def consolidate_knowledge_graphs(results_path: Path):
    """整理和去重知识图谱文件"""
    
    # 收集所有KG文件
    kg_files = []
    
    # 从原始outputs目录收集
    old_kg_path = results_path / "outputs" / "knowledge_graphs"
    if old_kg_path.exists():
        kg_files.extend(old_kg_path.glob("*.json"))
    
    # 从by_schema目录收集
    by_schema_path = results_path / "outputs" / "by_schema"
    if by_schema_path.exists():
        for schema_dir in by_schema_path.iterdir():
            if schema_dir.is_dir():
                kg_dir = schema_dir / "knowledge_graphs"
                if kg_dir.exists():
                    kg_files.extend(kg_dir.glob("*.json"))
    
    print(f"   📄 找到 {len(kg_files)} 个KG文件")
    
    # 按Schema分类并去重
    schema_files = {"general": [], "spatiotemporal": [], "mixed": []}
    processed_files = set()
    
    for kg_file in kg_files:
        try:
            # 读取文件内容
            with open(kg_file, 'r', encoding='utf-8') as f:
                kg_data = json.load(f)
            
            # 生成内容哈希用于去重
            content_hash = hash(json.dumps(kg_data, sort_keys=True))
            if content_hash in processed_files:
                print(f"   🔄 跳过重复文件: {kg_file.name}")
                continue
            
            processed_files.add(content_hash)
            
            # 确定Schema类型
            schema_used = kg_data.get('metadata', {}).get('schema', '')
            schema_category = classify_schema_type(schema_used)
            
            # 生成标准文件名
            session_id = extract_session_id_from_filename(kg_file.name)
            new_filename = f"{session_id}_{schema_category}_kg.json"
            
            # 移动到新位置
            target_path = results_path / "knowledge_graphs" / schema_category / new_filename
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(kg_data, f, ensure_ascii=False, indent=2)
            
            schema_files[schema_category].append(target_path)
            print(f"   📄 {kg_file.name} -> {schema_category}/{new_filename}")
            
        except Exception as e:
            print(f"   ❌ 处理文件失败 {kg_file.name}: {e}")
    
    # 统计结果
    for schema, files in schema_files.items():
        print(f"   📊 {schema}: {len(files)} 个文件")

def generate_multi_format_exports(results_path: Path):
    """生成多格式导出文件"""
    
    # 为每个Schema类型生成导出
    for schema_type in ["general", "spatiotemporal", "mixed"]:
        kg_dir = results_path / "knowledge_graphs" / schema_type
        if not kg_dir.exists():
            continue
        
        kg_files = list(kg_dir.glob("*.json"))
        if not kg_files:
            continue
        
        print(f"   📊 处理 {schema_type} Schema ({len(kg_files)} 个文件)")
        
        # 合并所有KG数据
        all_entities = []
        all_relations = []
        
        for kg_file in kg_files:
            try:
                with open(kg_file, 'r', encoding='utf-8') as f:
                    kg_data = json.load(f)
                
                # 提取实体
                for entity in kg_data.get('entities', []):
                    entity_record = {
                        'id': entity.get('id', ''),
                        'name': entity.get('name', ''),
                        'type': entity.get('type', ''),
                        'schema': schema_type,
                        'confidence': entity.get('confidence', 0.0),
                        'source_file': kg_file.name
                    }
                    all_entities.append(entity_record)
                
                # 提取关系
                for relation in kg_data.get('relations', []):
                    relation_record = {
                        'id': relation.get('id', ''),
                        'subject': relation.get('subject', ''),
                        'predicate': relation.get('predicate', ''),
                        'object': relation.get('object', ''),
                        'schema': schema_type,
                        'confidence': relation.get('confidence', 0.0),
                        'source_file': kg_file.name
                    }
                    all_relations.append(relation_record)
                    
            except Exception as e:
                print(f"     ❌ 处理文件失败 {kg_file.name}: {e}")
        
        # 生成CSV导出
        if all_entities:
            entities_df = pd.DataFrame(all_entities)
            entities_csv = results_path / "exports" / "csv" / f"{schema_type}_entities.csv"
            entities_csv.parent.mkdir(parents=True, exist_ok=True)
            entities_df.to_csv(entities_csv, index=False, encoding='utf-8')
            print(f"     📄 实体CSV: {entities_csv.name} ({len(all_entities)} 行)")
        
        if all_relations:
            relations_df = pd.DataFrame(all_relations)
            relations_csv = results_path / "exports" / "csv" / f"{schema_type}_relations.csv"
            relations_df.to_csv(relations_csv, index=False, encoding='utf-8')
            print(f"     📄 关系CSV: {relations_csv.name} ({len(all_relations)} 行)")
        
        # 生成统计报告
        stats = {
            'schema_type': schema_type,
            'total_files': len(kg_files),
            'total_entities': len(all_entities),
            'total_relations': len(all_relations),
            'entity_types': list(set(e['type'] for e in all_entities)),
            'relation_types': list(set(r['predicate'] for r in all_relations)),
            'generated_time': datetime.now().isoformat()
        }
        
        stats_file = results_path / "analysis" / f"{schema_type}_statistics.json"
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"     📊 统计报告: {stats_file.name}")

def cleanup_duplicates_and_unused(results_path: Path):
    """清理重复和无用文件"""
    
    # 删除旧的outputs目录
    old_outputs = results_path / "outputs"
    if old_outputs.exists():
        shutil.rmtree(old_outputs)
        print(f"   🗑️ 删除旧的outputs目录")
    
    # 清理空目录
    for root, dirs, files in os.walk(results_path, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    print(f"   🗑️ 删除空目录: {dir_path.relative_to(results_path)}")
            except OSError:
                pass  # 目录不为空或其他错误
    
    # 移动备份文件
    backups_dir = results_path / "backups"
    backups_dir.mkdir(exist_ok=True)
    
    for backup_file in results_path.glob("*.pkl"):
        target_path = backups_dir / backup_file.name
        shutil.move(str(backup_file), str(target_path))
        print(f"   📦 移动备份文件: {backup_file.name}")

def generate_structure_report(results_path: Path):
    """生成最终结构报告"""
    
    report = {
        'cleanup_time': datetime.now().isoformat(),
        'directory_structure': {},
        'file_statistics': {},
        'schema_distribution': {}
    }
    
    # 统计目录结构
    for item in results_path.rglob('*'):
        if item.is_file():
            rel_path = item.relative_to(results_path)
            category = str(rel_path.parts[0]) if rel_path.parts else 'root'
            
            if category not in report['file_statistics']:
                report['file_statistics'][category] = {'count': 0, 'total_size': 0}
            
            report['file_statistics'][category]['count'] += 1
            report['file_statistics'][category]['total_size'] += item.stat().st_size
    
    # 统计Schema分布
    kg_base = results_path / "knowledge_graphs"
    if kg_base.exists():
        for schema_dir in kg_base.iterdir():
            if schema_dir.is_dir():
                kg_files = list(schema_dir.glob("*.json"))
                report['schema_distribution'][schema_dir.name] = len(kg_files)
    
    # 保存报告
    report_file = results_path / "CLEANUP_REPORT.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 打印摘要
    print("📊 最终结构摘要:")
    for category, stats in report['file_statistics'].items():
        size_mb = stats['total_size'] / (1024 * 1024)
        print(f"   📁 {category}: {stats['count']} 文件, {size_mb:.1f} MB")
    
    print("📋 Schema分布:")
    for schema, count in report['schema_distribution'].items():
        print(f"   🎯 {schema}: {count} 个知识图谱")
    
    print(f"📄 详细报告: {report_file}")

def classify_schema_type(schema_path: str) -> str:
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

def extract_session_id_from_filename(filename: str) -> str:
    """从文件名提取会话ID"""
    # 尝试提取时间戳格式的会话ID
    parts = filename.split('_')
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{parts[0]}_{parts[1]}"
    
    # 如果没有找到，使用文件名前缀
    return filename.split('.')[0].split('_')[0]

if __name__ == "__main__":
    cleanup_results_directory()
