"""
基于规则的三元组抽取器
智能推断层的核心组件，通过规则和模式识别直接抽取三元组
"""

import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ontology.managers.dynamic_schema import DynamicOntologyManager
from pipeline.enhanced_entity_inferer import EnhancedEntityTypeInferer

@dataclass
class TripleExtractionResult:
    """三元组抽取结果"""
    subject: str
    predicate: str
    object: str
    confidence: float
    method: str
    evidence: str

class RuleBasedTripleExtractor:
    """基于规则的三元组抽取器"""
    
    def __init__(self, ontology_manager: DynamicOntologyManager):
        self.ontology_manager = ontology_manager
        self.entity_inferer = EnhancedEntityTypeInferer()
        self.entity_inferer.ontology_manager = ontology_manager
        
        # 预编译的模式
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译抽取模式"""
        self.patterns = {
            # 实例关系模式
            'instance_patterns': [
                r'(\w+)\s+是\s+(\w+)',
                r'(\w+)\s+属于\s+(\w+)',
                r'(\w+)\s+is\s+a\s+(\w+)',
                r'(\w+)\s+is\s+an\s+(\w+)',
                r'(\w+)\s+is\s+instance\s+of\s+(\w+)',
            ],
            
            # 时间关系模式
            'temporal_patterns': [
                r'(\w+)\s+开始时间\s*[:：]\s*([0-9\-:\s]+)',
                r'(\w+)\s+结束时间\s*[:：]\s*([0-9\-:\s]+)',
                r'(\w+)\s+持续时间\s*[:：]\s*([0-9]+[小时天分钟])',
                r'(\w+)\s+发生在\s+([0-9\-:\s]+)',
                r'(\w+)\s+before\s+(\w+)',
                r'(\w+)\s+after\s+(\w+)',
            ],
            
            # 空间关系模式
            'spatial_patterns': [
                r'(\w+)\s+位于\s+(\w+)',
                r'(\w+)\s+在\s+(\w+)',
                r'(\w+)\s+located\s+at\s+(\w+)',
                r'(\w+)\s+contains\s+(\w+)',
                r'(\w+)\s+包含\s+(\w+)',
            ],
            
            # DO-DA-F关系模式
            'dodaf_patterns': [
                r'(\w+)\s+条件\s*[:：]\s*([^,，。.]+)',
                r'(\w+)\s+结果\s*[:：]\s*([^,，。.]+)',
                r'(\w+)\s+导致\s+(\w+)',
                r'(\w+)\s+causes\s+(\w+)',
                r'(\w+)\s+results\s+in\s+(\w+)',
                r'(\w+)\s+has\s+condition\s+([^,，。.]+)',
            ],
            
            # 架构关系模式
            'architecture_patterns': [
                r'(\w+)\s+包含\s+(\w+)',
                r'(\w+)\s+supports\s+(\w+)',
                r'(\w+)\s+implements\s+(\w+)',
                r'(\w+)\s+uses\s+(\w+)',
            ]
        }
        
        # 编译正则表达式
        self.compiled_patterns = {}
        for category, patterns in self.patterns.items():
            self.compiled_patterns[category] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def extract_triples(self, text: str) -> List[TripleExtractionResult]:
        """
        从文本中抽取三元组
        
        Args:
            text: 输入文本
            
        Returns:
            三元组抽取结果列表
        """
        print(f"🔧 规则抽取器开始处理文本，长度: {len(text)}")
        
        triples = []
        
        # 1. 实例关系抽取
        instance_triples = self._extract_instance_relations(text)
        triples.extend(instance_triples)
        
        # 2. 时间关系抽取
        temporal_triples = self._extract_temporal_relations(text)
        triples.extend(temporal_triples)
        
        # 3. 空间关系抽取
        spatial_triples = self._extract_spatial_relations(text)
        triples.extend(spatial_triples)
        
        # 4. DO-DA-F关系抽取
        dodaf_triples = self._extract_dodaf_relations(text)
        triples.extend(dodaf_triples)
        
        # 5. 架构关系抽取
        arch_triples = self._extract_architecture_relations(text)
        triples.extend(arch_triples)
        
        # 6. 基于实体推断的关系发现
        inferred_triples = self._infer_relations_from_entities(text)
        triples.extend(inferred_triples)
        
        print(f"🔧 规则抽取完成，共抽取 {len(triples)} 个三元组")
        
        return triples
    
    def _extract_instance_relations(self, text: str) -> List[TripleExtractionResult]:
        """抽取实例关系"""
        triples = []
        
        for pattern in self.compiled_patterns['instance_patterns']:
            matches = pattern.findall(text)
            for match in matches:
                subject, obj = match
                
                # 验证实体类型
                subject_type = self.entity_inferer.infer_entity_type(subject)
                object_type = self.entity_inferer.infer_entity_type(obj)
                
                if subject_type.confidence > 0.5 and object_type.confidence > 0.5:
                    triple = TripleExtractionResult(
                        subject=subject,
                        predicate="is_instance_of",
                        object=obj,
                        confidence=min(subject_type.confidence, object_type.confidence),
                        method="rule_pattern",
                        evidence=f"Pattern match: {pattern.pattern}"
                    )
                    triples.append(triple)
        
        return triples
    
    def _extract_temporal_relations(self, text: str) -> List[TripleExtractionResult]:
        """抽取时间关系"""
        triples = []
        
        # 开始时间模式
        start_time_patterns = [
            r'(\w+)[^0-9]*开始时间[^0-9]*([0-9\-:\s]+)',
            r'(\w+)[^0-9]*发生在[^0-9]*([0-9\-:\s]+)',
        ]
        
        for pattern_str in start_time_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(text)
            for match in matches:
                subject, time_str = match
                
                triple = TripleExtractionResult(
                    subject=subject.strip(),
                    predicate="hasStartTime",
                    object=time_str.strip(),
                    confidence=0.8,
                    method="temporal_pattern",
                    evidence=f"Time pattern: {pattern_str}"
                )
                triples.append(triple)
        
        # 持续时间模式
        duration_patterns = [
            r'(\w+)[^0-9]*持续时间[^0-9]*([0-9]+[小时天分钟])',
            r'(\w+)[^0-9]*持续[^0-9]*([0-9]+[小时天分钟])',
        ]
        
        for pattern_str in duration_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(text)
            for match in matches:
                subject, duration = match
                
                triple = TripleExtractionResult(
                    subject=subject.strip(),
                    predicate="hasDuration",
                    object=duration.strip(),
                    confidence=0.8,
                    method="temporal_pattern",
                    evidence=f"Duration pattern: {pattern_str}"
                )
                triples.append(triple)
        
        return triples
    
    def _extract_spatial_relations(self, text: str) -> List[TripleExtractionResult]:
        """抽取空间关系"""
        triples = []
        
        # 位置关系模式
        location_patterns = [
            r'(\w+)[^a-zA-Z]*位于[^a-zA-Z]*(\w+)',
            r'(\w+)[^a-zA-Z]*在[^a-zA-Z]*(\w+)',
        ]
        
        for pattern_str in location_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(text)
            for match in matches:
                subject, location = match
                
                triple = TripleExtractionResult(
                    subject=subject.strip(),
                    predicate="locatedAt",
                    object=location.strip(),
                    confidence=0.8,
                    method="spatial_pattern",
                    evidence=f"Location pattern: {pattern_str}"
                )
                triples.append(triple)
        
        return triples
    
    def _extract_dodaf_relations(self, text: str) -> List[TripleExtractionResult]:
        """抽取DO-DA-F关系"""
        triples = []
        
        # 条件关系模式
        condition_patterns = [
            r'(\w+)[^>]*条件[^>]*[:：]\s*([^,，。.]+)',
            r'(\w+)[^>]*when[^>]*([^,，。.]+)',
        ]
        
        for pattern_str in condition_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(text)
            for match in matches:
                action, condition = match
                
                triple = TripleExtractionResult(
                    subject=action.strip(),
                    predicate="hasCondition",
                    object=condition.strip(),
                    confidence=0.7,
                    method="dodaf_pattern",
                    evidence=f"Condition pattern: {pattern_str}"
                )
                triples.append(triple)
        
        # 结果关系模式
        result_patterns = [
            r'(\w+)[^a-zA-Z]*结果[^a-zA-Z]*[:：]\s*([^,，。.]+)',
            r'(\w+)[^a-zA-Z]*导致[^a-zA-Z]*(\w+)',
            r'(\w+)[^a-zA-Z]*results\s+in[^a-zA-Z]*(\w+)',
        ]
        
        for pattern_str in result_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(text)
            for match in matches:
                action, result = match
                
                triple = TripleExtractionResult(
                    subject=action.strip(),
                    predicate="resultsIn",
                    object=result.strip(),
                    confidence=0.7,
                    method="dodaf_pattern",
                    evidence=f"Result pattern: {pattern_str}"
                )
                triples.append(triple)
        
        return triples
    
    def _extract_architecture_relations(self, text: str) -> List[TripleExtractionResult]:
        """抽取架构关系"""
        triples = []
        
        # 包含关系模式
        contains_patterns = [
            r'(\w+)[^a-zA-Z]*包含[^a-zA-Z]*(\w+)',
            r'(\w+)[^a-zA-Z]*contains[^a-zA-Z]*(\w+)',
        ]
        
        for pattern_str in contains_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = pattern.findall(text)
            for match in matches:
                container, contained = match
                
                triple = TripleExtractionResult(
                    subject=container.strip(),
                    predicate="contains",
                    object=contained.strip(),
                    confidence=0.7,
                    method="architecture_pattern",
                    evidence=f"Contains pattern: {pattern_str}"
                )
                triples.append(triple)
        
        return triples
    
    def _infer_relations_from_entities(self, text: str) -> List[TripleExtractionResult]:
        """基于实体推断关系"""
        triples = []
        
        # 简单的共现关系推断
        sentences = re.split(r'[。.!！?？]', text)
        
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue
            
            # 提取句子中的实体
            entities = self._extract_entities_from_sentence(sentence)
            
            if len(entities) >= 2:
                # 为每对实体推断可能的关系
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i+1:]:
                        relation = self._infer_relation_between_entities(entity1, entity2, sentence)
                        if relation:
                            triples.append(relation)
        
        return triples
    
    def _extract_entities_from_sentence(self, sentence: str) -> List[str]:
        """从句子中提取实体"""
        # 简单的实体识别：大写字母开头的词、数字时间、特殊模式
        entity_patterns = [
            r'[A-Z][a-zA-Z]+',  # 大写开头的词
            r'\d{4}-\d{2}-\d{2}[\s\d:]*',  # 时间格式
            r'\d+[小时天分钟]',  # 时间长度
            r'[a-zA-Z]+[A-Z][a-zA-Z]*',  # 驼峰命名
        ]
        
        entities = []
        for pattern_str in entity_patterns:
            pattern = re.compile(pattern_str)
            matches = pattern.findall(sentence)
            entities.extend(matches)
        
        return list(set(entities))  # 去重
    
    def _infer_relation_between_entities(self, entity1: str, entity2: str, context: str) -> Optional[TripleExtractionResult]:
        """推断两个实体之间的关系"""
        # 基于上下文关键词推断关系
        context_lower = context.lower()
        
        # 时间关系推断
        if any(keyword in context_lower for keyword in ['开始', '发生', 'start', 'begin']):
            if re.match(r'\d{4}-\d{2}-\d{2}', entity2):
                return TripleExtractionResult(
                    subject=entity1,
                    predicate="hasStartTime",
                    object=entity2,
                    confidence=0.6,
                    method="context_inference",
                    evidence=f"Context: {context[:50]}..."
                )
        
        # 位置关系推断
        if any(keyword in context_lower for keyword in ['位于', '在', 'located', 'at']):
            return TripleExtractionResult(
                subject=entity1,
                predicate="locatedAt",
                object=entity2,
                confidence=0.6,
                method="context_inference",
                evidence=f"Context: {context[:50]}..."
            )
        
        return None
