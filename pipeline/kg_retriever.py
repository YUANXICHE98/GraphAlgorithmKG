"""
知识图谱检索模块
支持模糊查询、子图检索、两跳扩展等功能
"""

import json
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from collections import defaultdict, deque
import difflib

from ontology.dynamic_schema import DynamicOntologyManager

@dataclass
class SearchResult:
    """搜索结果"""
    query: str
    matched_entities: List[Dict]
    subgraph: Dict
    relevance_scores: Dict[str, float]
    search_time: float
    total_nodes: int
    total_edges: int

class KGRetriever:
    """知识图谱检索器"""
    
    def __init__(self, ontology: DynamicOntologyManager, storage_path: str = "dynamic_kg_storage"):
        self.ontology = ontology
        self.storage_path = Path(storage_path)
        self.entity_index = {}
        self.relation_index = {}
        self.graph_data = {}
        self._build_search_index()
    
    def _build_search_index(self):
        """构建搜索索引"""
        # 加载图数据
        self._load_graph_data()
        
        # 构建实体索引
        self._build_entity_index()
        
        # 构建关系索引
        self._build_relation_index()
    
    def _load_graph_data(self):
        """加载图数据"""
        try:
            # 加载实体数据
            entities_file = self.storage_path / "entities.json"
            if entities_file.exists():
                with open(entities_file, 'r', encoding='utf-8') as f:
                    entities_data = json.load(f)
                    self.graph_data['entities'] = {
                        entity['name']: entity for entity in entities_data
                    }
            
            # 加载关系数据
            relations_file = self.storage_path / "relations.json"
            if relations_file.exists():
                with open(relations_file, 'r', encoding='utf-8') as f:
                    relations_data = json.load(f)
                    self.graph_data['relations'] = relations_data
            
            # 加载三元组数据
            triples_file = self.storage_path / "triples.json"
            if triples_file.exists():
                with open(triples_file, 'r', encoding='utf-8') as f:
                    self.graph_data['triples'] = json.load(f)
            
        except Exception as e:
            print(f"加载图数据失败: {e}")
            self.graph_data = {'entities': {}, 'relations': [], 'triples': []}
    
    def _build_entity_index(self):
        """构建实体索引"""
        self.entity_index = {
            'by_name': {},
            'by_type': defaultdict(list),
            'by_keywords': defaultdict(set)
        }
        
        entities = self.graph_data.get('entities', {})
        for entity_name, entity_data in entities.items():
            # 按名称索引
            self.entity_index['by_name'][entity_name.lower()] = entity_data
            
            # 按类型索引
            entity_type = entity_data.get('type', 'Unknown')
            self.entity_index['by_type'][entity_type].append(entity_data)
            
            # 按关键词索引
            keywords = self._extract_keywords(entity_name)
            for keyword in keywords:
                self.entity_index['by_keywords'][keyword].add(entity_name)
    
    def _build_relation_index(self):
        """构建关系索引"""
        self.relation_index = {
            'by_type': defaultdict(list),
            'by_entities': defaultdict(list)
        }
        
        triples = self.graph_data.get('triples', [])
        for triple in triples:
            relation_type = triple.get('predicate', '')
            subject = triple.get('subject', '')
            object_entity = triple.get('object', '')
            
            # 按关系类型索引
            self.relation_index['by_type'][relation_type].append(triple)
            
            # 按实体索引
            self.relation_index['by_entities'][subject].append(triple)
            self.relation_index['by_entities'][object_entity].append(triple)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 分割单词
        words = re.findall(r'\w+', text.lower())
        
        # 过滤停用词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def fuzzy_entity_search(self, query: str, threshold: float = 0.6) -> List[Dict]:
        """模糊实体搜索"""
        query_lower = query.lower()
        matched_entities = []
        
        # 1. 精确匹配
        if query_lower in self.entity_index['by_name']:
            entity = self.entity_index['by_name'][query_lower]
            matched_entities.append({
                'entity': entity,
                'match_type': 'exact',
                'similarity': 1.0
            })
        
        # 2. 模糊匹配
        for entity_name, entity_data in self.entity_index['by_name'].items():
            if query_lower != entity_name:
                similarity = difflib.SequenceMatcher(None, query_lower, entity_name).ratio()
                if similarity >= threshold:
                    matched_entities.append({
                        'entity': entity_data,
                        'match_type': 'fuzzy',
                        'similarity': similarity
                    })
        
        # 3. 关键词匹配
        query_keywords = self._extract_keywords(query)
        for keyword in query_keywords:
            if keyword in self.entity_index['by_keywords']:
                for entity_name in self.entity_index['by_keywords'][keyword]:
                    entity_data = self.entity_index['by_name'].get(entity_name.lower())
                    if entity_data and not any(m['entity']['name'] == entity_data['name'] for m in matched_entities):
                        matched_entities.append({
                            'entity': entity_data,
                            'match_type': 'keyword',
                            'similarity': 0.7
                        })
        
        # 按相似度排序
        matched_entities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matched_entities[:10]  # 返回前10个结果
    
    def retrieve_subgraph(self, query: str, hops: int = 2, max_nodes: int = 50) -> SearchResult:
        """检索相关子图"""
        import time
        start_time = time.time()
        
        # 1. 实体匹配
        matched_entities = self.fuzzy_entity_search(query)
        
        if not matched_entities:
            return SearchResult(
                query=query,
                matched_entities=[],
                subgraph={'nodes': [], 'edges': []},
                relevance_scores={},
                search_time=time.time() - start_time,
                total_nodes=0,
                total_edges=0
            )
        
        # 2. 子图扩展
        seed_entities = [match['entity']['name'] for match in matched_entities[:5]]  # 取前5个作为种子
        subgraph = self._expand_subgraph(seed_entities, hops, max_nodes)
        
        # 3. 计算相关性评分
        relevance_scores = self._calculate_relevance_scores(subgraph, query, matched_entities)
        
        # 4. 剪枝优化
        pruned_subgraph = self._prune_subgraph(subgraph, relevance_scores, max_nodes)
        
        search_time = time.time() - start_time
        
        return SearchResult(
            query=query,
            matched_entities=matched_entities,
            subgraph=pruned_subgraph,
            relevance_scores=relevance_scores,
            search_time=search_time,
            total_nodes=len(pruned_subgraph['nodes']),
            total_edges=len(pruned_subgraph['edges'])
        )
    
    def _expand_subgraph(self, seed_entities: List[str], hops: int, max_nodes: int) -> Dict:
        """扩展子图"""
        nodes = {}
        edges = []
        visited = set()
        
        # BFS扩展
        queue = deque([(entity, 0) for entity in seed_entities])
        
        while queue and len(nodes) < max_nodes:
            current_entity, current_hop = queue.popleft()
            
            if current_entity in visited or current_hop > hops:
                continue
            
            visited.add(current_entity)
            
            # 添加节点
            entity_data = self.entity_index['by_name'].get(current_entity.lower())
            if entity_data:
                nodes[current_entity] = entity_data
            
            # 查找相关的三元组
            related_triples = self.relation_index['by_entities'].get(current_entity, [])
            
            for triple in related_triples:
                subject = triple['subject']
                object_entity = triple['object']
                predicate = triple['predicate']
                
                # 添加边
                edge = {
                    'source': subject,
                    'target': object_entity,
                    'relation': predicate,
                    'confidence': triple.get('confidence', 1.0),
                    'metadata': {
                        'source_file': triple.get('source', ''),
                        'evidence': triple.get('evidence', '')
                    }
                }
                edges.append(edge)
                
                # 添加相邻节点到队列
                if current_hop < hops:
                    if subject != current_entity and subject not in visited:
                        queue.append((subject, current_hop + 1))
                    if object_entity != current_entity and object_entity not in visited:
                        queue.append((object_entity, current_hop + 1))
        
        return {
            'nodes': list(nodes.values()),
            'edges': edges
        }
    
    def _calculate_relevance_scores(self, subgraph: Dict, query: str, matched_entities: List[Dict]) -> Dict[str, float]:
        """计算相关性评分"""
        scores = {}
        query_keywords = set(self._extract_keywords(query))
        
        # 为匹配的实体设置高分
        for match in matched_entities:
            entity_name = match['entity']['name']
            scores[entity_name] = match['similarity']
        
        # 为其他节点计算评分
        for node in subgraph['nodes']:
            node_name = node['name']
            if node_name not in scores:
                # 基于关键词匹配
                node_keywords = set(self._extract_keywords(node_name))
                keyword_overlap = len(query_keywords & node_keywords)
                keyword_score = keyword_overlap / max(len(query_keywords), 1)
                
                # 基于节点度数（连接数）
                degree = sum(1 for edge in subgraph['edges'] 
                           if edge['source'] == node_name or edge['target'] == node_name)
                degree_score = min(degree / 10.0, 1.0)  # 归一化
                
                # 综合评分
                scores[node_name] = 0.7 * keyword_score + 0.3 * degree_score
        
        return scores
    
    def _prune_subgraph(self, subgraph: Dict, relevance_scores: Dict[str, float], max_nodes: int) -> Dict:
        """剪枝子图"""
        if len(subgraph['nodes']) <= max_nodes:
            return subgraph
        
        # 按相关性评分排序节点
        sorted_nodes = sorted(
            subgraph['nodes'],
            key=lambda node: relevance_scores.get(node['name'], 0),
            reverse=True
        )
        
        # 保留前max_nodes个节点
        kept_nodes = sorted_nodes[:max_nodes]
        kept_node_names = {node['name'] for node in kept_nodes}
        
        # 过滤边，只保留连接保留节点的边
        kept_edges = [
            edge for edge in subgraph['edges']
            if edge['source'] in kept_node_names and edge['target'] in kept_node_names
        ]
        
        return {
            'nodes': kept_nodes,
            'edges': kept_edges
        }
    
    def get_entity_neighbors(self, entity_name: str, relation_types: Optional[List[str]] = None) -> Dict:
        """获取实体的邻居节点"""
        neighbors = {
            'incoming': [],  # 指向该实体的关系
            'outgoing': []   # 从该实体出发的关系
        }
        
        related_triples = self.relation_index['by_entities'].get(entity_name, [])
        
        for triple in related_triples:
            if relation_types and triple['predicate'] not in relation_types:
                continue
            
            if triple['subject'] == entity_name:
                # 出边
                neighbors['outgoing'].append({
                    'target': triple['object'],
                    'relation': triple['predicate'],
                    'confidence': triple.get('confidence', 1.0)
                })
            elif triple['object'] == entity_name:
                # 入边
                neighbors['incoming'].append({
                    'source': triple['subject'],
                    'relation': triple['predicate'],
                    'confidence': triple.get('confidence', 1.0)
                })
        
        return neighbors
    
    def search_by_relation_pattern(self, pattern: Dict) -> List[Dict]:
        """按关系模式搜索"""
        # 例如: {"subject_type": "Algorithm", "relation": "outperforms", "object_type": "Algorithm"}
        results = []
        
        subject_type = pattern.get('subject_type')
        relation = pattern.get('relation')
        object_type = pattern.get('object_type')
        
        for triple in self.graph_data.get('triples', []):
            match = True
            
            if relation and triple.get('predicate') != relation:
                match = False
            
            if subject_type:
                subject_entity = self.entity_index['by_name'].get(triple.get('subject', '').lower())
                if not subject_entity or subject_entity.get('type') != subject_type:
                    match = False
            
            if object_type:
                object_entity = self.entity_index['by_name'].get(triple.get('object', '').lower())
                if not object_entity or object_entity.get('type') != object_type:
                    match = False
            
            if match:
                results.append(triple)
        
        return results
    
    def get_search_statistics(self) -> Dict:
        """获取搜索统计信息"""
        return {
            'total_entities': len(self.entity_index['by_name']),
            'total_relations': len(self.graph_data.get('triples', [])),
            'entity_types': dict(self.entity_index['by_type']),
            'relation_types': dict(self.relation_index['by_type']),
            'index_size': {
                'entity_keywords': len(self.entity_index['by_keywords']),
                'relation_entities': len(self.relation_index['by_entities'])
            }
        }