"""
动态本体映射模块
基于动态本体系统进行三元组映射
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from difflib import SequenceMatcher

from ontology.dynamic_schema import (
    DynamicOntologyManager, EntityTypeConfig, RelationTypeConfig,
    DYNAMIC_ONTOLOGY
)

@dataclass
class MappingResult:
    """映射结果"""
    success: bool
    mapped_triple: Optional[Dict] = None
    confidence: float = 0.0
    issues: List[str] = None
    suggestions: List[str] = None
    new_types_discovered: List[str] = None

class DynamicOntologyMapper:
    """动态本体映射器"""
    
    def __init__(self, ontology_manager: DynamicOntologyManager = None):
        self.ontology = ontology_manager or DYNAMIC_ONTOLOGY
        
    def map_triples(self, cleaned_triples: List[Dict]) -> List[MappingResult]:
        """映射多个三元组到动态本体"""
        results = []
        
        for triple in cleaned_triples:
            result = self.map_single_triple(triple)
            results.append(result)
        
        return results
    
    def map_single_triple(self, triple: Dict) -> MappingResult:
        """映射单个三元组到动态本体"""
        try:
            subject = triple["subject"]
            predicate = triple["predicate"]
            obj = triple["object"]
            
            issues = []
            suggestions = []
            new_types_discovered = []
            
            # 映射谓词到关系类型
            mapped_relation = self._map_predicate_to_relation_type(predicate)
            if not mapped_relation:
                issues.append(f"未识别的关系类型: {predicate}")
                suggestions.extend(self._suggest_predicate_mappings(predicate))
                
                # 记录为待发现的关系类型
                new_types_discovered.append(f"relation:{predicate}")
            
            # 映射实体类型
            subject_type = self.ontology._identify_entity_type(subject)
            if not subject_type:
                # 尝试从名称推断类型
                inferred_type = self.ontology._extract_type_from_name(subject)
                subject_type = inferred_type
                new_types_discovered.append(f"entity:{inferred_type}")
            
            object_type = None
            if not self.ontology._is_literal(obj):
                object_type = self.ontology._identify_entity_type(obj)
                if not object_type:
                    inferred_type = self.ontology._extract_type_from_name(obj)
                    object_type = inferred_type
                    new_types_discovered.append(f"entity:{inferred_type}")
            
            # 计算映射置信度
            confidence = self._calculate_mapping_confidence(
                subject_type, mapped_relation, object_type, triple
            )
            
            # 构建映射后的三元组
            mapped_triple = {
                "subject": subject,
                "subject_type": subject_type,
                "predicate": mapped_relation or predicate,  # 使用原始谓词如果无法映射
                "object": obj,
                "object_type": object_type,
                "confidence": confidence,
                "source": triple.get("source", "unknown"),
                "original_triple": triple
            }
            
            return MappingResult(
                success=True,  # 即使有些类型未识别，仍然算作成功
                mapped_triple=mapped_triple,
                confidence=confidence,
                issues=issues,
                suggestions=suggestions,
                new_types_discovered=new_types_discovered
            )
            
        except Exception as e:
            return MappingResult(
                success=False,
                confidence=0.0,
                issues=[f"映射过程中发生错误: {str(e)}"],
                suggestions=[],
                new_types_discovered=[]
            )
    
    def _map_predicate_to_relation_type(self, predicate: str) -> Optional[str]:
        """将谓词映射到关系类型"""
        return self.ontology._identify_relation_type(predicate)
    
    def _calculate_mapping_confidence(self, subject_type: Optional[str], 
                                    relation_type: Optional[str], 
                                    object_type: Optional[str], 
                                    original_triple: Dict) -> float:
        """计算映射置信度"""
        confidence_factors = []
        
        # 主语类型置信度
        if subject_type and subject_type != "Unknown":
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.5)
        
        # 宾语类型置信度
        if object_type and object_type != "Unknown":
            confidence_factors.append(0.9)
        elif self.ontology._is_literal(original_triple["object"]):
            confidence_factors.append(1.0)  # 字面值总是可信的
        else:
            confidence_factors.append(0.5)
        
        # 关系类型置信度
        if relation_type:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.6)  # 未识别的关系仍有一定置信度
        
        # 原始三元组置信度
        confidence_factors.append(original_triple.get("confidence", 1.0))
        
        # 计算综合置信度（几何平均）
        if confidence_factors:
            confidence = 1.0
            for factor in confidence_factors:
                confidence *= factor
            return confidence ** (1.0 / len(confidence_factors))
        
        return 0.5
    
    def _suggest_predicate_mappings(self, predicate: str) -> List[str]:
        """为未识别的谓词提供建议"""
        suggestions = []
        predicate_lower = predicate.lower()
        
        # 寻找相似的关系类型
        for relation_name, config in self.ontology.relation_types.items():
            similarity = SequenceMatcher(None, predicate_lower, relation_name.lower()).ratio()
            if similarity > 0.3:
                suggestions.append(f"相似关系: '{relation_name}' (相似度: {similarity:.2f})")
        
        if not suggestions:
            suggestions.append("建议手动定义此关系类型，或等待自动学习")
        
        return suggestions
    
    def get_mapping_statistics(self) -> Dict:
        """获取映射统计信息"""
        return {
            "ontology_version": self.ontology.current_version,
            "entity_types_count": len(self.ontology.entity_types),
            "relation_types_count": len(self.ontology.relation_types),
            "processing_stats": dict(self.ontology.processing_stats)
        }

# 使用示例
if __name__ == "__main__":
    from pipeline.triple_cleaner import TripleCleaner
    from data.sample_triples import SAMPLE_TRIPLES
    
    # 清理三元组
    cleaner = TripleCleaner()
    cleaned_triples = cleaner.clean_triples(SAMPLE_TRIPLES)
    
    # 使用动态本体映射
    mapper = DynamicOntologyMapper()
    mapping_results = mapper.map_triples(cleaned_triples)
    
    print(f"映射了 {len(mapping_results)} 个三元组")
    
    # 显示映射结果
    for i, result in enumerate(mapping_results[:5]):
        print(f"\n映射结果 {i+1}:")
        print(f"  成功: {result.success}")
        print(f"  置信度: {result.confidence:.3f}")
        if result.mapped_triple:
            triple = result.mapped_triple
            print(f"  映射后: {triple['subject']}({triple['subject_type']}) --{triple['predicate']}--> {triple['object']}({triple.get('object_type', 'literal')})")
        if result.new_types_discovered:
            print(f"  发现新类型: {result.new_types_discovered}")
        if result.issues:
            print(f"  问题: {result.issues}")
    
    # 显示本体状态
    print(f"\n本体状态: {mapper.get_mapping_statistics()}") 