"""
增强的实体类型推断器
基于分层匹配策略的实体类型推断系统
"""

import re
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class InferenceResult:
    """推断结果"""
    entity_type: Optional[str]
    confidence: float
    method: str  # 'cache', 'pattern', 'keyword', 'context', 'unknown'
    inference_time: float

class EntityTypeCache:
    """实体类型缓存"""
    
    def __init__(self):
        self.verified_entities = {}
        self.confidence_threshold = 0.9
    
    def get(self, entity_name: str) -> Optional[Dict]:
        """获取缓存的实体类型"""
        return self.verified_entities.get(entity_name.lower())
    
    def add_verified_entity(self, entity_name: str, entity_type: str, 
                          confidence: float, source: str):
        """添加已验证的实体类型"""
        key = entity_name.lower()
        if key in self.verified_entities:
            # 更新使用计数
            self.verified_entities[key]['count'] += 1
            self.verified_entities[key]['last_used'] = time.time()
        else:
            self.verified_entities[key] = {
                'type': entity_type,
                'confidence': confidence,
                'source': source,
                'count': 1,
                'last_used': time.time()
            }
    
    def export_for_review(self) -> List[Dict]:
        """导出高频实体供人工审核"""
        high_freq_entities = []
        for entity, info in self.verified_entities.items():
            if info['count'] >= 3:  # 出现3次以上
                high_freq_entities.append({
                    'entity': entity,
                    'type': info['type'],
                    'confidence': info['confidence'],
                    'frequency': info['count'],
                    'source': info['source']
                })
        return sorted(high_freq_entities, key=lambda x: x['frequency'], reverse=True)

