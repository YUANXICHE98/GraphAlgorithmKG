"""
三元组填充模块
基于本体规则和推理机制，为现有三元组生成派生的新三元组
"""

from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass
from collections import defaultdict
import itertools

# 使用动态本体系统的类
from ontology.managers.dynamic_schema import DynamicOntologyManager, Entity, Relation

@dataclass
class EnrichmentRule:
    """填充推理规则"""
    rule_name: str
    description: str
    premise_patterns: List[Tuple[str, str, str]]  # (subject_pattern, predicate, object_pattern)
    conclusion_pattern: Tuple[str, str, str]  # 结论三元组模式
    confidence_factor: float = 0.8  # 推理置信度因子

class TripleEnricher:
    """三元组填充器"""
    
    def __init__(self, ontology_schema: DynamicOntologyManager):
        self.schema = ontology_schema
        self.enrichment_rules = self._initialize_enrichment_rules()
        self.inferred_triples = []
    
    def _initialize_enrichment_rules(self) -> List[EnrichmentRule]:
        """初始化推理规则"""
        rules = []
        
        # 规则1: 传递性规则 - builds_on关系的传递性
        rules.append(EnrichmentRule(
            rule_name="builds_on_transitivity",
            description="如果A基于B，B基于C，则A基于C",
            premise_patterns=[
                ("?X", "builds_on", "?Y"),
                ("?Y", "builds_on", "?Z")
            ],
            conclusion_pattern=("?X", "builds_on", "?Z"),
            confidence_factor=0.7
        ))
        
        # 规则2: 实现关系的逆向推理
        rules.append(EnrichmentRule(
            rule_name="implements_inverse",
            description="如果技术T实现算法A，则算法A被技术T实现",
            premise_patterns=[
                ("?T", "implements", "?A")
            ],
            conclusion_pattern=("?A", "implemented_by", "?T"),
            confidence_factor=1.0
        ))
        
        # 规则3: 范式使用的传播
        rules.append(EnrichmentRule(
            rule_name="paradigm_propagation",
            description="如果算法A使用范式P，技术T实现算法A，则技术T间接使用范式P",
            premise_patterns=[
                ("?A", "uses_paradigm", "?P"),
                ("?T", "implements", "?A")
            ],
            conclusion_pattern=("?T", "uses_paradigm", "?P"),
            confidence_factor=0.6
        ))
        
        # 规则4: 框架-技术关系推理
        rules.append(EnrichmentRule(
            rule_name="framework_technique_inference",
            description="如果技术T基于框架F，算法A使用技术T，则算法A与框架F相关",
            premise_patterns=[
                ("?T", "builds_on", "?F"),
                ("?A", "implements", "?T")  # 这里应该是implemented_by，但为了规则简化
            ],
            conclusion_pattern=("?A", "uses_framework", "?F"),
            confidence_factor=0.5
        ))
        
        # 规则5: 性能指标继承
        rules.append(EnrichmentRule(
            rule_name="metric_inheritance",
            description="如果技术T减少了X%计算量，使用T的算法A也会减少计算量",
            premise_patterns=[
                ("?T", "reduces_computation_by", "?X"),
                ("?A", "implemented_by", "?T")
            ],
            conclusion_pattern=("?A", "benefits_from_reduction", "?X"),
            confidence_factor=0.4
        ))
        
        return rules
    
    def enrich_triples(self, mapped_triples: List[Dict]) -> List[Dict]:
        """填充三元组，返回包含原始和推理三元组的列表"""
        # 首先将映射的三元组加入本体
        self._add_triples_to_schema(mapped_triples)
        
        # 执行推理填充
        inferred = self._perform_inference()
        
        # 去重和过滤
        filtered_inferred = self._filter_and_deduplicate(inferred, mapped_triples)
        
        # 合并原始三元组和推理三元组
        all_triples = mapped_triples.copy()
        all_triples.extend(filtered_inferred)
        
        return all_triples
    
    def _add_triples_to_schema(self, mapped_triples: List[Dict]):
        """将映射的三元组添加到本体模式中"""
        for triple in mapped_triples:
            try:
                # 构建关系对象
                relation = Relation(
                    subject=triple["subject"],
                    predicate=triple["predicate"], # Assuming predicate is a string
                    object=triple["object"],
                    confidence=triple.get("confidence", 1.0),
                    source=triple.get("source", "mapped")
                )
                
                # 添加到本体
                self.schema.add_relation(relation)
                
            except Exception as e:
                print(f"添加三元组到本体时出错: {triple}, 错误: {e}")
    
    def _perform_inference(self) -> List[Dict]:
        """执行推理，生成新三元组"""
        inferred_triples = []
        
        for rule in self.enrichment_rules:
            try:
                rule_inferences = self._apply_rule(rule)
                inferred_triples.extend(rule_inferences)
            except Exception as e:
                print(f"应用规则 {rule.rule_name} 时出错: {e}")
        
        return inferred_triples
    
    def _apply_rule(self, rule: EnrichmentRule) -> List[Dict]:
        """应用单个推理规则"""
        inferred = []
        
        # 获取所有关系的索引
        relations_by_predicate = defaultdict(list)
        for relation in self.schema.relations:
            relations_by_predicate[relation.predicate].append(relation)  # 直接使用字符串
        
        # 查找满足前提条件的绑定
        bindings = self._find_rule_bindings(rule, relations_by_predicate)
        
        # 为每个绑定生成结论
        for binding in bindings:
            conclusion_triple = self._instantiate_conclusion(rule.conclusion_pattern, binding)
            if conclusion_triple:
                # 计算推理置信度
                premise_confidences = []
                for var_binding in binding.values():
                    if isinstance(var_binding, Relation):
                        premise_confidences.append(var_binding.confidence)
                
                avg_premise_confidence = sum(premise_confidences) / len(premise_confidences) if premise_confidences else 1.0
                inferred_confidence = avg_premise_confidence * rule.confidence_factor
                
                inferred_triple_dict = {
                    "subject": conclusion_triple[0],
                    "predicate": conclusion_triple[1],
                    "object": conclusion_triple[2],
                    "confidence": inferred_confidence,
                    "source": f"inference_{rule.rule_name}",
                    "rule_applied": rule.rule_name,
                    "is_inferred": True
                }
                
                inferred.append(inferred_triple_dict)
        
        return inferred
    
    def _find_rule_bindings(self, rule: EnrichmentRule, relations_by_predicate: Dict) -> List[Dict]:
        """查找满足规则前提条件的变量绑定"""
        bindings = []
        
        if not rule.premise_patterns:
            return bindings
        
        # 获取第一个前提的所有可能绑定
        first_pattern = rule.premise_patterns[0]
        first_bindings = self._get_pattern_bindings(first_pattern, relations_by_predicate)
        
        # 如果只有一个前提条件
        if len(rule.premise_patterns) == 1:
            return first_bindings
        
        # 多个前提条件：需要找到一致的绑定
        for base_binding in first_bindings:
            consistent_bindings = [base_binding]
            
            # 检查其余前提条件
            is_consistent = True
            for pattern in rule.premise_patterns[1:]:
                pattern_bindings = self._get_pattern_bindings(pattern, relations_by_predicate)
                
                # 查找与当前绑定一致的绑定
                compatible_bindings = []
                for binding in pattern_bindings:
                    if self._is_binding_compatible(base_binding, binding):
                        # 合并绑定
                        merged_binding = {**base_binding, **binding}
                        compatible_bindings.append(merged_binding)
                
                if not compatible_bindings:
                    is_consistent = False
                    break
                
                consistent_bindings = compatible_bindings
            
            if is_consistent:
                bindings.extend(consistent_bindings)
        
        return bindings
    
    def _get_pattern_bindings(self, pattern: Tuple[str, str, str], relations_by_predicate: Dict) -> List[Dict]:
        """获取单个模式的所有可能绑定"""
        subject_pattern, predicate_pattern, object_pattern = pattern
        bindings = []
        
        # 获取匹配谓词的关系
        matching_relations = []
        if predicate_pattern.startswith("?"):
            # 谓词是变量，匹配所有关系
            for relations_list in relations_by_predicate.values():
                matching_relations.extend(relations_list)
        else:
            # 谓词是常量，只匹配特定关系
            matching_relations = relations_by_predicate.get(predicate_pattern, [])
        
        # 为每个匹配的关系创建绑定
        for relation in matching_relations:
            binding = {}
            
            # 绑定主语
            if subject_pattern.startswith("?"):
                binding[subject_pattern] = relation.subject
            elif subject_pattern != relation.subject:
                continue  # 主语不匹配，跳过
            
            # 绑定谓词
            if predicate_pattern.startswith("?"):
                binding[predicate_pattern] = relation.predicate  # 直接使用字符串
            
            # 绑定宾语
            if object_pattern.startswith("?"):
                binding[object_pattern] = relation.object
            elif object_pattern != relation.object:
                continue  # 宾语不匹配，跳过
            
            # 存储原始关系用于置信度计算
            binding[f"_relation_{len(bindings)}"] = relation
            
            bindings.append(binding)
        
        return bindings
    
    def _is_binding_compatible(self, binding1: Dict, binding2: Dict) -> bool:
        """检查两个绑定是否兼容（共同变量有相同的值）"""
        common_vars = set(binding1.keys()) & set(binding2.keys())
        
        for var in common_vars:
            if var.startswith("_relation_"):  # 跳过内部关系存储
                continue
            if binding1[var] != binding2[var]:
                return False
        
        return True
    
    def _instantiate_conclusion(self, conclusion_pattern: Tuple[str, str, str], binding: Dict) -> Optional[Tuple[str, str, str]]:
        """根据变量绑定实例化结论模式"""
        try:
            subject, predicate, obj = conclusion_pattern
            
            # 替换变量
            if subject.startswith("?") and subject in binding:
                subject = binding[subject]
            if predicate.startswith("?") and predicate in binding:
                predicate = binding[predicate] 
            if obj.startswith("?") and obj in binding:
                obj = binding[obj]
            
            # 检查是否还有未绑定的变量
            if subject.startswith("?") or predicate.startswith("?") or obj.startswith("?"):
                return None
            
            return (subject, predicate, obj)
            
        except Exception:
            return None
    
    def _filter_and_deduplicate(self, inferred_triples: List[Dict], original_triples: List[Dict]) -> List[Dict]:
        """过滤和去重推理三元组"""
        filtered = []
        seen_triples = set()
        
        # 记录原始三元组
        for triple in original_triples:
            triple_key = (triple["subject"], triple["predicate"], triple["object"])
            seen_triples.add(triple_key)
        
        # 过滤推理三元组
        for triple in inferred_triples:
            triple_key = (triple["subject"], triple["predicate"], triple["object"])
            
            # 跳过重复三元组
            if triple_key in seen_triples:
                continue
            
            # 过滤低置信度的三元组
            if triple.get("confidence", 0) < 0.1:
                continue
            
            # 过滤自指三元组（主语和宾语相同）
            if triple["subject"] == triple["object"]:
                continue
            
            filtered.append(triple)
            seen_triples.add(triple_key)
        
        return filtered
    
    def get_inference_statistics(self) -> Dict:
        """获取推理统计信息"""
        stats = {
            "total_rules": len(self.enrichment_rules),
            "total_relations_in_schema": len(self.schema.relations),
            "total_entities_in_schema": len(self.schema.entities),
        }
        
        # 按规则统计推理结果
        rules_stats = defaultdict(int)
        confidence_stats = []
        
        for relation in self.schema.relations:
            if hasattr(relation, 'source') and relation.source and 'inference_' in relation.source:
                rule_name = relation.source.replace('inference_', '')
                rules_stats[rule_name] += 1
                confidence_stats.append(relation.confidence)
        
        stats["rules_applied"] = dict(rules_stats)
        if confidence_stats:
            stats["avg_inference_confidence"] = sum(confidence_stats) / len(confidence_stats)
        
        return stats

# 注意: 此模块现在与动态本体系统集成使用
# 完整的使用示例请参考 dynamic_main.py 