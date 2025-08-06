"""
Neo4j知识图谱连接器
将动态知识图谱数据导入到Neo4j数据库
"""

from typing import List, Dict, Any, Optional
import json
from dataclasses import asdict
import logging

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

class Neo4jConnector:
    """Neo4j数据库连接器"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "yuanxi"):
        if not NEO4J_AVAILABLE:
            raise ImportError("请安装neo4j驱动: pip install neo4j")
        
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        """连接到Neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # 测试连接
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            self.logger.info("✅ 成功连接到Neo4j数据库")
            return True
        except Exception as e:
            self.logger.error(f"❌ 连接Neo4j失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.driver:
            self.driver.close()
            self.logger.info("🔌 已断开Neo4j连接")
    
    def clear_database(self):
        """清空数据库（谨慎使用）"""
        with self.driver.session() as session:
            # 删除所有关系和节点
            session.run("MATCH (n) DETACH DELETE n")
            
            # 删除所有约束（如果存在）
            try:
                constraints_result = session.run("SHOW CONSTRAINTS")
                for record in constraints_result:
                    constraint_name = record.get("name")
                    if constraint_name:
                        session.run(f"DROP CONSTRAINT {constraint_name}")
            except Exception as e:
                self.logger.warning(f"删除约束时出错（可能不存在）: {e}")
            
            # 删除所有索引
            try:
                indexes_result = session.run("SHOW INDEXES")
                for record in indexes_result:
                    index_name = record.get("name") 
                    if index_name and "btree" not in index_name.lower():  # 保留btree基础索引
                        session.run(f"DROP INDEX {index_name}")
            except Exception as e:
                self.logger.warning(f"删除索引时出错（可能不存在）: {e}")
                
            self.logger.info("🗑️ 已清空Neo4j数据库（包括约束和索引）")
    
    def create_constraints(self):
        """创建约束和索引"""
        with self.driver.session() as session:
            # 创建唯一性约束
            try:
                session.run("CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")
                self.logger.info("✅ 创建实体名称唯一约束")
            except Exception as e:
                self.logger.warning(f"创建唯一约束失败（可能已存在）: {e}")
            
            # 创建索引
            indexes = [
                ("CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)", "实体类型索引"),
                ("CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)", "实体名称索引"),
                ("CREATE INDEX relation_type_index IF NOT EXISTS FOR ()-[r:RELATED]-() ON (r.type)", "关系类型索引")
            ]
            
            for index_query, description in indexes:
                try:
                    session.run(index_query)
                    self.logger.info(f"✅ 创建{description}")
                except Exception as e:
                    if "already exists" not in str(e).lower() and "equivalent" not in str(e).lower():
                        self.logger.warning(f"创建{description}失败: {e}")
        
        self.logger.info("📋 数据库约束和索引设置完成")
    
    def import_entities(self, entities: Dict[str, Any]) -> int:
        """导入实体到Neo4j"""
        count = 0
        with self.driver.session() as session:
            for entity_name, entity_data in entities.items():
                # 如果entity_data是Entity对象，转换为字典
                if hasattr(entity_data, '__dict__'):
                    entity_dict = asdict(entity_data)
                else:
                    entity_dict = entity_data
                
                entity_type = entity_dict.get('entity_type', 'Unknown')
                
                # 创建实体节点，使用实体类型作为额外标签，name作为主显示属性
                cypher = f"""
                MERGE (e:Entity:`{entity_type}` {{name: $name}})
                SET e.type = $type,
                    e.description = $description,
                    e.confidence = $confidence,
                    e.created_at = $created_at,
                    e.attributes = $attributes,
                    e.display_name = $name
                """
                
                try:
                    session.run(cypher, 
                        name=entity_name,
                        type=entity_type,
                        description=entity_dict.get('description', ''),
                        confidence=float(entity_dict.get('confidence', 1.0)),
                        created_at=entity_dict.get('created_at', ''),
                        attributes=json.dumps(entity_dict.get('attributes', {}))
                    )
                    count += 1
                except Exception as e:
                    # 如果实体类型作为标签有问题，回退到基本创建
                    self.logger.warning(f"使用类型标签创建实体失败，回退基本创建: {e}")
                    basic_cypher = """
                    MERGE (e:Entity {name: $name})
                    SET e.type = $type,
                        e.description = $description,
                        e.confidence = $confidence,
                        e.created_at = $created_at,
                        e.attributes = $attributes,
                        e.display_name = $name
                    """
                    session.run(basic_cypher, 
                        name=entity_name,
                        type=entity_type,
                        description=entity_dict.get('description', ''),
                        confidence=float(entity_dict.get('confidence', 1.0)),
                        created_at=entity_dict.get('created_at', ''),
                        attributes=json.dumps(entity_dict.get('attributes', {}))
                    )
                    count += 1
        
        self.logger.info(f"📊 已导入 {count} 个实体")
        return count
    
    def import_relations(self, relations: List[Any]) -> int:
        """导入关系到Neo4j"""
        count = 0
        literal_count = 0
        relation_count = 0
        
        with self.driver.session() as session:
            for relation in relations:
                # 如果relation是Relation对象，转换为字典
                if hasattr(relation, '__dict__'):
                    relation_dict = asdict(relation)
                else:
                    relation_dict = relation
                
                subject = relation_dict['subject']
                predicate = relation_dict['predicate']
                obj = relation_dict['object']
                confidence = float(relation_dict.get('confidence', 1.0))
                source = relation_dict.get('source', '')
                
                # 检查是否为字面值关系
                if self._is_literal_value(obj):
                    # 字面值作为实体属性
                    cypher = f"""
                    MATCH (e:Entity {{name: $subject}})
                    SET e.`{predicate}` = $object
                    """
                    try:
                        session.run(cypher,
                            subject=subject,
                            object=obj
                        )
                        literal_count += 1
                    except Exception as e:
                        self.logger.warning(f"设置字面值属性失败 {subject}.{predicate}={obj}: {e}")
                else:
                    # 创建实体间关系 - 先确保两个实体都存在
                    # 检查subject是否存在
                    subject_check = session.run("MATCH (s:Entity {name: $name}) RETURN count(s) as count", name=subject).single()
                    if subject_check["count"] == 0:
                        self.logger.warning(f"主语实体不存在，跳过关系: {subject} -[{predicate}]-> {obj}")
                        continue
                    
                    # 检查object是否存在    
                    object_check = session.run("MATCH (o:Entity {name: $name}) RETURN count(o) as count", name=obj).single()
                    if object_check["count"] == 0:
                        self.logger.warning(f"宾语实体不存在，跳过关系: {subject} -[{predicate}]-> {obj}")
                        continue
                    
                    # 使用具体关系类型作为关系标签，转换为Neo4j兼容的标签格式
                    neo4j_relation_type = self._normalize_relation_type_for_neo4j(predicate)
                    
                    # 创建关系 - 使用动态关系类型
                    cypher = f"""
                    MATCH (s:Entity {{name: $subject}})
                    MATCH (o:Entity {{name: $object}})
                    MERGE (s)-[r:`{neo4j_relation_type}`]->(o)
                    SET r.type = $predicate,
                        r.confidence = $confidence,
                        r.source = $source,
                        r.created_at = datetime()
                    """
                    try:
                        session.run(cypher,
                            subject=subject,
                            object=obj,
                            predicate=predicate,
                            confidence=confidence,
                            source=source
                        )
                        relation_count += 1
                    except Exception as e:
                        # 如果动态关系类型失败，回退到RELATED
                        self.logger.warning(f"使用动态关系类型失败，回退到RELATED: {e}")
                        fallback_cypher = """
                        MATCH (s:Entity {name: $subject})
                        MATCH (o:Entity {name: $object})
                        MERGE (s)-[r:RELATED]->(o)
                        SET r.type = $predicate,
                            r.confidence = $confidence,
                            r.source = $source,
                            r.created_at = datetime()
                        """
                        session.run(fallback_cypher,
                            subject=subject,
                            object=obj,
                            predicate=predicate,
                            confidence=confidence,
                            source=source
                        )
                        relation_count += 1
                
                count += 1
        
        self.logger.info(f"🔗 已处理 {count} 个关系:")
        self.logger.info(f"   - 实体间关系: {relation_count} 个")
        self.logger.info(f"   - 字面值属性: {literal_count} 个")
        return count
    
    def _is_literal_value(self, value: str) -> bool:
        """判断值是否为字面值"""
        literal_patterns = [
            lambda v: '%' in v,
            lambda v: v.lower() in ['true', 'false'],
            lambda v: v.replace('.', '').replace('-', '').isdigit(),
            lambda v: len(v.split()) > 3
        ]
        return any(pattern(value) for pattern in literal_patterns)
    
    def _normalize_relation_type_for_neo4j(self, predicate: str) -> str:
        """将谓词转换为Neo4j兼容的关系类型标签"""
        # Neo4j关系类型规则：
        # 1. 只能包含字母、数字、下划线
        # 2. 不能以数字开头
        # 3. 通常使用大写
        
        # 转换为大写并替换特殊字符
        neo4j_type = predicate.upper()
        neo4j_type = neo4j_type.replace('-', '_')
        neo4j_type = neo4j_type.replace(' ', '_')
        
        # 移除其他特殊字符
        import re
        neo4j_type = re.sub(r'[^A-Z0-9_]', '', neo4j_type)
        
        # 确保不以数字开头
        if neo4j_type and neo4j_type[0].isdigit():
            neo4j_type = 'REL_' + neo4j_type
        
        # 如果为空，使用默认值
        if not neo4j_type:
            neo4j_type = 'RELATED'
            
        return neo4j_type
    
    def query_entities_by_type(self, entity_type: str) -> List[Dict]:
        """按类型查询实体"""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (e:Entity) WHERE e.type = $type RETURN e",
                type=entity_type
            )
            return [record["e"] for record in result]
    
    def query_entity_relations(self, entity_name: str) -> List[Dict]:
        """查询实体的所有关系"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Entity {name: $name})
                OPTIONAL MATCH (e)-[r:RELATED]-(other:Entity)
                RETURN e, r, other
            """, name=entity_name)
            
            relations = []
            for record in result:
                if record["r"] and record["other"]:
                    relations.append({
                        "subject": record["e"]["name"],
                        "predicate": record["r"]["type"],
                        "object": record["other"]["name"],
                        "confidence": record["r"].get("confidence", 1.0)
                    })
            return relations
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """获取图统计信息"""
        with self.driver.session() as session:
            # 节点统计
            nodes_result = session.run("MATCH (n:Entity) RETURN count(n) as count")
            nodes_count = nodes_result.single()["count"]
            
            # 关系统计 - 修复：统计所有关系，不仅仅是RELATED
            edges_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            edges_count = edges_result.single()["count"]
            
            # 按类型统计实体
            type_result = session.run("""
                MATCH (n:Entity) 
                RETURN n.type as type, count(n) as count 
                ORDER BY count DESC
            """)
            entity_types = {record["type"]: record["count"] for record in type_result}
            
            # 按类型统计关系 - 修复：统计所有关系类型
            rel_type_result = session.run("""
                MATCH ()-[r]->() 
                RETURN type(r) as neo4j_type, r.type as original_type, count(r) as count 
                ORDER BY count DESC
            """)
            relation_types = {}
            for record in rel_type_result:
                neo4j_type = record["neo4j_type"]
                original_type = record["original_type"] or neo4j_type
                count = record["count"]
                relation_types[f"{original_type} ({neo4j_type})"] = count
            
            return {
                "nodes": nodes_count,
                "edges": edges_count,
                "entity_types": entity_types,
                "relation_types": relation_types
            }

    def export_database_to_files(self, output_dir: str = "neo4j_export") -> bool:
        """导出Neo4j数据库内容到文件"""
        try:
            from pathlib import Path
            import json
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            with self.driver.session() as session:
                # 导出实体
                entities_result = session.run("""
                    MATCH (e:Entity)
                    RETURN e.name as name, e.type as type, e.description as description,
                           e.confidence as confidence, e.created_at as created_at,
                           e.attributes as attributes
                """)
                
                entities = []
                for record in entities_result:
                    entity = {
                        "name": record["name"],
                        "entity_type": record["type"],
                        "description": record["description"] or "",
                        "confidence": float(record["confidence"]) if record["confidence"] else 1.0,
                        "created_at": record["created_at"] or "",
                        "attributes": json.loads(record["attributes"]) if record["attributes"] else {}
                    }
                    entities.append(entity)
                
                # 导出关系
                relations_result = session.run("""
                    MATCH (s:Entity)-[r:RELATED]->(o:Entity)
                    RETURN s.name as subject, r.type as predicate, o.name as object,
                           r.confidence as confidence, r.source as source
                """)
                
                relations = []
                for record in relations_result:
                    relation = {
                        "subject": record["subject"],
                        "predicate": record["predicate"],
                        "object": record["object"],
                        "confidence": float(record["confidence"]) if record["confidence"] else 1.0,
                        "source": record["source"] or ""
                    }
                    relations.append(relation)
                
                # 导出字面值属性关系
                literal_relations = []
                for entity in entities:
                    entity_name = entity["name"]
                    # 查询该实体的所有属性
                    props_result = session.run(f"""
                        MATCH (e:Entity {{name: $name}})
                        RETURN properties(e) as props
                    """, name=entity_name)
                    
                    props_record = props_result.single()
                    if props_record and props_record["props"]:
                        props = props_record["props"]
                        # 排除标准属性，只保留关系属性
                        standard_props = {"name", "type", "description", "confidence", "created_at", "attributes"}
                        for key, value in props.items():
                            if key not in standard_props and value is not None:
                                literal_relations.append({
                                    "subject": entity_name,
                                    "predicate": key,
                                    "object": str(value),
                                    "confidence": 1.0,
                                    "source": "literal_property"
                                })
                
                # 合并所有关系
                all_relations = relations + literal_relations
                
                # 保存到文件
                with open(output_path / "entities.json", 'w', encoding='utf-8') as f:
                    json.dump(entities, f, ensure_ascii=False, indent=2)
                
                with open(output_path / "relations.json", 'w', encoding='utf-8') as f:
                    json.dump(all_relations, f, ensure_ascii=False, indent=2)
                
                # 生成CSV格式
                import pandas as pd
                
                # 实体CSV
                entities_df = pd.DataFrame(entities)
                entities_df.to_csv(output_path / "entities.csv", index=False, encoding='utf-8')
                
                # 关系CSV
                relations_df = pd.DataFrame(all_relations)
                relations_df.to_csv(output_path / "relations.csv", index=False, encoding='utf-8')
                
                # 生成三元组CSV（与dynamic_kg_storage格式兼容）
                triples = []
                for rel in all_relations:
                    triples.append({
                        "subject": rel["subject"],
                        "predicate": rel["predicate"],
                        "object": rel["object"],
                        "confidence": rel["confidence"],
                        "source": rel["source"]
                    })
                
                triples_df = pd.DataFrame(triples)
                triples_df.to_csv(output_path / "triples.csv", index=False, encoding='utf-8')
                
                self.logger.info(f"📤 数据库内容已导出到: {output_path}")
                self.logger.info(f"   实体: {len(entities)} 个")
                self.logger.info(f"   关系: {len(all_relations)} 个")
                
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 导出失败: {e}")
            return False

    def import_from_storage_files(self, storage_path: str = "dynamic_kg_storage", 
                                 clear_existing: bool = False) -> bool:
        """从dynamic_kg_storage文件导入数据到Neo4j"""
        try:
            from pathlib import Path
            import json
            
            storage_dir = Path(storage_path)
            if not storage_dir.exists():
                self.logger.error(f"❌ 存储目录不存在: {storage_path}")
                return False
            
            if clear_existing:
                self.clear_database()
            
            self.create_constraints()
            
            # 导入实体
            entities_file = storage_dir / "entities.json"
            if entities_file.exists():
                with open(entities_file, 'r', encoding='utf-8') as f:
                    entities_data = json.load(f)
                
                # 转换为字典格式
                entities_dict = {}
                for entity in entities_data:
                    entities_dict[entity["name"]] = entity
                
                entity_count = self.import_entities(entities_dict)
            else:
                self.logger.warning("⚠️  未找到entities.json文件")
                entity_count = 0
            
            # 导入关系
            relations_file = storage_dir / "relations.json"
            if relations_file.exists():
                with open(relations_file, 'r', encoding='utf-8') as f:
                    relations_data = json.load(f)
                
                relation_count = self.import_relations(relations_data)
            else:
                self.logger.warning("⚠️  未找到relations.json文件")
                relation_count = 0
            
            self.logger.info(f"🎉 成功从存储文件导入:")
            self.logger.info(f"   实体: {entity_count} 个")
            self.logger.info(f"   关系: {relation_count} 个")
            
            # 显示最终统计
            stats = self.get_graph_statistics()
            self.logger.info(f"📊 导入后图统计:")
            self.logger.info(f"   节点: {stats['nodes']} 个")
            self.logger.info(f"   边: {stats['edges']} 个")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 从存储文件导入失败: {e}")
            return False