class EnhancedEntityTypeInferer:
    """增强的分层实体类型推断器"""
    
    def __init__(self):
        # 实体类型缓存
        self.entity_cache = EntityTypeCache()
        
        # 清理后的通用关键词（移除具体算法名称）
        self.type_keywords = {
            'Algorithm': [
                'algorithm', 'method', 'approach', 'technique', 'procedure',
                'search', 'sort', 'optimization', 'learning', 'training',
                'greedy', 'heuristic', 'recursive', 'iterative', 'dynamic'
            ],
            'Framework': [
                'framework', 'library', 'platform', 'toolkit', 'system',
                'network', 'model', 'architecture', 'neural', 'deep'
            ],
            'Technique': [
                'technique', 'strategy', 'mechanism', 'process', 'procedure',
                'pruning', 'compression', 'embedding', 'representation'
            ],
            'Task': [
                'task', 'problem', 'application', 'scenario', 'challenge',
                'prediction', 'classification', 'reasoning', 'analysis',
                # 中文关键词
                '分析', '预测', '识别', '检测', '推荐', '系统', '任务'
            ],
            'Metric': [
                'metric', 'measure', 'score', 'rate', 'accuracy', 'precision',
                'recall', 'performance', 'quality', 'efficiency'
            ]
        }
        
        # 命名模式（正则表达式）
        self.type_patterns = {
            'Algorithm': [
                r'^Graph[A-Z][a-zA-Z]*$',      # GraphSAGE, GraphSAINT
                r'^[A-Z]{2,}$',                # GAT, GCN, GNN
                r'.*[Aa]lgorithm$',            # PageRankAlgorithm
                r'.*[Ss]earch$',               # BreadthFirstSearch
                r'.*[Nn]et$',                  # ResNet, DenseNet
                r'.*SAGE$',                    # GraphSAGE
            ],
            'Framework': [
                r'.*[Ff]ramework$',            # TensorFlow
                r'.*[Nn]etwork$',              # Neural Network
                r'.*[Ss]ystem$',               # RecommendationSystem
                r'.*[Ll]ibrary$',              # GraphLibrary
            ],
            'Task': [
                r'.*[Pp]rediction$',           # LinkPrediction
                r'.*[Cc]lassification$',       # NodeClassification
                r'.*[Aa]nalysis$',             # 社交网络分析
                r'.*[Rr]ecognition$',          # PatternRecognition
                # 中文模式
                r'.*分析$',                     # 社交网络分析
                r'.*预测$',                     # 分子性质预测
                r'.*系统$',                     # 推荐系统
                r'.*图谱$',                     # 知识图谱
            ],
            'Technique': [
                r'.*[Pp]runing$',              # NetworkPruning
                r'.*[Cc]ompression$',          # ModelCompression
                r'.*[Ee]mbedding$',            # GraphEmbedding
            ]
        }
        
        # 上下文指示词
        self.context_indicators = {
            'Algorithm': [
                'algorithm', 'method', 'approach', 'technique',
                'implements', 'proposes', 'introduces', 'develops',
                'solves', 'optimizes', 'searches', 'computes'
            ],
            'Framework': [
                'framework', 'library', 'platform', 'toolkit',
                'based on', 'built on', 'uses', 'leverages',
                'powered by', 'implemented in'
            ],
            'Task': [
                'task', 'problem', 'application', 'scenario',
                'used for', 'applied to', 'addresses', 'tackles',
                'solves', 'handles', 'performs'
            ],
            'Technique': [
                'technique', 'strategy', 'mechanism', 'process',
                'applies', 'employs', 'utilizes', 'adopts'
            ]
        }
    
    def infer_entity_type(self, entity_name: str, context: str = "") -> InferenceResult:
        """分层实体类型推断"""
        start_time = time.time()
        
        # 第1层：硬匹配缓存（最快）
        cached_result = self._cache_lookup(entity_name)
        if cached_result:
            return InferenceResult(
                entity_type=cached_result['type'],
                confidence=cached_result['confidence'],
                method='cache',
                inference_time=time.time() - start_time
            )
        
        # 第2层：模式匹配（快）
        pattern_result = self._pattern_match(entity_name)
        if pattern_result:
            return InferenceResult(
                entity_type=pattern_result,
                confidence=0.8,
                method='pattern',
                inference_time=time.time() - start_time
            )
        
        # 第3层：关键词匹配（中等）
        keyword_result = self._keyword_match(entity_name)
        if keyword_result:
            return InferenceResult(
                entity_type=keyword_result,
                confidence=0.7,
                method='keyword',
                inference_time=time.time() - start_time
            )
        
        # 第4层：上下文推断（慢）
        if context:
            context_result = self._context_infer(entity_name, context)
            if context_result:
                return InferenceResult(
                    entity_type=context_result,
                    confidence=0.6,
                    method='context',
                    inference_time=time.time() - start_time
                )
        
        # 第5层：未知类型（交给LLM处理）
        return InferenceResult(
            entity_type=None,
            confidence=0.0,
            method='unknown',
            inference_time=time.time() - start_time
        )
    
    def _cache_lookup(self, entity_name: str) -> Optional[Dict]:
        """缓存查找"""
        cached = self.entity_cache.get(entity_name)
        if cached and cached['confidence'] > self.entity_cache.confidence_threshold:
            return cached
        return None
    
    def _pattern_match(self, entity_name: str) -> Optional[str]:
        """基于命名模式的类型推断"""
        for entity_type, patterns in self.type_patterns.items():
            for pattern in patterns:
                if re.match(pattern, entity_name, re.IGNORECASE):
                    return entity_type
        return None
    
    def _keyword_match(self, entity_name: str) -> Optional[str]:
        """基于关键词的类型推断"""
        entity_lower = entity_name.lower()
        
        # 计算每种类型的匹配分数
        type_scores = defaultdict(int)
        
        for entity_type, keywords in self.type_keywords.items():
            for keyword in keywords:
                if keyword in entity_lower:
                    # 根据匹配长度给分
                    score = len(keyword)
                    type_scores[entity_type] += score
        
        if type_scores:
            # 返回得分最高的类型
            best_type = max(type_scores.items(), key=lambda x: x[1])
            return best_type[0]
        
        return None
    
    def _context_infer(self, entity_name: str, context: str) -> Optional[str]:
        """基于上下文的类型推断"""
        context_lower = context.lower()
        
        # 计算上下文指示词匹配分数
        type_scores = defaultdict(int)
        
        for entity_type, indicators in self.context_indicators.items():
            for indicator in indicators:
                if indicator in context_lower:
                    type_scores[entity_type] += 1
        
        if type_scores:
            # 返回得分最高的类型
            best_type = max(type_scores.items(), key=lambda x: x[1])
            return best_type[0]
        
        return None
    
    def update_cache_from_validation(self, entity_name: str, entity_type: str, 
                                   confidence: float, source: str):
        """从验证结果更新缓存"""
        self.entity_cache.add_verified_entity(entity_name, entity_type, confidence, source)
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        total_entities = len(self.entity_cache.verified_entities)
        high_freq_count = len([e for e in self.entity_cache.verified_entities.values() if e['count'] >= 3])
        
        return {
            'total_cached_entities': total_entities,
            'high_frequency_entities': high_freq_count,
            'cache_hit_potential': high_freq_count / total_entities if total_entities > 0 else 0
        }

# 向后兼容的接口
class EntityTypeInferer(EnhancedEntityTypeInferer):
    """向后兼容的实体类型推断器"""
    
    def _infer_type_from_name(self, entity_name: str) -> Optional[str]:
        """向后兼容的方法"""
        result = self.infer_entity_type(entity_name)
        return result.entity_type
