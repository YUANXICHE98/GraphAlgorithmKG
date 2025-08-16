#!/usr/bin/env python3
"""
测试新的会话管理系统
验证中间结果保存和文件结构
"""

import sys
import os
import json
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.schema_based_kg_builder import SchemaBasedKGBuilder
from pipeline.session_manager import session_manager

def test_session_management():
    """测试会话管理功能"""
    print("🧪 测试会话管理系统")
    print("=" * 80)
    
    builder = SchemaBasedKGBuilder()
    
    # 测试文档
    test_doc = "data/test_documents/dodaf_enterprise_architecture.json"
    
    print(f"\n📄 测试文档: {test_doc}")
    
    try:
        # 构建知识图谱（会自动管理会话）
        kg = builder.build_knowledge_graph(test_doc)
        
        print(f"\n🔍 验证会话结果:")
        
        # 列出所有会话
        sessions = session_manager.list_sessions()
        if sessions:
            latest_session = sessions[0]  # 最新的会话
            session_id = latest_session['session_id']
            
            print(f"   📋 最新会话: {session_id}")
            print(f"   ⏱️ 处理时间: {latest_session.get('total_processing_time', 0):.2f}s")
            print(f"   📊 完成阶段: {len(latest_session.get('stages_completed', []))} 个")
            
            # 检查中间结果
            intermediate_results = session_manager.get_intermediate_results(session_id)
            print(f"\n📁 中间结果文件:")
            for stage_name, file_path in intermediate_results.items():
                file_size = Path(file_path).stat().st_size / 1024  # KB
                print(f"   {stage_name}: {file_size:.1f} KB")
            
            # 检查具体阶段内容
            print(f"\n🔍 阶段内容检查:")
            
            # 检查文档输入阶段
            doc_input = session_manager.get_stage_result(session_id, "document_input")
            if doc_input:
                print(f"   📖 文档输入: {doc_input['data']['content_length']} 字符")
            
            # 检查Schema检测阶段
            schema_detection = session_manager.get_stage_result(session_id, "schema_detection")
            if schema_detection:
                candidates = schema_detection['data']['candidates']
                selected = schema_detection['data']['selected_schema']
                print(f"   🎯 Schema检测: {len(candidates)} 个候选，选择 {selected}")
            
            # 检查三元组抽取阶段
            triple_extraction = session_manager.get_stage_result(session_id, "triple_extraction")
            if triple_extraction:
                rule_count = triple_extraction['data']['rule_extraction_count']
                llm_count = triple_extraction['data']['llm_extraction_count']
                total_triples = len(triple_extraction['data']['triples'])
                print(f"   🔄 三元组抽取: 规则{rule_count}个，LLM{llm_count}个，最终{total_triples}个")
            
            # 检查实体推断阶段
            entity_inference = session_manager.get_stage_result(session_id, "entity_inference")
            if entity_inference:
                entities = len(entity_inference['data']['entities'])
                relations = len(entity_inference['data']['relations'])
                print(f"   🏗️ 实体推断: {entities} 个实体，{relations} 个关系")
            
            # 检查最终KG
            final_kg = session_manager.get_stage_result(session_id, "final_kg")
            if final_kg:
                total_entities = final_kg['data']['statistics']['total_entities']
                total_relations = final_kg['data']['statistics']['total_relations']
                print(f"   📦 最终KG: {total_entities} 个实体，{total_relations} 个关系")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_structure():
    """测试文件结构"""
    print(f"\n\n📁 测试文件结构")
    print("=" * 80)
    
    results_path = Path("results")
    
    if not results_path.exists():
        print("❌ results目录不存在")
        return False
    
    # 检查目录结构
    expected_dirs = [
        "sessions",
        "outputs/knowledge_graphs",
        "outputs/intermediate", 
        "outputs/analysis",
        "cache/entities",
        "cache/schemas"
    ]
    
    print("🔍 检查目录结构:")
    for expected_dir in expected_dirs:
        dir_path = results_path / expected_dir
        exists = dir_path.exists()
        print(f"   {expected_dir}: {'✅ 存在' if exists else '❌ 缺失'}")
    
    # 检查会话文件
    sessions_path = results_path / "sessions"
    if sessions_path.exists():
        sessions = list(sessions_path.iterdir())
        print(f"\n📋 会话数量: {len([s for s in sessions if s.is_dir()])} 个")
        
        for session_dir in sessions:
            if session_dir.is_dir() and not session_dir.name.startswith('.'):
                files = list(session_dir.glob("*.json"))
                print(f"   {session_dir.name}: {len(files)} 个文件")
    
    # 检查输出文件
    kg_path = results_path / "outputs" / "knowledge_graphs"
    if kg_path.exists():
        kg_files = list(kg_path.glob("*.json"))
        print(f"\n📦 知识图谱文件: {len(kg_files)} 个")
        for kg_file in kg_files:
            file_size = kg_file.stat().st_size / 1024  # KB
            print(f"   {kg_file.name}: {file_size:.1f} KB")
    
    analysis_path = results_path / "outputs" / "analysis"
    if analysis_path.exists():
        analysis_files = list(analysis_path.glob("*.json"))
        print(f"\n📊 分析文件: {len(analysis_files)} 个")
        for analysis_file in analysis_files:
            file_size = analysis_file.stat().st_size / 1024  # KB
            print(f"   {analysis_file.name}: {file_size:.1f} KB")
    
    return True

def test_session_retrieval():
    """测试会话检索功能"""
    print(f"\n\n🔍 测试会话检索功能")
    print("=" * 80)
    
    # 列出所有会话
    sessions = session_manager.list_sessions()
    print(f"📋 总会话数: {len(sessions)}")
    
    if sessions:
        print(f"\n📊 会话详情:")
        for i, session in enumerate(sessions[:3], 1):  # 只显示前3个
            print(f"   {i}. {session['session_id']}")
            print(f"      文档: {session['document_path']}")
            print(f"      Schema: {session.get('schema_used', '未知')}")
            print(f"      耗时: {session.get('total_processing_time', 0):.2f}s")
            print(f"      阶段: {len(session.get('stages_completed', []))} 个")
            
            # 检查中间结果
            intermediate = session_manager.get_intermediate_results(session['session_id'])
            print(f"      中间文件: {len(intermediate)} 个")
    
    return True

def main():
    """主测试函数"""
    print("🧪 会话管理系统测试套件")
    print("🎯 目标: 验证新的文件结构和会话管理功能")
    print("=" * 100)
    
    tests = [
        ("会话管理功能", test_session_management),
        ("文件结构", test_file_structure),
        ("会话检索功能", test_session_retrieval)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print(f"\n\n🎉 测试总结")
    print("=" * 100)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"✅ 成功: {success_count}/{total_count}")
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    if success_count == total_count:
        print(f"\n🎯 结论: 会话管理系统工作正常！")
    else:
        print(f"\n⚠️ 结论: 部分功能需要修复")

if __name__ == "__main__":
    main()
