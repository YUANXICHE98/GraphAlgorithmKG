#!/usr/bin/env python3
"""
测试基于Schema的知识图谱构建器
"""

import sys
import os
import json
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.schema_based_kg_builder import SchemaBasedKGBuilder

def test_kg_building():
    """测试知识图谱构建功能"""
    print("🏗️ 测试基于Schema的知识图谱构建")
    print("=" * 80)
    
    builder = SchemaBasedKGBuilder()
    
    # 测试文档列表
    test_documents = [
        {
            "path": "data/test_documents/dodaf_enterprise_architecture.json",
            "name": "通用架构文档",
            "expected_schema": "通用本体"
        },
        {
            "path": "data/test_documents/dodaf_spatiotemporal.json", 
            "name": "时空描述文档",
            "expected_schema": "时空本体"
        },
        {
            "path": "data/test_documents/pure_dodaf_structure.json",
            "name": "纯DO-DA-F结构",
            "expected_schema": "时空本体"
        }
    ]
    
    results = []
    
    for i, doc_info in enumerate(test_documents, 1):
        print(f"\n📄 测试 {i}: {doc_info['name']}")
        print("-" * 60)
        
        try:
            # 构建知识图谱
            # 直接使用session_manager保存，不需要output路径
            kg = builder.build_knowledge_graph(
                document_path=doc_info["path"]
            )
            
            # 分析结果
            print(f"\n📊 构建结果分析:")
            print(f"   📋 使用Schema: {kg.metadata['schema']}")
            print(f"   🏷️ 实体数量: {kg.statistics['total_entities']}")
            print(f"   🔗 关系数量: {kg.statistics['total_relations']}")
            print(f"   ⏱️ 处理时间: {kg.statistics.get('processing_time', 0):.2f}s")
            print(f"   📈 平均实体置信度: {kg.statistics['average_entity_confidence']:.2f}")
            print(f"   📈 平均关系置信度: {kg.statistics['average_relation_confidence']:.2f}")
            
            # 实体类型分布
            print(f"\n🏷️ 实体类型分布:")
            for entity_type, count in kg.statistics['entity_type_distribution'].items():
                print(f"   {entity_type:<20}: {count} 个")
            
            # 关系类型分布
            print(f"\n🔗 关系类型分布:")
            for relation_type, count in kg.statistics['relation_type_distribution'].items():
                print(f"   {relation_type:<20}: {count} 个")
            
            # 显示部分实体示例
            print(f"\n📋 实体示例 (前5个):")
            for j, entity in enumerate(kg.entities[:5], 1):
                print(f"   {j}. {entity.name} ({entity.type}) - 置信度: {entity.confidence:.2f}")
            
            # 显示部分关系示例
            print(f"\n🔗 关系示例 (前5个):")
            for j, relation in enumerate(kg.relations[:5], 1):
                print(f"   {j}. ({relation.subject_name}, {relation.predicate}, {relation.object_name}) - 置信度: {relation.confidence:.2f}")
            
            results.append({
                "document": doc_info["name"],
                "success": True,
                "entities": kg.statistics['total_entities'],
                "relations": kg.statistics['total_relations'],
                "schema": kg.metadata['schema'],
                "processing_time": kg.statistics.get('processing_time', 0)
            })
            
        except Exception as e:
            print(f"❌ 构建失败: {e}")
            import traceback
            traceback.print_exc()
            
            results.append({
                "document": doc_info["name"],
                "success": False,
                "error": str(e)
            })
    
    # 总结报告
    print(f"\n\n📊 测试总结报告")
    print("=" * 80)
    
    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]
    
    print(f"✅ 成功测试: {len(successful_tests)}/{len(results)}")
    print(f"❌ 失败测试: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        total_entities = sum(r["entities"] for r in successful_tests)
        total_relations = sum(r["relations"] for r in successful_tests)
        avg_processing_time = sum(r["processing_time"] for r in successful_tests) / len(successful_tests)
        
        print(f"\n📈 整体统计:")
        print(f"   总实体数: {total_entities}")
        print(f"   总关系数: {total_relations}")
        print(f"   平均处理时间: {avg_processing_time:.2f}s")
        
        print(f"\n📋 详细结果:")
        for result in successful_tests:
            print(f"   {result['document']:<25}: {result['entities']} 实体, {result['relations']} 关系, {result['processing_time']:.2f}s")
    
    if failed_tests:
        print(f"\n❌ 失败详情:")
        for result in failed_tests:
            print(f"   {result['document']}: {result['error']}")
    
    return len(successful_tests) == len(results)

def test_json_format():
    """测试JSON格式的正确性"""
    print(f"\n\n🔍 测试JSON格式")
    print("=" * 80)
    
    # 检查生成的JSON文件
    # 检查results目录下的文件
    results_dir = Path("results/knowledge_graphs")
    output_files = list(results_dir.rglob("*.json"))
    
    for i, file_path in enumerate(output_files, 1):
        if os.path.exists(file_path):
            print(f"\n📄 检查文件 {i}: {file_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    kg_data = json.load(f)
                
                # 验证JSON结构
                required_keys = ['metadata', 'entities', 'relations', 'statistics']
                for key in required_keys:
                    if key not in kg_data:
                        print(f"❌ 缺少必需字段: {key}")
                        continue
                
                print(f"✅ JSON结构正确")
                print(f"   元数据字段: {list(kg_data['metadata'].keys())}")
                print(f"   实体数量: {len(kg_data['entities'])}")
                print(f"   关系数量: {len(kg_data['relations'])}")
                print(f"   统计字段: {list(kg_data['statistics'].keys())}")
                
                # 检查实体结构
                if kg_data['entities']:
                    entity = kg_data['entities'][0]
                    entity_keys = list(entity.keys())
                    print(f"   实体字段: {entity_keys}")
                
                # 检查关系结构
                if kg_data['relations']:
                    relation = kg_data['relations'][0]
                    relation_keys = list(relation.keys())
                    print(f"   关系字段: {relation_keys}")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON格式错误: {e}")
            except Exception as e:
                print(f"❌ 文件读取错误: {e}")
        else:
            print(f"⚠️ 文件不存在: {file_path}")

def main():
    """主测试函数"""
    print("🧪 基于Schema的知识图谱构建测试套件")
    print("=" * 100)
    
    try:
        # 测试1: KG构建功能
        success = test_kg_building()
        
        # 测试2: JSON格式验证
        test_json_format()
        
        print(f"\n🎉 测试完成! 整体结果: {'✅ 成功' if success else '❌ 部分失败'}")
        
    except Exception as e:
        print(f"\n❌ 测试套件执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
