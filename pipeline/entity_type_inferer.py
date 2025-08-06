"""
实体类型推断模块
从三元组数据中推断实体类型
"""

from typing import Dict, List, Set, Optional
from collections import defaultdict, Counter

class EntityTypeInferer:
    """实体类型推断器"""
    
    def __init__(self):
        self.known_types = {
            'Paradigm', 'Algorithm', 'Technique', 'Framework', 'Task', 'Metric', 'Boolean'
        }
        
        # 关键词映射
        self.type_keywords = {
            'Algorithm': [
                'algorithm', 'search', 'learning', 'neural', 'tree', 'walk', 'ranking',
                'minerva', 'grail', 'gnn_rl', 'neuralp', 'ant_colony', 'greedy', 'monte_carlo'
            ],
            'Paradigm': [
                'paradigm', 'decision', 'learning', 'inference', 'mechanism', 'search',
                'sequential_decision', 'divide_and_conquer', 'probabilistic_inference',
                'reinforcement_learning', 'attention_mechanism', 'representation_learning',
                'heuristic_search', 'planning'
            ],
            'Technique': [
                'technique', 'pruning', 'compression', 'computing', 'bottleneck',
                'information_bottleneck', 'embedding_compression', 'approximate_computing',
                'incremental_computing', 'rl_agent_pruning_strategy'
            ],
            'Framework': [
                'framework', 'neural', 'network', 'reinforcement', 'contrastive',
                'graph_neural_network', 'graph_reinforcement_learning', 
                'graph_contrastive_learning'
            ],
            'Task': [
                'task', 'reasoning', 'prediction', 'classification', 'qa',
                'graph_sparse_reasoning', 'relation_prediction', 'game_ai_reasoning',
                'node_classification', 'complex_kg_qa', 'presampling_largckg'
            ],
            'Metric': [
                'metric', 'reduction', 'accuracy', 'confidence', 'path', 'cost',
                'explainability', 'exploration', 'reward', 'quality',
                'compute_reduction', 'accuracy_retention', 'relation_confidence'
            ]
        }
    
    def infer_entity_types_from_triples(self, triples: List[Dict]) -> Dict[str, str]:
        """从三元组列表推断所有实体的类型"""
        entity_type_votes = defaultdict(Counter)
        
        # 第一轮：从is_instance_of关系直接获取类型
        for triple in triples:
            predicate = triple.get('predicate', '').lower()
            subject = triple.get('subject', '')
            obj = triple.get('object', '')
            
            if predicate == 'is_instance_of':
                # 直接类型声明
                if obj in self.known_types:
                    entity_type_votes[subject][obj] += 10  # 高权重
                    
        # 第二轮：从名称关键词推断
        all_entities = set()
        for triple in triples:
            all_entities.add(triple.get('subject', ''))
            obj = triple.get('object', '')
            if not self._is_literal_value(obj):
                all_entities.add(obj)
        
        for entity in all_entities:
            inferred_type = self._infer_type_from_name(entity)
            if inferred_type:
                entity_type_votes[entity][inferred_type] += 5  # 中等权重
        
        # 第三轮：从关系模式推断
        for triple in triples:
            predicate = triple.get('predicate', '').lower()
            subject = triple.get('subject', '')
            obj = triple.get('object', '')
            
            # 基于谓词模式推断主语类型
            if predicate == 'uses_paradigm' and not self._is_literal_value(obj):
                entity_type_votes[subject]['Algorithm'] += 3
                if obj in self.known_types:
                    entity_type_votes[obj]['Paradigm'] += 3
            
            elif predicate == 'implements':
                entity_type_votes[subject]['Technique'] += 3
                entity_type_votes[obj]['Algorithm'] += 2
            
            elif predicate == 'builds_on':
                entity_type_votes[obj]['Framework'] += 3
            
            elif predicate == 'has_algorithm':
                entity_type_votes[subject]['Task'] += 3
                entity_type_votes[obj]['Algorithm'] += 2
                
            elif predicate in ['reduces_computation_by', 'maintains_accuracy']:
                entity_type_votes[subject]['Technique'] += 2
                
            elif predicate in ['has_advantage', 'has_challenge']:
                entity_type_votes[obj]['Metric'] += 2
        
        # 决定最终类型
        final_types = {}
        for entity, votes in entity_type_votes.items():
            if votes:
                final_types[entity] = votes.most_common(1)[0][0]
            else:
                final_types[entity] = 'Unknown'
        
        # 为没有投票的实体分配Unknown
        for entity in all_entities:
            if entity not in final_types:
                final_types[entity] = 'Unknown'
        
        return final_types
    
    def _infer_type_from_name(self, entity_name: str) -> Optional[str]:
        """从实体名称推断类型"""
        name_lower = entity_name.lower()
        
        # 计算每个类型的匹配分数
        scores = {}
        for type_name, keywords in self.type_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in name_lower:
                    score += len(keyword)  # 长匹配获得更高分数
            scores[type_name] = score
        
        # 返回得分最高的类型，如果得分为0则返回None
        if scores:
            best_type = max(scores, key=scores.get)
            if scores[best_type] > 0:
                return best_type
        
        return None
    
    def _is_literal_value(self, value: str) -> bool:
        """判断值是否为字面值"""
        if not isinstance(value, str):
            return True
            
        literal_patterns = [
            lambda v: '%' in v,
            lambda v: v.lower() in ['true', 'false'],
            lambda v: v.replace('.', '').replace('-', '').isdigit(),
            lambda v: len(v.split()) > 3
        ]
        return any(pattern(value) for pattern in literal_patterns)
    
    def get_entity_type_summary(self, entity_types: Dict[str, str]) -> Dict[str, int]:
        """获取实体类型统计摘要"""
        return dict(Counter(entity_types.values()))
    
    def validate_entity_types(self, entity_types: Dict[str, str], triples: List[Dict]) -> Dict[str, List[str]]:
        """验证推断的实体类型，返回可能的问题"""
        issues = defaultdict(list)
        
        for triple in triples:
            subject = triple.get('subject', '')
            predicate = triple.get('predicate', '').lower()
            obj = triple.get('object', '')
            
            if predicate == 'is_instance_of' and obj in self.known_types:
                # 检查是否与直接声明的类型一致
                declared_type = obj
                inferred_type = entity_types.get(subject, 'Unknown')
                if inferred_type != declared_type:
                    issues[subject].append(f"推断类型({inferred_type})与声明类型({declared_type})不一致")
        
        return dict(issues) 