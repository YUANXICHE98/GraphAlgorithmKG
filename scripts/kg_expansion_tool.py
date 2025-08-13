#!/usr/bin/env python3
"""
知识图谱智能扩展工具
基于已有节点进行语义扩展，避免重复
"""

import json
from typing import Dict, List, Set, Tuple
from pathlib import Path
from pipeline.neo4j_connector import Neo4jConnector
from pipeline.entity_type_inferer import EntityTypeInferer

class KGExpansionTool:
    """知识图谱扩展工具"""
    
    def __init__(self, neo4j_password: str = "yuanxi98"):
        self.connector = Neo4jConnector(password=neo4j_password)
        self.type_inferer = EntityTypeInferer()
        self.existing_entities = set()
        self.existing_relations = set()
        
    def load_existing_kg(self):
        """加载现有知识图谱数据"""
        if self.connector.connect():
            # 获取所有现有实体
            with self.connector.driver.session() as session:
                entities_result = session.run("MATCH (e:Entity) RETURN e.name as name")
                self.existing_entities = {record["name"] for record in entities_result}
                
                # 获取所有现有关系
                relations_result = session.run("""
                    MATCH (s:Entity)-[r]->(o:Entity) 
                    RETURN s.name as subject, type(r) as predicate, o.name as object
                """)
                self.existing_relations = {
                    (record["subject"], record["predicate"], record["object"]) 
                    for record in relations_result
                }
            
            self.connector.disconnect()
            print(f"📊 已加载现有KG: {len(self.existing_entities)} 个实体, {len(self.existing_relations)} 个关系")
        else:
            print("❌ 无法连接Neo4j，使用空白KG")
    
    def expand_ant_colony_node(self) -> List[Dict]:
        """扩展Ant Colony节点"""
        print("🐜 开始扩展Ant Colony节点...")
        
        new_triples = []
        
        # 1. 经典应用任务
        classic_applications = [
            {
                "name": "Traveling_Salesman_Problem",
                "type": "Task",
                "description": "旅行商问题，寻找访问所有城市的最短路径",
                "aliases": ["TSP", "旅行商问题"]
            },
            {
                "name": "Vehicle_Routing_Problem", 
                "type": "Task",
                "description": "车辆路径问题，优化多车辆配送路径",
                "aliases": ["VRP", "车辆路径问题"]
            },
            {
                "name": "Combinatorial_Optimization",
                "type": "Task",
                "description": "组合优化问题，在有限集合中寻找最优解",
                "aliases": ["组合优化"]
            },
            {
                "name": "Path_Optimization",
                "type": "Task", 
                "description": "路径优化，寻找最优路径序列",
                "aliases": ["路径优化", "最优路径"]
            }
        ]
        
        # 2. 添加应用关系
        for app in classic_applications:
            if not self._entity_exists(app["name"]):
                # 添加实体定义三元组
                new_triples.append({
                    "subject": app["name"],
                    "predicate": "is_instance_of",
                    "object": app["type"],
                    "confidence": 1.0,
                    "source": "expansion_ant_colony"
                })
                
                # 添加Ant Colony解决这些问题的关系
                new_triples.append({
                    "subject": "Ant_Colony", 
                    "predicate": "solves",
                    "object": app["name"],
                    "confidence": 0.9,
                    "source": "expansion_ant_colony"
                })
                
                # 添加优势关系
                if app["name"] == "Traveling_Salesman_Problem":
                    new_triples.extend([
                        {
                            "subject": "Ant_Colony",
                            "predicate": "has_advantage_in",
                            "object": "Global_Search_Capability",
                            "confidence": 0.8,
                            "source": "expansion_ant_colony"
                        },
                        {
                            "subject": "Global_Search_Capability",
                            "predicate": "is_instance_of", 
                            "object": "Metric",
                            "confidence": 1.0,
                            "source": "expansion_ant_colony"
                        }
                    ])
        
        # 3. 相关算法（基于相似性）
        related_algorithms = self._find_related_algorithms("Ant_Colony")
        for algo in related_algorithms:
            if not self._relation_exists("Ant_Colony", "SIMILAR_TO", algo):
                new_triples.append({
                    "subject": "Ant_Colony",
                    "predicate": "similar_to", 
                    "object": algo,
                    "confidence": 0.7,
                    "source": "expansion_similarity"
                })
        
        # 4. 技术特征
        technical_features = [
            {
                "name": "Pheromone_Trail",
                "type": "Technique",
                "relation": "uses_technique"
            },
            {
                "name": "Positive_Feedback",
                "type": "Technique", 
                "relation": "implements"
            },
            {
                "name": "Stigmergy",
                "type": "Paradigm",
                "relation": "uses_paradigm"
            }
        ]
        
        for feature in technical_features:
            if not self._entity_exists(feature["name"]):
                new_triples.extend([
                    {
                        "subject": feature["name"],
                        "predicate": "is_instance_of",
                        "object": feature["type"],
                        "confidence": 1.0,
                        "source": "expansion_ant_colony"
                    },
                    {
                        "subject": "Ant_Colony",
                        "predicate": feature["relation"],
                        "object": feature["name"],
                        "confidence": 0.9,
                        "source": "expansion_ant_colony"
                    }
                ])
        
        print(f"🔍 生成了 {len(new_triples)} 个新三元组")
        return new_triples
    
    def _entity_exists(self, entity_name: str) -> bool:
        """检查实体是否已存在"""
        return entity_name in self.existing_entities
    
    def _relation_exists(self, subject: str, predicate: str, obj: str) -> bool:
        """检查关系是否已存在"""
        return (subject, predicate, obj) in self.existing_relations
    
    def _find_related_algorithms(self, target_algorithm: str) -> List[str]:
        """基于相似性找到相关算法"""
        # 基于算法特征的相似性匹配
        algorithm_features = {
            "Ant_Colony": ["optimization", "swarm", "nature_inspired", "population_based", "heuristic"],
            "Genetic_Algorithm": ["optimization", "evolution", "nature_inspired", "population_based", "heuristic"],
            "Particle_Swarm": ["optimization", "swarm", "nature_inspired", "population_based"],
            "Simulated_Annealing": ["optimization", "nature_inspired", "single_solution", "heuristic"],
            "Greedy_Search": ["optimization", "heuristic", "single_solution"],
            "MINERVA": ["reinforcement_learning", "graph", "sequential"],
        }
        
        if target_algorithm not in algorithm_features:
            return []
        
        target_features = set(algorithm_features[target_algorithm])
        related = []
        
        for algo, features in algorithm_features.items():
            if algo == target_algorithm:
                continue
            
            # 计算特征重叠度
            overlap = len(target_features & set(features))
            similarity = overlap / len(target_features | set(features))
            
            # 如果相似度超过阈值且算法存在于KG中
            if similarity > 0.3 and self._entity_exists(algo):
                related.append(algo)
        
        return related
    
    def discover_expansion_opportunities(self) -> Dict[str, List[str]]:
        """发现扩展机会"""
        opportunities = {
            "isolated_entities": [],  # 孤立实体
            "incomplete_algorithms": [],  # 缺少应用场景的算法
            "missing_paradigms": [],  # 缺少范式关系的算法
            "potential_tasks": []  # 潜在的新任务
        }
        
        if not self.connector.connect():
            return opportunities
            
        with self.connector.driver.session() as session:
            # 1. 找到孤立实体（度数为0或1）
            isolated_result = session.run("""
                MATCH (e:Entity)
                WHERE size([(e)--() | 1]) <= 1 AND e.type = 'Algorithm'
                RETURN e.name as name
            """)
            opportunities["isolated_entities"] = [r["name"] for r in isolated_result]
            
            # 2. 找到缺少应用场景的算法
            no_usage_result = session.run("""
                MATCH (a:Entity) 
                WHERE a.type = 'Algorithm' 
                AND NOT EXISTS {
                    MATCH (a)-[:USED_IN|:SOLVES]->(:Entity)
                }
                RETURN a.name as name
            """)
            opportunities["incomplete_algorithms"] = [r["name"] for r in no_usage_result]
            
            # 3. 找到缺少范式的算法
            no_paradigm_result = session.run("""
                MATCH (a:Entity)
                WHERE a.type = 'Algorithm'
                AND NOT EXISTS {
                    MATCH (a)-[:USES_PARADIGM]->(:Entity)
                }
                RETURN a.name as name
            """)
            opportunities["missing_paradigms"] = [r["name"] for r in no_paradigm_result]
        
        self.connector.disconnect()
        return opportunities
    
    def save_expansion_triples(self, triples: List[Dict], filename: str = "expansion_triples.csv"):
        """保存扩展三元组到CSV文件"""
        import pandas as pd
        
        if not triples:
            print("⚠️  没有新三元组需要保存")
            return
            
        df = pd.DataFrame(triples)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"💾 已保存 {len(triples)} 个扩展三元组到: {filename}")
        
        # 显示预览
        print("\n📋 扩展三元组预览:")
        for i, triple in enumerate(triples[:10]):  # 显示前10个
            print(f"   {i+1}. {triple['subject']} -[{triple['predicate']}]-> {triple['object']} (置信度: {triple['confidence']})")
        
        if len(triples) > 10:
            print(f"   ... 还有 {len(triples) - 10} 个三元组")
    
    def apply_expansion_to_kg(self, triples: List[Dict]):
        """将扩展三元组应用到知识图谱"""
        if not triples:
            print("⚠️  没有新三元组需要应用")
            return
            
        print(f"🚀 开始应用 {len(triples)} 个扩展三元组到知识图谱...")
        
        # 1. 先保存到CSV
        self.save_expansion_triples(triples, "kg_expansion_triples.csv")
        
        # 2. 使用动态主程序处理这些三元组
        print("📝 请运行以下命令应用扩展:")
        print("python dynamic_main.py kg_expansion_triples.csv --import-to-neo4j")
        print("\n🔍 或者如果想要完整重建（包含原始数据）:")
        print("python dynamic_main.py data/graph_algorithm_triples.csv kg_expansion_triples.csv --import-to-neo4j --neo4j-clear")

