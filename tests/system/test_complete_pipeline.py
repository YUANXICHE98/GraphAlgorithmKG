#!/usr/bin/env python3
"""
测试完整的Pipeline流程
验证新的文件结构和混合抽取架构
"""

import sys
import os
import json
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.schema_based_kg_builder import SchemaBasedKGBuilder
from pipeline.session_manager import session_manager

def test_complete_pipeline():
    """测试完整的Pipeline流程"""
    print("🚀 测试完整Pipeline流程")
    print("🎯 目标: 验证文件结构整理和混合抽取架构")
    print("=" * 100)
    
    builder = SchemaBasedKGBuilder()
    
    # 测试三种不同类型的文档
    test_cases = [
        {
            "name": "通用架构文档",
            "path": "data/test_documents/dodaf_enterprise_architecture.json",
            "expected_schema": "通用本体",
            "expected_entities": 5,
            "expected_relations": 3
        },
        {
            "name": "时空描述文档", 
            "path": "data/test_documents/dodaf_spatiotemporal.json",
            "expected_schema": "时空本体",
            "expected_entities": 8,
            "expected_relations": 6
        },
        {
            "name": "DO-DA-F结构文档",
            "path": "data/test_documents/pure_dodaf_structure.json", 
            "expected_schema": "时空本体",
            "expected_entities": 10,
            "expected_relations": 8
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📄 测试 {i}: {test_case['name']}")
        print("=" * 80)
        
        try:
            # 构建知识图谱
            kg = builder.build_knowledge_graph(test_case["path"])
            
            # 验证结果
            success = True
            issues = []
            
            # 检查Schema选择
            schema_used = kg.metadata.get('schema', '')
            if test_case['expected_schema'] == "通用本体" and 'schema_config.yaml' not in schema_used:
                issues.append(f"Schema选择错误: 期望通用本体，实际{schema_used}")
                success = False
            elif test_case['expected_schema'] == "时空本体" and 'spatiotemporal' not in schema_used:
                issues.append(f"Schema选择错误: 期望时空本体，实际{schema_used}")
                success = False
            
            # 检查实体和关系数量（允许一定误差）
            actual_entities = kg.statistics['total_entities']
            actual_relations = kg.statistics['total_relations']
            
            if actual_entities == 0:
                issues.append("实体数量为0，可能存在抽取问题")
                success = False
            
            if actual_relations == 0:
                issues.append("关系数量为0，可能存在抽取问题")
                success = False
            
            # 记录结果
            result = {
                "test_case": test_case['name'],
                "success": success,
                "issues": issues,
                "schema_used": schema_used,
                "entities": actual_entities,
                "relations": actual_relations,
                "processing_time": kg.statistics.get('processing_time', 0)
            }
            
            results.append(result)
            
            # 显示详细结果
            print(f"✅ 测试完成")
            print(f"   📋 Schema: {schema_used}")
            print(f"   🏷️ 实体: {actual_entities} 个")
            print(f"   🔗 关系: {actual_relations} 个")
            print(f"   ⏱️ 耗时: {result['processing_time']:.2f}s")
            
            if issues:
                print(f"   ⚠️ 问题:")
                for issue in issues:
                    print(f"      - {issue}")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            
            results.append({
                "test_case": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    return results

def test_file_structure():
    """测试新的文件结构"""
    print(f"\n\n📁 测试新的文件结构")
    print("=" * 100)
    
    results_path = Path("results")
    
    # 检查目录结构
    expected_structure = [
        "sessions",
        "outputs/knowledge_graphs",
        "outputs/analysis", 
        "outputs/exports",
        "outputs/intermediate",
        "cache/entities",
        "cache/schemas",
        "backups"
    ]
    
    print("🔍 检查目录结构:")
    structure_ok = True
    
    for expected_dir in expected_structure:
        dir_path = results_path / expected_dir
        exists = dir_path.exists()
        print(f"   {expected_dir}: {'✅ 存在' if exists else '❌ 缺失'}")
        if not exists:
            structure_ok = False
    
    # 检查README文件
    readme_path = results_path / "README.md"
    readme_exists = readme_path.exists()
    print(f"   README.md: {'✅ 存在' if readme_exists else '❌ 缺失'}")
    
    # 统计文件数量
    print(f"\n📊 文件统计:")
    
    # 会话文件
    sessions_path = results_path / "sessions"
    if sessions_path.exists():
        sessions = [d for d in sessions_path.iterdir() if d.is_dir() and d.name != "latest"]
        print(f"   📋 有效会话: {len(sessions)} 个")
        
        # 检查最新会话的完整性
        latest_link = sessions_path / "latest"
        if latest_link.exists():
            if latest_link.is_symlink():
                target = latest_link.readlink()
                print(f"   🔗 latest链接: -> {target}")
            else:
                # 检查latest目录内容
                latest_files = list(latest_link.glob("*.json"))
                print(f"   📁 latest目录: {len(latest_files)} 个文件")
    
    # 输出文件
    kg_path = results_path / "outputs" / "knowledge_graphs"
    if kg_path.exists():
        kg_files = list(kg_path.glob("*.json"))
        total_size = sum(f.stat().st_size for f in kg_files) / 1024  # KB
        print(f"   📦 知识图谱: {len(kg_files)} 个文件, {total_size:.1f} KB")
    
    # 导出文件
    exports_path = results_path / "outputs" / "exports"
    if exports_path.exists():
        export_files = list(exports_path.glob("*"))
        export_files = [f for f in export_files if f.is_file()]
        print(f"   📤 导出文件: {len(export_files)} 个")
    
    # 备份文件
    backups_path = results_path / "backups"
    if backups_path.exists():
        backup_files = list(backups_path.glob("*.pkl"))
        total_backup_size = sum(f.stat().st_size for f in backup_files) / 1024  # KB
        print(f"   💾 备份文件: {len(backup_files)} 个, {total_backup_size:.1f} KB")
    
    return structure_ok and readme_exists

def test_session_management():
    """测试会话管理功能"""
    print(f"\n\n🔄 测试会话管理功能")
    print("=" * 100)
    
    # 列出所有会话
    sessions = session_manager.list_sessions()
    print(f"📋 总会话数: {len(sessions)}")
    
    if not sessions:
        print("❌ 没有找到任何会话")
        return False
    
    # 检查最新会话
    latest_session = sessions[0]
    session_id = latest_session['session_id']
    
    print(f"\n🔍 检查最新会话: {session_id}")
    print(f"   📄 文档: {latest_session['document_path']}")
    print(f"   ⏱️ 耗时: {latest_session.get('total_processing_time', 0):.2f}s")
    print(f"   📊 阶段: {len(latest_session.get('stages_completed', []))} 个")
    
    # 检查中间结果
    intermediate_results = session_manager.get_intermediate_results(session_id)
    print(f"\n📁 中间结果文件: {len(intermediate_results)} 个")
    
    expected_stages = [
        "document_input", "schema_detection", "triple_extraction", 
        "entity_inference", "final_kg"
    ]
    
    stages_ok = True
    for stage in expected_stages:
        if stage in intermediate_results:
            file_path = Path(intermediate_results[stage])
            file_size = file_path.stat().st_size / 1024  # KB
            print(f"   ✅ {stage}: {file_size:.1f} KB")
        else:
            print(f"   ❌ {stage}: 缺失")
            stages_ok = False
    
    return stages_ok

def main():
    """主测试函数"""
    print("🧪 完整Pipeline测试套件")
    print("🎯 验证文件结构整理和混合抽取架构的完整性")
    print("=" * 120)
    
    # 执行所有测试
    tests = [
        ("Pipeline流程", test_complete_pipeline),
        ("文件结构", test_file_structure), 
        ("会话管理", test_session_management)
    ]
    
    all_results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*30} {test_name} {'='*30}")
        try:
            result = test_func()
            all_results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            all_results[test_name] = False
    
    # 总结报告
    print(f"\n\n🎉 完整测试总结")
    print("=" * 120)
    
    # Pipeline结果
    if "Pipeline流程" in all_results and isinstance(all_results["Pipeline流程"], list):
        pipeline_results = all_results["Pipeline流程"]
        success_count = sum(1 for r in pipeline_results if r.get("success", False))
        
        print(f"🚀 Pipeline测试: {success_count}/{len(pipeline_results)} 成功")
        
        for result in pipeline_results:
            status = "✅" if result.get("success", False) else "❌"
            test_name = result.get("test_case", "未知")
            entities = result.get("entities", 0)
            relations = result.get("relations", 0)
            time_cost = result.get("processing_time", 0)
            
            print(f"   {status} {test_name}: {entities}实体, {relations}关系, {time_cost:.2f}s")
            
            if result.get("issues"):
                for issue in result["issues"]:
                    print(f"      ⚠️ {issue}")
    
    # 其他测试结果
    for test_name, result in all_results.items():
        if test_name != "Pipeline流程":
            status = "✅ 通过" if result else "❌ 失败"
            print(f"📁 {test_name}: {status}")
    
    # 最终结论
    all_success = all(
        isinstance(result, list) and all(r.get("success", False) for r in result) 
        if isinstance(result, list) 
        else result 
        for result in all_results.values()
    )
    
    if all_success:
        print(f"\n🎯 结论: 🎉 所有测试通过！文件结构和Pipeline都工作正常！")
    else:
        print(f"\n🎯 结论: ⚠️ 部分测试需要优化")

if __name__ == "__main__":
    main()
