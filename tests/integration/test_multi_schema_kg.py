#!/usr/bin/env python3
"""
多Schema知识图谱构建测试
专门测试通用、时空、DO-DA-F三种不同Schema的KG构建效果
"""

import sys
import os
import json
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.schema_based_kg_builder import SchemaBasedKGBuilder

def test_general_schema_kg():
    """测试通用Schema的KG构建"""
    print("🎯 测试1: 通用Schema知识图谱构建")
    print("=" * 100)
    
    builder = SchemaBasedKGBuilder()
    
    # 使用通用架构文档
    document_path = "data/test_documents/dodaf_enterprise_architecture.json"
    # 使用session_manager自动保存，不需要指定output路径
    
    try:
        kg = builder.build_knowledge_graph(document_path)
        
        # 验证结果
        print(f"\n🔍 结果验证:")
        print(f"   期望Schema类型: 通用本体")
        print(f"   实际Schema: {kg.metadata['schema']}")
        print(f"   Schema匹配: {'✅ 正确' if 'schema_config.yaml' in kg.metadata['schema'] else '❌ 错误'}")
        
        # 检查是否包含预期的通用实体
        expected_entities = ["DoDAF", "Operational View", "System View", "OV-1", "SV-1"]
        found_entities = [e.name for e in kg.entities]
        
        print(f"\n📋 实体检查:")
        for expected in expected_entities:
            found = any(expected.lower() in entity.lower() for entity in found_entities)
            print(f"   {expected}: {'✅ 找到' if found else '❌ 未找到'}")
        
        return kg
        
    except Exception as e:
        print(f"❌ 通用Schema测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_spatiotemporal_schema_kg():
    """测试时空Schema的KG构建"""
    print("\n\n🌍 测试2: 时空Schema知识图谱构建")
    print("=" * 100)
    
    builder = SchemaBasedKGBuilder()
    
    # 使用时空描述文档
    document_path = "data/test_documents/dodaf_spatiotemporal.json"
    try:
        kg = builder.build_knowledge_graph(document_path)
        
        # 验证结果
        print(f"\n🔍 结果验证:")
        print(f"   期望Schema类型: 时空本体")
        print(f"   实际Schema: {kg.metadata['schema']}")
        print(f"   Schema匹配: {'✅ 正确' if 'spatiotemporal' in kg.metadata['schema'] else '❌ 错误'}")
        
        # 检查是否包含预期的时空实体
        expected_entities = ["洪水事件", "长江流域", "2024-10-23 08:00", "4小时", "执行水位监测"]
        found_entities = [e.name for e in kg.entities]
        
        print(f"\n📋 实体检查:")
        for expected in expected_entities:
            found = any(expected in entity for entity in found_entities)
            print(f"   {expected}: {'✅ 找到' if found else '❌ 未找到'}")
        
        # 检查时空关系
        expected_relations = ["hasStartTime", "locatedAt", "hasDuration"]
        found_relations = [r.predicate for r in kg.relations]
        
        print(f"\n🔗 关系检查:")
        for expected in expected_relations:
            found = expected in found_relations
            print(f"   {expected}: {'✅ 找到' if found else '❌ 未找到'}")
        
        return kg
        
    except Exception as e:
        print(f"❌ 时空Schema测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_dodaf_structure_kg():
    """测试DO-DA-F结构的KG构建"""
    print("\n\n🔧 测试3: DO-DA-F结构知识图谱构建")
    print("=" * 100)
    
    builder = SchemaBasedKGBuilder()
    
    # 使用纯DO-DA-F结构文档
    document_path = "data/test_documents/pure_dodaf_structure.json"
    try:
        kg = builder.build_knowledge_graph(document_path)
        
        # 验证结果
        print(f"\n🔍 结果验证:")
        print(f"   期望Schema类型: 时空本体 (DO-DA-F)")
        print(f"   实际Schema: {kg.metadata['schema']}")
        print(f"   Schema匹配: {'✅ 正确' if 'spatiotemporal' in kg.metadata['schema'] else '❌ 错误'}")
        
        # 检查DO-DA-F三元结构
        action_entities = [e for e in kg.entities if e.type == "Action"]
        condition_entities = [e for e in kg.entities if e.type == "Condition"]
        outcome_entities = [e for e in kg.entities if e.type == "Outcome"]
        
        print(f"\n🔧 DO-DA-F结构检查:")
        print(f"   Action (DO) 实体: {len(action_entities)} 个")
        for action in action_entities:
            print(f"      - {action.name} (置信度: {action.confidence:.2f})")
        
        print(f"   Condition (DA) 实体: {len(condition_entities)} 个")
        for condition in condition_entities:
            print(f"      - {condition.name} (置信度: {condition.confidence:.2f})")
        
        print(f"   Outcome (F) 实体: {len(outcome_entities)} 个")
        for outcome in outcome_entities:
            print(f"      - {outcome.name} (置信度: {outcome.confidence:.2f})")
        
        # 检查DO-DA-F关系
        dodaf_relations = [r for r in kg.relations if r.predicate in ["hasCondition", "resultsIn", "causes"]]
        
        print(f"\n🔗 DO-DA-F关系检查:")
        print(f"   DO-DA-F关系: {len(dodaf_relations)} 个")
        for relation in dodaf_relations:
            print(f"      - ({relation.subject_name}, {relation.predicate}, {relation.object_name})")
        
        return kg
        
    except Exception as e:
        print(f"❌ DO-DA-F结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_schemas(general_kg, spatiotemporal_kg, dodaf_kg):
    """对比不同Schema的构建结果"""
    print("\n\n📊 多Schema对比分析")
    print("=" * 100)
    
    kgs = [
        ("通用Schema", general_kg),
        ("时空Schema", spatiotemporal_kg), 
        ("DO-DA-F结构", dodaf_kg)
    ]
    
    # 基本统计对比
    print(f"\n📈 基本统计对比:")
    print(f"{'Schema类型':<15} {'实体数':<8} {'关系数':<8} {'处理时间':<10} {'平均实体置信度':<15}")
    print("-" * 70)
    
    for name, kg in kgs:
        if kg:
            stats = kg.statistics
            print(f"{name:<15} {stats['total_entities']:<8} {stats['total_relations']:<8} "
                  f"{stats.get('processing_time', 0):<10.2f} {stats['average_entity_confidence']:<15.2f}")
        else:
            print(f"{name:<15} {'失败':<8} {'失败':<8} {'失败':<10} {'失败':<15}")
    
    # 实体类型分布对比
    print(f"\n🏷️ 实体类型分布对比:")
    for name, kg in kgs:
        if kg:
            print(f"\n{name}:")
            for entity_type, count in kg.statistics['entity_type_distribution'].items():
                print(f"   {entity_type}: {count} 个")
    
    # 关系类型分布对比
    print(f"\n🔗 关系类型分布对比:")
    for name, kg in kgs:
        if kg:
            print(f"\n{name}:")
            for relation_type, count in kg.statistics['relation_type_distribution'].items():
                print(f"   {relation_type}: {count} 个")
    
    # Schema特色分析
    print(f"\n🎯 Schema特色分析:")
    
    if general_kg:
        framework_entities = [e for e in general_kg.entities if e.type == "Framework"]
        algorithm_entities = [e for e in general_kg.entities if e.type == "Algorithm"]
        print(f"\n通用Schema特色:")
        print(f"   Framework实体: {len(framework_entities)} 个 (架构框架类)")
        print(f"   Algorithm实体: {len(algorithm_entities)} 个 (算法模型类)")
    
    if spatiotemporal_kg:
        temporal_entities = [e for e in spatiotemporal_kg.entities if e.type == "TemporalEntity"]
        spatial_entities = [e for e in spatiotemporal_kg.entities if e.type == "SpatialEntity"]
        event_entities = [e for e in spatiotemporal_kg.entities if e.type == "Event"]
        print(f"\n时空Schema特色:")
        print(f"   TemporalEntity实体: {len(temporal_entities)} 个 (时间概念)")
        print(f"   SpatialEntity实体: {len(spatial_entities)} 个 (空间概念)")
        print(f"   Event实体: {len(event_entities)} 个 (事件概念)")
    
    if dodaf_kg:
        action_entities = [e for e in dodaf_kg.entities if e.type == "Action"]
        condition_entities = [e for e in dodaf_kg.entities if e.type == "Condition"]
        outcome_entities = [e for e in dodaf_kg.entities if e.type == "Outcome"]
        print(f"\nDO-DA-F结构特色:")
        print(f"   Action实体: {len(action_entities)} 个 (动作)")
        print(f"   Condition实体: {len(condition_entities)} 个 (条件)")
        print(f"   Outcome实体: {len(outcome_entities)} 个 (结果)")

def main():
    """主测试函数"""
    print("🧪 多Schema知识图谱构建测试套件")
    print("🎯 目标: 验证不同Schema下的KG构建效果差异")
    print("=" * 120)
    
    # 测试三种不同的Schema
    general_kg = test_general_schema_kg()
    spatiotemporal_kg = test_spatiotemporal_schema_kg()
    dodaf_kg = test_dodaf_structure_kg()
    
    # 对比分析
    compare_schemas(general_kg, spatiotemporal_kg, dodaf_kg)
    
    # 总结
    success_count = sum(1 for kg in [general_kg, spatiotemporal_kg, dodaf_kg] if kg is not None)
    
    print(f"\n\n🎉 测试总结")
    print("=" * 100)
    print(f"✅ 成功测试: {success_count}/3")
    print(f"📊 生成的KG文件:")
    
    # 检查results目录下的KG文件
    results_dir = Path("results/knowledge_graphs")
    output_files = list(results_dir.rglob("*.json"))

    for file_path in output_files:
        if file_path.exists():
            file_size = file_path.stat().st_size / 1024  # KB
            print(f"   📁 {file_path} ({file_size:.1f} KB)")
        else:
            print(f"   ❌ {file_path} (未生成)")
    
    print(f"\n🎯 结论: {'多Schema系统工作正常' if success_count == 3 else '部分Schema需要优化'}")

if __name__ == "__main__":
    main()
