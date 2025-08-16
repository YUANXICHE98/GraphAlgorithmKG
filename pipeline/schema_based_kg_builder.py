"""
基于Schema的知识图谱构建器
支持JSON格式的结构化知识图谱构建，包含完整的实体属性和关系信息
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from ontology.managers.schema_detector import SchemaDetector
from ontology.managers.dynamic_schema import DynamicOntologyManager
from pipeline.enhanced_entity_inferer import EnhancedEntityTypeInferer
from pipeline.hybrid_triple_extractor import HybridTripleExtractor
from pipeline.session_manager import session_manager

@dataclass
class KGEntity:
    """知识图谱实体"""
    id: str
    name: str
    type: str
    properties: Dict[str, Any]
    confidence: float
    source: str
    created_at: str
    schema: str

@dataclass
class KGRelation:
    """知识图谱关系"""
    id: str
    subject_id: str
    subject_name: str
    predicate: str
    object_id: str
    object_name: str
    properties: Dict[str, Any]
    confidence: float
    source: str
    created_at: str
    schema: str

@dataclass
class KnowledgeGraph:
    """完整的知识图谱"""
    metadata: Dict[str, Any]
    entities: List[KGEntity]
    relations: List[KGRelation]
    statistics: Dict[str, Any]

class SchemaBasedKGBuilder:
    """基于Schema的知识图谱构建器"""
    
    def __init__(self):
        self.schema_detector = SchemaDetector()
        self.entity_inferer = EnhancedEntityTypeInferer()
        self.hybrid_extractor = None  # 延迟初始化

        # 实体ID映射
        self.entity_id_map = {}
        
    def build_knowledge_graph(self, document_path: str,
                            output_path: Optional[str] = None) -> KnowledgeGraph:
        """
        从文档构建完整的知识图谱

        Args:
            document_path: 文档路径
            output_path: 输出路径（可选）

        Returns:
            完整的知识图谱对象
        """
        start_time = time.time()

        print(f"\n🏗️ 开始构建知识图谱")
        print(f"📄 输入文档: {document_path}")
        print("=" * 80)

        # 开始会话
        session_id = session_manager.start_session(document_path)

        # 1. 读取文档
        print(f"\n📖 步骤1: 读取文档内容")
        document_content = self._load_document(document_path)
        print(f"   📝 文档长度: {len(document_content)} 字符")
        print(f"   📋 文档预览: {document_content[:200]}...")

        # 保存文档输入阶段
        session_manager.save_stage_result(
            "document_input",
            {
                "document_path": document_path,
                "content": document_content,
                "content_length": len(document_content)
            },
            "原始文档输入和内容解析"
        )

        # 2. 检测Schema
        print(f"\n🔍 步骤2: Schema检测")
        schema_results = self.schema_detector.detect_schema(document_content, use_llm=True)

        print(f"   🎯 候选Schema列表:")
        for i, result in enumerate(schema_results, 1):
            print(f"      {i}. {result.schema_file} (置信度: {result.confidence:.3f}, 方法: {result.method})")
            print(f"         证据: {', '.join(result.evidence[:3])}")

        best_schema = self.schema_detector.get_best_schema(document_content)
        if not best_schema:
            raise ValueError("无法检测到合适的Schema")

        print(f"   ✅ 选择Schema: {best_schema}")

        # 保存Schema检测阶段
        session_manager.save_stage_result(
            "schema_detection",
            {
                "candidates": [
                    {
                        "schema_file": result.schema_file,
                        "confidence": result.confidence,
                        "method": result.method,
                        "evidence": result.evidence
                    } for result in schema_results
                ],
                "selected_schema": best_schema
            },
            f"Schema检测和选择，最终选择: {best_schema}"
        )

        # 3. 切换到对应的Schema
        print(f"\n⚙️ 步骤3: 切换Schema配置")
        self._switch_to_schema(best_schema)

        # 显示Schema信息
        schema_info = {
            'name': self.entity_inferer.ontology_manager.metadata.get('name', '未知Schema'),
            'entity_types': list(self.entity_inferer.ontology_manager.entity_types.keys()),
            'relation_types': list(self.entity_inferer.ontology_manager.relation_types.keys())
        }
        print(f"   📋 Schema名称: {schema_info['name']}")
        print(f"   🏷️ 实体类型 ({len(schema_info['entity_types'])}): {', '.join(schema_info['entity_types'][:5])}{'...' if len(schema_info['entity_types']) > 5 else ''}")
        print(f"   🔗 关系类型 ({len(schema_info['relation_types'])}): {', '.join(schema_info['relation_types'][:5])}{'...' if len(schema_info['relation_types']) > 5 else ''}")

        # 4. 混合三元组抽取（规则+LLM）
        print(f"\n🔄 步骤4: 混合三元组抽取")
        extraction_result = self._extract_triples_hybrid(document_content)
        triples = extraction_result.triples

        print(f"   📊 抽取统计:")
        print(f"      总三元组: {len(triples)} 个")
        print(f"      规则抽取: {extraction_result.rule_count} 个")
        print(f"      LLM抽取: {extraction_result.llm_count} 个")
        print(f"      使用方法: {', '.join(extraction_result.methods_used)}")

        if triples:
            print(f"   📋 三元组示例:")
            for i, triple in enumerate(triples[:3], 1):
                method = triple.get('method', 'unknown')
                print(f"      {i}. ({triple['subject']}, {triple['predicate']}, {triple['object']}) - 置信度: {triple.get('confidence', 0.8):.2f} [{method}]")

        # 保存三元组抽取阶段
        session_manager.save_stage_result(
            "triple_extraction",
            {
                "extraction_method": "hybrid",
                "rule_extraction_count": extraction_result.rule_count,
                "llm_extraction_count": extraction_result.llm_count,
                "methods_used": extraction_result.methods_used,
                "extraction_time": extraction_result.total_time,
                "triples": triples
            },
            f"混合三元组抽取，规则:{extraction_result.rule_count}个，LLM:{extraction_result.llm_count}个"
        )

        # 5. 构建实体和关系
        print(f"\n🏗️ 步骤5: 构建实体和关系对象")
        entities, relations = self._build_entities_and_relations(triples, best_schema, document_path, extraction_result)
        print(f"   🏷️ 生成实体: {len(entities)} 个")
        print(f"   🔗 生成关系: {len(relations)} 个")

        # 显示实体类型分布
        entity_type_counts = {}
        for entity in entities:
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1

        print(f"   📊 实体类型分布:")
        for entity_type, count in sorted(entity_type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"      {entity_type}: {count} 个")

        # 保存实体推断阶段
        session_manager.save_stage_result(
            "entity_inference",
            {
                "entities": [asdict(entity) for entity in entities],
                "relations": [asdict(relation) for relation in relations],
                "entity_type_distribution": entity_type_counts
            },
            f"实体推断和关系构建，生成{len(entities)}个实体，{len(relations)}个关系"
        )

        # 6. 创建知识图谱
        print(f"\n📦 步骤6: 生成知识图谱")
        kg = self._create_knowledge_graph(entities, relations, best_schema, document_path, start_time, extraction_result)

        # 7. 保存结果
        print(f"\n💾 步骤7: 保存知识图谱")

        # 保存最终KG到会话和输出目录
        kg_dict = {
            'metadata': kg.metadata,
            'entities': [asdict(entity) for entity in kg.entities],
            'relations': [asdict(relation) for relation in kg.relations],
            'statistics': kg.statistics
        }

        # 保存到会话目录
        session_manager.save_stage_result(
            "final_kg",
            kg_dict,
            f"最终知识图谱，包含{kg.statistics['total_entities']}个实体，{kg.statistics['total_relations']}个关系"
        )

        # 计算处理时间
        processing_time = time.time() - start_time

        # 保存到输出目录
        analysis_data = {
            "processing_summary": {
                "total_time": processing_time,
                "schema_used": best_schema,
                "extraction_methods": extraction_result.methods_used,
                "quality_metrics": {
                    "entity_count": kg.statistics['total_entities'],
                    "relation_count": kg.statistics['total_relations'],
                    "avg_entity_confidence": kg.statistics['average_entity_confidence'],
                    "avg_relation_confidence": kg.statistics['average_relation_confidence']
                }
            }
        }

        saved_files = session_manager.save_final_result(kg_dict, analysis_data, best_schema)

        # 兼容旧接口
        if output_path:
            self._save_knowledge_graph(kg, output_path)
            print(f"   📁 兼容保存: {output_path}")

        # 结束会话
        final_stats = {
            "total_entities": kg.statistics['total_entities'],
            "total_relations": kg.statistics['total_relations'],
            "processing_time": processing_time,
            "schema_used": best_schema,
            "extraction_methods": extraction_result.methods_used if extraction_result else []
        }
        session_manager.end_session(final_stats)

        print(f"\n✅ 知识图谱构建完成")
        print(f"   ⏱️ 总耗时: {processing_time:.2f}s")
        print(f"   📊 最终统计: {kg.statistics['total_entities']} 实体, {kg.statistics['total_relations']} 关系")
        print(f"   📁 会话文件: {saved_files}")
        print("=" * 80)

        return kg
    
    def _load_document(self, document_path: str) -> str:
        """加载文档内容"""
        path = Path(document_path)
        
        if path.suffix.lower() == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('text_content', str(data))
        else:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _switch_to_schema(self, schema_file: str):
        """切换到指定Schema"""
        # 处理不同的Schema路径格式
        if schema_file == "../schemas/general/schema_config.yaml":
            schema_path = "ontology/schemas/general/schema_config.yaml"
        elif schema_file == "spatiotemporal_schema.yaml":
            schema_path = "ontology/schemas/spatiotemporal/spatiotemporal_schema.yaml"
        elif schema_file.startswith("ontology/"):
            schema_path = schema_file
        else:
            schema_path = schema_file

        self.entity_inferer.switch_domain(schema_path)
        self.current_schema = schema_file

        # 初始化混合抽取器
        self.hybrid_extractor = HybridTripleExtractor(self.entity_inferer.ontology_manager)
    
    def _extract_triples_hybrid(self, text: str):
        """使用混合方法抽取三元组"""
        if not self.hybrid_extractor:
            raise ValueError("混合抽取器未初始化，请先切换Schema")

        # 使用混合抽取器
        extraction_result = self.hybrid_extractor.extract_triples(text)

        # 验证三元组
        validated_triples = []
        for triple in extraction_result.triples:
            if self._validate_triple(triple):
                validated_triples.append(triple)

        # 更新结果
        extraction_result.triples = validated_triples

        return extraction_result
    
    def _validate_triple(self, triple: Dict[str, Any]) -> bool:
        """验证三元组的有效性"""
        required_fields = ['subject', 'predicate', 'object']

        # 检查必需字段
        for field in required_fields:
            if field not in triple or not triple[field]:
                print(f"⚠️ 三元组缺少字段 {field}: {triple}")
                return False

        predicate = triple['predicate']
        available_relations = list(self.entity_inferer.ontology_manager.relation_types.keys())

        # 检查关系类型是否在Schema中定义
        if predicate not in available_relations:
            # 尝试关系映射和修复
            mapped_predicate = self._map_relation_to_schema(predicate, available_relations)
            if mapped_predicate:
                print(f"🔄 关系映射: '{predicate}' -> '{mapped_predicate}'")
                triple['predicate'] = mapped_predicate
                triple['original_predicate'] = predicate  # 保留原始关系
            else:
                print(f"❌ 关系类型 '{predicate}' 无法映射到Schema")
                print(f"   可用关系类型: {available_relations[:5]}{'...' if len(available_relations) > 5 else ''}")
                return False

        print(f"✅ 三元组验证通过: ({triple['subject']}, {triple['predicate']}, {triple['object']})")
        return True

    def _map_relation_to_schema(self, predicate: str, available_relations: List[str]) -> Optional[str]:
        """将关系映射到Schema中的合法关系"""
        predicate_lower = predicate.lower()

        # 关系映射规则
        relation_mappings = {
            # 通用映射
            'contains': 'implements',
            'locatedat': 'used_in',
            'located_at': 'used_in',
            'includes': 'implements',
            'has': 'has_algorithm',
            'uses': 'uses_paradigm',

            # 时空映射
            'hasstarttime': 'hasStartTime',
            'hasendtime': 'hasEndTime',
            'hasduration': 'hasDuration',
            'hascondition': 'hasCondition',
            'resultsin': 'resultsIn',
            'causes': 'resultsIn',
            'triggers': 'resultsIn',

            # 实例关系映射
            'is_a': 'is_instance_of',
            'isa': 'is_instance_of',
            'instanceof': 'is_instance_of',
            'type_of': 'is_instance_of'
        }

        # 直接映射
        if predicate_lower in relation_mappings:
            mapped = relation_mappings[predicate_lower]
            if mapped in available_relations:
                return mapped

        # 模糊匹配
        for available_rel in available_relations:
            available_lower = available_rel.lower()

            # 包含匹配
            if predicate_lower in available_lower or available_lower in predicate_lower:
                return available_rel

            # 编辑距离匹配
            if self._calculate_similarity(predicate_lower, available_lower) > 0.7:
                return available_rel

        # 默认映射策略
        if 'is_instance_of' in available_relations:
            return 'is_instance_of'

        return None

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        if not str1 or not str2:
            return 0.0

        # 简单的编辑距离相似度
        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 1.0

        # 计算公共字符数
        common_chars = sum(1 for c in str1 if c in str2)
        return common_chars / max_len
    
    def _build_entities_and_relations(self, triples: List[Dict[str, Any]],
                                    schema: str, source: str, extraction_result=None) -> Tuple[List[KGEntity], List[KGRelation]]:
        """构建实体和关系对象"""
        entities = []
        relations = []
        entity_names = set()
        
        current_time = datetime.now().isoformat()
        
        # 收集所有实体名称
        for triple in triples:
            entity_names.add(triple['subject'])
            entity_names.add(triple['object'])
        
        # 创建实体对象
        for entity_name in entity_names:
            entity_id = self._generate_entity_id(entity_name)
            
            # 推断实体类型
            inference_result = self.entity_inferer.infer_entity_type(entity_name)
            entity_type = inference_result.entity_type or "Unknown"
            
            # 创建实体属性
            properties = {
                'inference_method': inference_result.method,
                'inference_time': inference_result.inference_time,
                'original_name': entity_name
            }
            
            # 添加Schema特定属性
            if entity_type in self.entity_inferer.ontology_manager.entity_types:
                type_config = self.entity_inferer.ontology_manager.entity_types[entity_type]
                if hasattr(type_config, 'description'):
                    properties['type_description'] = type_config.description
                if hasattr(type_config, 'aliases'):
                    properties['aliases'] = type_config.aliases
            
            entity = KGEntity(
                id=entity_id,
                name=entity_name,
                type=entity_type,
                properties=properties,
                confidence=inference_result.confidence,
                source=source,
                created_at=current_time,
                schema=schema
            )
            
            entities.append(entity)
            self.entity_id_map[entity_name] = entity_id
        
        # 创建关系对象
        for i, triple in enumerate(triples):
            relation_id = f"rel_{uuid.uuid4().hex[:8]}"
            
            subject_id = self.entity_id_map[triple['subject']]
            object_id = self.entity_id_map[triple['object']]
            
            # 创建关系属性
            properties = {
                'extraction_confidence': triple.get('confidence', 0.8),
                'triple_index': i
            }
            
            # 添加Schema特定属性
            predicate = triple['predicate']
            if predicate in self.entity_inferer.ontology_manager.relation_types:
                rel_config = self.entity_inferer.ontology_manager.relation_types[predicate]
                if hasattr(rel_config, 'description'):
                    properties['relation_description'] = rel_config.description
                if hasattr(rel_config, 'subject_types'):
                    properties['expected_subject_types'] = rel_config.subject_types
                if hasattr(rel_config, 'object_types'):
                    properties['expected_object_types'] = rel_config.object_types
            
            relation = KGRelation(
                id=relation_id,
                subject_id=subject_id,
                subject_name=triple['subject'],
                predicate=predicate,
                object_id=object_id,
                object_name=triple['object'],
                properties=properties,
                confidence=triple.get('confidence', 0.8),
                source=source,
                created_at=current_time,
                schema=schema
            )
            
            relations.append(relation)
        
        return entities, relations
    
    def _generate_entity_id(self, entity_name: str) -> str:
        """生成实体ID"""
        # 使用实体名称的hash生成稳定的ID
        import hashlib
        name_hash = hashlib.md5(entity_name.encode('utf-8')).hexdigest()[:8]
        return f"entity_{name_hash}"
    
    def _create_knowledge_graph(self, entities: List[KGEntity], relations: List[KGRelation],
                              schema: str, source: str, start_time: float, extraction_result=None) -> KnowledgeGraph:
        """创建完整的知识图谱对象"""
        processing_time = time.time() - start_time
        
        # 统计信息
        entity_type_counts = {}
        relation_type_counts = {}
        
        for entity in entities:
            entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1
        
        for relation in relations:
            relation_type_counts[relation.predicate] = relation_type_counts.get(relation.predicate, 0) + 1
        
        # 元数据
        metadata = {
            'schema': schema,
            'source_document': source,
            'created_at': datetime.now().isoformat(),
            'processing_time': processing_time,
            'builder_version': '3.0.0'
        }
        
        # 统计信息
        statistics = {
            'total_entities': len(entities),
            'total_relations': len(relations),
            'entity_type_distribution': entity_type_counts,
            'relation_type_distribution': relation_type_counts,
            'average_entity_confidence': sum(e.confidence for e in entities) / len(entities) if entities else 0,
            'average_relation_confidence': sum(r.confidence for r in relations) / len(relations) if relations else 0
        }

        # 添加抽取统计信息
        if extraction_result:
            extraction_stats = self.hybrid_extractor.get_extraction_statistics(extraction_result)
            statistics.update({
                'extraction_method_breakdown': extraction_stats['method_breakdown'],
                'rule_extraction_count': extraction_stats['rule_triples'],
                'llm_extraction_count': extraction_stats['llm_triples'],
                'extraction_methods_used': extraction_stats['methods_used'],
                'triple_extraction_time': extraction_stats['processing_time']
            })
        
        return KnowledgeGraph(
            metadata=metadata,
            entities=entities,
            relations=relations,
            statistics=statistics
        )
    
    def _save_knowledge_graph(self, kg: KnowledgeGraph, output_path: str):
        """保存知识图谱到JSON文件"""
        # 转换为可序列化的字典
        kg_dict = {
            'metadata': kg.metadata,
            'entities': [asdict(entity) for entity in kg.entities],
            'relations': [asdict(relation) for relation in kg.relations],
            'statistics': kg.statistics
        }
        
        # 保存到文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(kg_dict, f, ensure_ascii=False, indent=2)
        
        print(f"💾 知识图谱已保存到: {output_path}")

# 全局构建器实例
kg_builder = SchemaBasedKGBuilder()
