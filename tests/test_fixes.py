#!/usr/bin/env python3
"""
测试修复效果的脚本
"""

from pipeline.entity_type_inferer import EntityTypeInferer
from pipeline.neo4j_connector import Neo4jConnector

def test_entity_type_inference():
    """测试实体类型推断"""
    print("🔍 测试实体类型推断...")
    
    # 测试数据
    test_triples = [
        {"subject": "MINERVA", "predicate": "is_instance_of", "object": "Algorithm"},
        {"subject": "Sequential_Decision", "predicate": "is_instance_of", "object": "Paradigm"},
        {"subject": "Path_Ranking_Algorithm", "predicate": "is_instance_of", "object": "Algorithm"},
        {"subject": "MINERVA", "predicate": "uses_paradigm", "object": "Reinforcement_Learning"},
        {"subject": "Graph_Sparse_Reasoning", "predicate": "has_algorithm", "object": "MINERVA"},
    ]
    
    inferer = EntityTypeInferer()
    entity_types = inferer.infer_entity_types_from_triples(test_triples)
    
    print("推断的实体类型:")
    for entity, type_name in entity_types.items():
        print(f"   - {entity}: {type_name}")
    
    # 验证关键实体的类型
    expected = {
        "MINERVA": "Algorithm",
        "Sequential_Decision": "Paradigm", 
        "Path_Ranking_Algorithm": "Algorithm",
        "Reinforcement_Learning": "Paradigm",
        "Graph_Sparse_Reasoning": "Task"
    }
    
    success = True
    for entity, expected_type in expected.items():
        actual_type = entity_types.get(entity, "Unknown")
        if actual_type == expected_type:
            print(f"   ✅ {entity}: {actual_type} (正确)")
        else:
            print(f"   ❌ {entity}: {actual_type} (期望: {expected_type})")
            success = False
    
    return success

def test_neo4j_statistics():
    """测试Neo4j统计功能"""
    print("\n📊 测试Neo4j统计...")
    
    try:
        connector = Neo4jConnector(password="yuanxi98")
        if connector.connect():
            stats = connector.get_graph_statistics()
            print(f"✅ Neo4j连接成功")
            print(f"   节点数: {stats['nodes']}")
            print(f"   边数: {stats['edges']}")
            print(f"   实体类型: {stats['entity_types']}")
            print(f"   关系类型: {stats['relation_types']}")
            
            connector.disconnect()
            return stats['edges'] > 0  # 如果边数大于0说明统计修复成功
        else:
            print("❌ Neo4j连接失败")
            return False
            
    except Exception as e:
        print(f"❌ Neo4j测试出错: {e}")
        return False

def main():
    print("=== 修复效果测试 ===\n")
    
    # 测试1: 实体类型推断
    type_inference_ok = test_entity_type_inference()
    
    # 测试2: Neo4j统计
    neo4j_stats_ok = test_neo4j_statistics()
    
    # 总结
    print(f"\n📋 测试结果:")
    print(f"   实体类型推断: {'✅' if type_inference_ok else '❌'}")
    print(f"   Neo4j统计修复: {'✅' if neo4j_stats_ok else '❌'}")
    
    if type_inference_ok and neo4j_stats_ok:
        print("\n🎉 所有测试通过! 可以重新运行主程序了")
        print("\n建议运行:")
        print("python3 dynamic_main.py data/graph_algorithm_triples.csv --import-to-neo4j --neo4j-clear")
    else:
        print("\n⚠️  部分测试失败，需要进一步调试")

if __name__ == "__main__":
    main() 