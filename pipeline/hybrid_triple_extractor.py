"""
混合三元组抽取器
协调规则抽取和LLM抽取，实现正确的抽取流程：
规则抽取 → 规则失败时使用LLM抽取
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from pipeline.rule_based_triple_extractor import RuleBasedTripleExtractor, TripleExtractionResult
from pipeline.llm_client import LLMClient
from ontology.managers.dynamic_schema import DynamicOntologyManager

@dataclass
class HybridExtractionResult:
    """混合抽取结果"""
    triples: List[Dict[str, Any]]
    rule_count: int
    llm_count: int
    total_time: float
    methods_used: List[str]

class HybridTripleExtractor:
    """混合三元组抽取器"""
    
    def __init__(self, ontology_manager: DynamicOntologyManager):
        self.ontology_manager = ontology_manager
        self.rule_extractor = RuleBasedTripleExtractor(ontology_manager)
        self.llm_client = LLMClient()
        
        # 配置参数
        self.min_rule_confidence = 0.6  # 规则抽取最低置信度
        self.min_rule_count = 3  # 规则抽取最少三元组数量
        self.use_llm_fallback = True  # 是否启用LLM兜底
    
    def extract_triples(self, text: str) -> HybridExtractionResult:
        """
        混合抽取三元组
        
        Args:
            text: 输入文本
            
        Returns:
            混合抽取结果
        """
        start_time = time.time()
        methods_used = []
        
        print(f"\n🔄 混合抽取器开始处理")
        print(f"📝 文本长度: {len(text)} 字符")
        print("=" * 60)
        
        # 第一阶段：规则抽取
        print(f"\n🔧 阶段1: 规则抽取")
        rule_results = self.rule_extractor.extract_triples(text)
        
        # 转换为标准格式
        rule_triples = []
        for result in rule_results:
            triple = {
                "subject": result.subject,
                "predicate": result.predicate,
                "object": result.object,
                "confidence": result.confidence,
                "method": result.method,
                "evidence": result.evidence
            }
            rule_triples.append(triple)
        
        print(f"   📊 规则抽取结果: {len(rule_triples)} 个三元组")
        
        # 分析规则抽取质量
        high_confidence_rules = [t for t in rule_triples if t["confidence"] >= self.min_rule_confidence]
        rule_quality_score = len(high_confidence_rules) / max(len(rule_triples), 1)
        
        print(f"   📈 高置信度三元组: {len(high_confidence_rules)} 个")
        print(f"   🎯 规则质量分数: {rule_quality_score:.2f}")
        
        methods_used.append("rule_extraction")
        
        # 第二阶段：判断是否需要LLM兜底
        need_llm_fallback = self._should_use_llm_fallback(rule_triples, text)
        
        llm_triples = []
        if need_llm_fallback and self.use_llm_fallback:
            print(f"\n🤖 阶段2: LLM兜底抽取")
            print(f"   🔍 触发原因: {self._get_fallback_reason(rule_triples, text)}")
            
            llm_triples = self._llm_extract_triples(text)
            print(f"   📊 LLM抽取结果: {len(llm_triples)} 个三元组")
            methods_used.append("llm_extraction")
        else:
            print(f"\n✅ 规则抽取充分，无需LLM兜底")
        
        # 第三阶段：结果合并和去重
        print(f"\n🔄 阶段3: 结果合并")
        final_triples = self._merge_and_deduplicate(rule_triples, llm_triples)
        
        total_time = time.time() - start_time
        
        print(f"   📊 最终结果: {len(final_triples)} 个三元组")
        print(f"   ⏱️ 总耗时: {total_time:.2f}s")
        print("=" * 60)
        
        return HybridExtractionResult(
            triples=final_triples,
            rule_count=len(rule_triples),
            llm_count=len(llm_triples),
            total_time=total_time,
            methods_used=methods_used
        )
    
    def _should_use_llm_fallback(self, rule_triples: List[Dict[str, Any]], text: str) -> bool:
        """判断是否需要LLM兜底"""
        # 条件1: 规则抽取数量不足
        if len(rule_triples) < self.min_rule_count:
            return True
        
        # 条件2: 高置信度三元组比例过低
        high_confidence_count = sum(1 for t in rule_triples if t["confidence"] >= self.min_rule_confidence)
        if high_confidence_count / len(rule_triples) < 0.5:
            return True
        
        # 条件3: 文本复杂度高但抽取结果少
        text_complexity = self._calculate_text_complexity(text)
        expected_triples = max(3, text_complexity // 100)  # 每100字符期望至少1个三元组
        
        if len(rule_triples) < expected_triples * 0.5:
            return True
        
        return False
    
    def _get_fallback_reason(self, rule_triples: List[Dict[str, Any]], text: str) -> str:
        """获取LLM兜底的原因"""
        reasons = []
        
        if len(rule_triples) < self.min_rule_count:
            reasons.append(f"三元组数量不足({len(rule_triples)}<{self.min_rule_count})")
        
        high_confidence_count = sum(1 for t in rule_triples if t["confidence"] >= self.min_rule_confidence)
        if len(rule_triples) > 0 and high_confidence_count / len(rule_triples) < 0.5:
            reasons.append(f"高置信度比例过低({high_confidence_count}/{len(rule_triples)})")
        
        text_complexity = self._calculate_text_complexity(text)
        expected_triples = max(3, text_complexity // 100)
        if len(rule_triples) < expected_triples * 0.5:
            reasons.append(f"抽取密度过低({len(rule_triples)}<{expected_triples*0.5:.1f})")
        
        return "; ".join(reasons) if reasons else "未知原因"
    
    def _calculate_text_complexity(self, text: str) -> int:
        """计算文本复杂度"""
        # 简单的复杂度计算：字符数 + 句子数 + 实体数估计
        char_count = len(text)
        sentence_count = len([s for s in text.split('.') if len(s.strip()) > 5])
        entity_estimate = len([w for w in text.split() if w[0].isupper()]) if text else 0
        
        return char_count + sentence_count * 10 + entity_estimate * 5
    
    def _llm_extract_triples(self, text: str) -> List[Dict[str, Any]]:
        """使用LLM抽取三元组"""
        schema_info = {
            'name': self.ontology_manager.metadata.get('name', '未知Schema'),
            'entity_types': self.ontology_manager.entity_types,
            'relation_types': self.ontology_manager.relation_types
        }
        
        # 调用LLM抽取
        llm_triples = self.llm_client.extract_triples(text, schema_info)
        
        # 标记LLM来源
        for triple in llm_triples:
            if "method" not in triple:
                triple["method"] = "llm_extraction"
            if "evidence" not in triple:
                triple["evidence"] = "LLM generated"
        
        return llm_triples
    
    def _merge_and_deduplicate(self, rule_triples: List[Dict[str, Any]], 
                              llm_triples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并和去重三元组"""
        all_triples = rule_triples + llm_triples
        
        if not all_triples:
            return []
        
        # 简单去重：基于主语-谓语-宾语的组合
        seen_triples = set()
        unique_triples = []
        
        for triple in all_triples:
            triple_key = (
                triple["subject"].lower().strip(),
                triple["predicate"].lower().strip(),
                triple["object"].lower().strip()
            )
            
            if triple_key not in seen_triples:
                seen_triples.add(triple_key)
                unique_triples.append(triple)
            else:
                # 如果重复，保留置信度更高的
                for i, existing in enumerate(unique_triples):
                    existing_key = (
                        existing["subject"].lower().strip(),
                        existing["predicate"].lower().strip(),
                        existing["object"].lower().strip()
                    )
                    if existing_key == triple_key:
                        if triple.get("confidence", 0) > existing.get("confidence", 0):
                            unique_triples[i] = triple
                        break
        
        # 按置信度排序
        unique_triples.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        print(f"   🔄 去重前: {len(all_triples)} 个，去重后: {len(unique_triples)} 个")
        
        return unique_triples
    
    def get_extraction_statistics(self, result: HybridExtractionResult) -> Dict[str, Any]:
        """获取抽取统计信息"""
        stats = {
            "total_triples": len(result.triples),
            "rule_triples": result.rule_count,
            "llm_triples": result.llm_count,
            "rule_ratio": result.rule_count / max(len(result.triples), 1),
            "llm_ratio": result.llm_count / max(len(result.triples), 1),
            "methods_used": result.methods_used,
            "processing_time": result.total_time,
            "avg_confidence": sum(t.get("confidence", 0) for t in result.triples) / max(len(result.triples), 1)
        }
        
        # 按方法分组统计
        method_stats = {}
        for triple in result.triples:
            method = triple.get("method", "unknown")
            if method not in method_stats:
                method_stats[method] = {"count": 0, "avg_confidence": 0}
            method_stats[method]["count"] += 1
        
        # 计算各方法的平均置信度
        for method in method_stats:
            method_triples = [t for t in result.triples if t.get("method") == method]
            if method_triples:
                method_stats[method]["avg_confidence"] = sum(t.get("confidence", 0) for t in method_triples) / len(method_triples)
        
        stats["method_breakdown"] = method_stats
        
        return stats