def main():
    print("=== 知识图谱智能扩展工具 ===\n")
    
    # 创建扩展工具
    expander = KGExpansionTool()
    
    # 加载现有KG
    expander.load_existing_kg()
    
    # 发现扩展机会
    print("\n🔍 分析扩展机会...")
    opportunities = expander.discover_expansion_opportunities()
    
    print("📊 发现的扩展机会:")
    for category, items in opportunities.items():
        if items:
            print(f"   {category}: {len(items)} 个")
            for item in items[:3]:  # 显示前3个
                print(f"      - {item}")
            if len(items) > 3:
                print(f"      ... 还有 {len(items) - 3} 个")
    
    # 扩展Ant Colony节点
    print(f"\n🐜 专门扩展 Ant_Colony 节点...")
    expansion_triples = expander.expand_ant_colony_node()
    
    # 应用扩展
    expander.apply_expansion_to_kg(expansion_triples)
    
    print(f"\n🎉 扩展完成！")
    print(f"📈 总计生成 {len(expansion_triples)} 个新三元组")
    print(f"🔗 新实体类型分布:")
    
    # 统计新实体类型
    entity_types = {}
    for triple in expansion_triples:
        if triple["predicate"] == "is_instance_of":
            entity_type = triple["object"]
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    
    for entity_type, count in entity_types.items():
        print(f"   {entity_type}: {count} 个")

if __name__ == "__main__":
    main() 