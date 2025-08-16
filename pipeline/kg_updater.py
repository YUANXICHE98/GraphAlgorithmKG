"""
知识图谱更新模块
负责将处理后的三元组数据更新到知识图谱中，并提供多种存储格式
"""

import json
import csv
import yaml
import pickle
from typing import Dict, List, Set, Optional, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime
import networkx as nx

# 使用动态本体系统的类
from ontology.managers.dynamic_schema import DynamicOntologyManager, EntityTypeConfig, RelationTypeConfig, Entity, Relation

@dataclass
class KGUpdateResult:
    """知识图谱更新结果"""
    success: bool
    updated_entities: int = 0
    updated_relations: int = 0
    new_entities: int = 0
    new_relations: int = 0
    errors: List[str] = None
    timestamp: str = None

class KnowledgeGraphUpdater:
    """知识图谱更新器"""
    
    def __init__(self, ontology_schema: DynamicOntologyManager, storage_path: str = "kg_storage"):
        self.schema = ontology_schema
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 知识图谱的图结构表示
        self.graph = nx.DiGraph()
        
        # 统计信息
        self.update_history = []
        
    def update_kg_from_triples(self, enriched_triples: List[Dict]) -> KGUpdateResult:
        """从填充的三元组更新知识图谱"""
        result = KGUpdateResult(
            success=False,
            errors=[],
            timestamp=datetime.now().isoformat()
        )
        
        try:
            # 备份当前状态
            self._backup_current_state()
            
            # 统计更新前的状态
            initial_entities = len(self.schema.entities)
            initial_relations = len(self.schema.relations)
            
            # 处理三元组
            for triple in enriched_triples:
                try:
                    self._process_triple(triple)
                except Exception as e:
                    result.errors.append(f"处理三元组 {triple} 时出错: {str(e)}")
            
            # 更新图结构
            self._update_graph_structure()
            
            # 计算更新统计
            result.new_entities = len(self.schema.entities) - initial_entities
            result.new_relations = len(self.schema.relations) - initial_relations
            result.updated_entities = len(self.schema.entities)
            result.updated_relations = len(self.schema.relations)
            
            # 持久化存储
            self._save_to_storage()
            
            # 生成可视化
            self._generate_visualizations()
            
            result.success = True
            self.update_history.append(result)
            
            print(f"知识图谱更新成功:")
            print(f"  新增实体: {result.new_entities}")
            print(f"  新增关系: {result.new_relations}")
            print(f"  总实体数: {result.updated_entities}")
            print(f"  总关系数: {result.updated_relations}")
            
        except Exception as e:
            result.errors.append(f"更新过程中发生严重错误: {str(e)}")
            result.success = False
            
        return result
    
    def _process_triple(self, triple: Dict):
        """处理单个三元组"""
        subject = triple["subject"]
        predicate = triple["predicate"] 
        obj = triple["object"]
        
        # 确保主语实体存在
        if subject not in self.schema.entities:
            subject_type = triple.get("subject_type", "Unknown")
            entity = Entity(
                name=subject,
                entity_type=subject_type,  # 使用推断的类型
                description=f"实体类型: {subject_type}",
                attributes={
                    "created_from": "kg_update",
                    "confidence": triple.get("confidence", 1.0),
                    "source": triple.get("source", "unknown"),
                    "inferred_type": subject_type
                }
            )
            self.schema.entities[subject] = entity
        
        # 确保宾语实体存在（如果宾语不是字面值）
        if obj not in self.schema.entities and not self._is_literal_value(obj):
            object_type = triple.get("object_type", "Unknown")
            entity = Entity(
                name=obj,
                entity_type=object_type,  # 使用推断的类型
                description=f"实体类型: {object_type}",
                attributes={
                    "created_from": "kg_update",
                    "confidence": triple.get("confidence", 1.0),
                    "source": triple.get("source", "unknown"),
                    "inferred_type": object_type
                }
            )
            self.schema.entities[obj] = entity
        
        # 添加关系
        try:
            relation = Relation(
                subject=subject,
                predicate=predicate,  # 直接使用字符串
                object=obj,
                confidence=triple.get("confidence", 1.0),
                source=triple.get("source", "unknown")
            )
            
            # 检查关系是否已存在
            existing_relation = self._find_existing_relation(relation)
            if existing_relation:
                # 更新置信度（取最大值）
                if relation.confidence > existing_relation.confidence:
                    existing_relation.confidence = relation.confidence
                    existing_relation.source = f"{existing_relation.source}, {relation.source}"
            else:
                self.schema.relations.append(relation)
                
        except Exception as e:
            # 记录错误但不中断处理
            print(f"警告: 处理关系时出错 '{predicate}' 在三元组 ({subject}, {predicate}, {obj}): {e}")
    
    def _is_literal_value(self, value: str) -> bool:
        """判断值是否为字面值（而非实体名称）"""
        # 简单的字面值识别：包含百分号、数字、或特定格式
        literal_patterns = [
            lambda v: '%' in v,  # 百分比
            lambda v: v.lower() in ['true', 'false'],  # 布尔值
            lambda v: v.replace('.', '').replace('-', '').isdigit(),  # 数字
            lambda v: len(v.split()) > 3,  # 长文本描述
        ]
        
        return any(pattern(value) for pattern in literal_patterns)
    
    def _find_existing_relation(self, relation: Relation) -> Optional[Relation]:
        """查找是否存在相同的关系"""
        for existing in self.schema.relations:
            if (existing.subject == relation.subject and 
                existing.predicate == relation.predicate and
                existing.object == relation.object):
                return existing
        return None
    
    def _update_graph_structure(self):
        """更新图结构表示"""
        self.graph.clear()
        
        # 添加实体作为节点
        for entity_name, entity in self.schema.entities.items():
            self.graph.add_node(
                entity_name,
                entity_type=entity.entity_type,  # 直接使用字符串
                description=entity.description or "",
                attributes=entity.attributes or {}
            )
        
        # 添加关系作为边
        for relation in self.schema.relations:
            # 只为非字面值的宾语创建边
            if not self._is_literal_value(relation.object):
                self.graph.add_edge(
                    relation.subject,
                    relation.object,
                    relation_type=relation.predicate,  # 直接使用字符串
                    confidence=relation.confidence,
                    source=relation.source or "unknown"
                )
            else:
                # 字面值作为节点属性
                if relation.subject in self.graph.nodes:
                    if 'literals' not in self.graph.nodes[relation.subject]:
                        self.graph.nodes[relation.subject]['literals'] = {}
                    self.graph.nodes[relation.subject]['literals'][relation.predicate] = relation.object
    
    def _backup_current_state(self):
        """备份当前状态"""
        backup_path = self.storage_path / "backups"
        backup_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"kg_backup_{timestamp}.pkl"
        
        with open(backup_file, 'wb') as f:
            pickle.dump({
                'schema': self.schema,
                'graph': self.graph,
                'timestamp': datetime.now().isoformat()
            }, f)
    
    def _save_to_storage(self):
        """保存到持久化存储"""
        # 保存为JSON格式
        self._save_as_json()
        
        # 保存为CSV格式
        self._save_as_csv()
        
        # 保存图结构
        self._save_graph_structure()
        
        # 保存统计信息
        self._save_statistics()
    
    def _save_as_json(self):
        """保存为JSON格式"""
        # 实体JSON
        entities_data = {}
        for name, entity in self.schema.entities.items():
            entities_data[name] = {
                "entity_type": entity.entity_type,  # 直接使用字符串
                "description": entity.description,
                "attributes": entity.attributes
            }
        
        with open(self.storage_path / "entities.json", 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, ensure_ascii=False, indent=2)
        
        # 关系JSON
        relations_data = []
        for relation in self.schema.relations:
            relations_data.append({
                "subject": relation.subject,
                "predicate": relation.predicate,  # 直接使用字符串
                "object": relation.object,
                "confidence": relation.confidence,
                "source": relation.source
            })
        
        with open(self.storage_path / "relations.json", 'w', encoding='utf-8') as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=2)
    
    def _save_as_csv(self):
        """保存为CSV格式"""
        # 实体CSV
        with open(self.storage_path / "entities.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "entity_type", "description", "attributes"])
            
            for name, entity in self.schema.entities.items():
                writer.writerow([
                    name,
                    entity.entity_type,  # 直接使用字符串
                    entity.description or "",
                    json.dumps(entity.attributes or {})
                ])
        
        # 关系CSV  
        with open(self.storage_path / "relations.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["subject", "predicate", "object", "confidence", "source"])
            
            for relation in self.schema.relations:
                writer.writerow([
                    relation.subject,
                    relation.predicate,  # 直接使用字符串
                    relation.object,
                    relation.confidence,
                    relation.source or ""
                ])
    
    def _save_graph_structure(self):
        """保存图结构"""
        # NetworkX格式
        nx.write_gexf(self.graph, self.storage_path / "knowledge_graph.gexf")
        nx.write_graphml(self.graph, self.storage_path / "knowledge_graph.graphml")
        
        # 简单的边列表格式
        with open(self.storage_path / "edges.txt", 'w', encoding='utf-8') as f:
            for subject, obj, data in self.graph.edges(data=True):
                relation_type = data.get('relation_type', 'unknown')
                confidence = data.get('confidence', 1.0)
                f.write(f"{subject}\t{relation_type}\t{obj}\t{confidence}\n")
    
    def _save_statistics(self):
        """保存统计信息"""
        stats = self.get_kg_statistics()
        
        with open(self.storage_path / "statistics.json", 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def _generate_visualizations(self):
        """生成可视化文件（为后续可视化工具准备）"""
        viz_path = self.storage_path / "visualizations"
        viz_path.mkdir(exist_ok=True)
        
        # 生成可视化配置文件
        viz_config = {
            "nodes": [],
            "edges": [],
            "categories": {}
        }
        
        # 按实体类型分类（使用字符串常量）
        type_colors = {
            "Paradigm": "#FF6B6B",
            "Algorithm": "#4ECDC4", 
            "Technique": "#45B7D1",
            "Framework": "#96CEB4",
            "Task": "#FFEAA7",
            "Metric": "#DDA0DD"
        }
        
        # 节点数据
        for name, entity in self.schema.entities.items():
            viz_config["nodes"].append({
                "id": name,
                "label": name,
                "category": entity.entity_type,  # 直接使用字符串
                "color": type_colors.get(entity.entity_type, "#999999"),
                "size": self.graph.degree(name) + 5 if name in self.graph else 5,
                "description": entity.description or ""
            })
        
        # 边数据
        for relation in self.schema.relations:
            if not self._is_literal_value(relation.object):
                viz_config["edges"].append({
                    "source": relation.subject,
                    "target": relation.object,
                    "label": relation.predicate,  # 直接使用字符串
                    "weight": relation.confidence,
                    "color": "#999999"
                })
        
        # 类别配置
        viz_config["categories"] = {
            entity_type: {
                "color": color,
                "description": f"{entity_type} entities"
            }
            for entity_type, color in type_colors.items()
        }
        
        with open(viz_path / "graph_data.json", 'w', encoding='utf-8') as f:
            json.dump(viz_config, f, ensure_ascii=False, indent=2)
    
    def get_kg_statistics(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_entities": len(self.schema.entities),
            "total_relations": len(self.schema.relations),
            "entities_by_type": {},
            "relations_by_type": {},
            "graph_metrics": {}
        }
        
        # 按类型统计实体
        for entity in self.schema.entities.values():
            entity_type = entity.entity_type  # 直接使用字符串
            stats["entities_by_type"][entity_type] = stats["entities_by_type"].get(entity_type, 0) + 1
        
        # 按类型统计关系
        for relation in self.schema.relations:
            relation_type = relation.predicate  # 直接使用字符串
            stats["relations_by_type"][relation_type] = stats["relations_by_type"].get(relation_type, 0) + 1
        
        # 图指标
        if self.graph.number_of_nodes() > 0:
            stats["graph_metrics"] = {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
                "density": nx.density(self.graph),
                "is_connected": nx.is_weakly_connected(self.graph),
                "average_clustering": nx.average_clustering(self.graph.to_undirected())
            }
            
            # 中心性指标
            if self.graph.number_of_nodes() > 1:
                degree_centrality = nx.degree_centrality(self.graph)
                stats["top_central_nodes"] = sorted(
                    degree_centrality.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10]
        
        return stats
    
    def query_kg(self, query_type: str, **kwargs) -> List[Dict]:
        """查询知识图谱"""
        results = []
        
        if query_type == "entity_by_type":
            entity_type = kwargs.get("entity_type")
            if entity_type:
                results = [
                    {"name": name, "entity": asdict(entity)}
                    for name, entity in self.schema.entities.items()
                    if entity.entity_type == entity_type  # 直接比较字符串
                ]
        
        elif query_type == "relations_of_entity":
            entity_name = kwargs.get("entity_name")
            if entity_name:
                results = [
                    {
                        "subject": rel.subject,
                        "predicate": rel.predicate,  # 直接使用字符串
                        "object": rel.object,
                        "confidence": rel.confidence
                    }
                    for rel in self.schema.relations
                    if rel.subject == entity_name or rel.object == entity_name
                ]
        
        elif query_type == "shortest_path":
            start = kwargs.get("start")
            end = kwargs.get("end")
            if start and end and start in self.graph and end in self.graph:
                try:
                    path = nx.shortest_path(self.graph, start, end)
                    results = [{"path": path, "length": len(path) - 1}]
                except nx.NetworkXNoPath:
                    results = [{"path": None, "message": "No path found"}]
        
        return results

# 注意: 此模块现在与动态本体系统集成使用
# 完整的使用示例请参考 dynamic_main.py 