def import_kg_to_neo4j(entities: Dict, relations: List, 
                       uri: str = "bolt://localhost:7687", 
                       user: str = "neo4j", 
                       password: str = "yuanxi",
                       clear_existing: bool = False) -> bool:
    """
    便捷函数：将知识图谱导入到Neo4j
    
    Args:
        entities: 实体字典
        relations: 关系列表
        uri: Neo4j URI
        user: 用户名
        password: 密码
        clear_existing: 是否清空现有数据
    
    Returns:
        bool: 导入是否成功
    """
    connector = Neo4jConnector(uri, user, password)
    
    try:
        if not connector.connect():
            return False
        
        if clear_existing:
            connector.clear_database()
        
        connector.create_constraints()
        
        entity_count = connector.import_entities(entities)
        relation_count = connector.import_relations(relations)
        
        print(f"🎉 成功导入到Neo4j:")
        print(f"   实体: {entity_count} 个")
        print(f"   关系: {relation_count} 个")
        
        # 显示统计信息
        stats = connector.get_graph_statistics()
        print(f"📊 图统计:")
        print(f"   节点: {stats['nodes']} 个")
        print(f"   边: {stats['edges']} 个")
        print(f"   实体类型: {stats['entity_types']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False
    finally:
        connector.disconnect()

def export_neo4j_to_files(output_dir: str = "neo4j_export",
                         uri: str = "bolt://localhost:7687", 
                         user: str = "neo4j", 
                         password: str = "yuanxi") -> bool:
    """
    便捷函数：导出Neo4j数据库内容到文件
    
    Args:
        output_dir: 输出目录
        uri: Neo4j URI
        user: 用户名
        password: 密码
    
    Returns:
        bool: 导出是否成功
    """
    connector = Neo4jConnector(uri, user, password)
    
    try:
        if not connector.connect():
            return False
        
        success = connector.export_database_to_files(output_dir)
        
        if success:
            print(f"📤 Neo4j数据库内容已导出到: {output_dir}")
        else:
            print("❌ 导出失败")
            
        return success
        
    except Exception as e:
        print(f"❌ 导出过程出错: {e}")
        return False
    finally:
        connector.disconnect()

def import_storage_to_neo4j(storage_path: str = "dynamic_kg_storage",
                           uri: str = "bolt://localhost:7687", 
                           user: str = "neo4j", 
                           password: str = "yuanxi",
                           clear_existing: bool = False) -> bool:
    """
    便捷函数：从dynamic_kg_storage导入数据到Neo4j
    
    Args:
        storage_path: 存储路径
        uri: Neo4j URI
        user: 用户名
        password: 密码
        clear_existing: 是否清空现有数据
    
    Returns:
        bool: 导入是否成功
    """
    connector = Neo4jConnector(uri, user, password)
    
    try:
        if not connector.connect():
            return False
        
        success = connector.import_from_storage_files(storage_path, clear_existing)
        
        if success:
            print(f"📥 存储文件已导入到Neo4j数据库")
        else:
            print("❌ 导入失败")
            
        return success
        
    except Exception as e:
        print(f"❌ 导入过程出错: {e}")
        return False
    finally:
        connector.disconnect()

# 使用示例
if __name__ == "__main__":
    # 测试连接
    connector = Neo4jConnector(password="yuanxi")  # 使用你的密码
    if connector.connect():
        print("✅ Neo4j连接测试成功!")
        stats = connector.get_graph_statistics()
        print(f"当前图统计: {stats}")
        connector.disconnect()
    else:
        print("❌ Neo4j连接测试失败!") 