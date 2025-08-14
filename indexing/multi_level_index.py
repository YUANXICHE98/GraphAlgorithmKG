"""
多级索引系统
支持高效的实体类型推断和检索
"""

import re
import time
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass
import pickle
import json
from pathlib import Path

@dataclass
class IndexEntry:
    """索引条目"""
    term: str
    entity_type: str
    confidence: float
    source: str  # 'keyword', 'pattern', 'learned'

class InvertedIndex:
    """倒排索引：关键词 -> 实体类型"""
    
    def __init__(self):
        self.index: Dict[str, List[IndexEntry]] = defaultdict(list)
    
    def add(self, term: str, entity_type: str, confidence: float = 1.0, source: str = 'keyword'):
        """添加索引项"""
        term_lower = term.lower()
        entry = IndexEntry(term, entity_type, confidence, source)
        
        # 避免重复添加相同的条目
        existing = [e for e in self.index[term_lower] if e.entity_type == entity_type and e.source == source]
        if not existing:
            self.index[term_lower].append(entry)
    
    def get(self, term: str) -> List[IndexEntry]:
        """获取匹配的索引项"""
        return self.index.get(term.lower(), [])
    
    def search_partial(self, term: str) -> List[IndexEntry]:
        """部分匹配搜索"""
        term_lower = term.lower()
        results = []
        
        for indexed_term, entries in self.index.items():
            if term_lower in indexed_term:
                results.extend(entries)
        
        return results

class TrieNode:
    """前缀树节点"""
    
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.entries: List[IndexEntry] = []
        self.is_end = False

class TrieIndex:
    """前缀树索引：快速前缀匹配"""
    
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, term: str, entity_type: str, confidence: float = 0.8, source: str = 'pattern'):
        """插入词条"""
        node = self.root
        term_lower = term.lower()
        
        for char in term_lower:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end = True
        entry = IndexEntry(term, entity_type, confidence, source)
        node.entries.append(entry)
    
    def search_prefix(self, prefix: str, max_results: int = 10) -> List[IndexEntry]:
        """前缀搜索"""
        node = self.root
        prefix_lower = prefix.lower()
        
        # 找到前缀对应的节点
        for char in prefix_lower:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # 收集所有以该前缀开头的词条
        results = []
        self._collect_entries(node, results, max_results)
        return results
    
    def _collect_entries(self, node: TrieNode, results: List[IndexEntry], max_results: int):
        """递归收集条目"""
        if len(results) >= max_results:
            return
        
        if node.is_end:
            results.extend(node.entries)
        
        for child in node.children.values():
            self._collect_entries(child, results, max_results)

class PatternIndex:
    """模式索引：正则表达式匹配"""
    
    def __init__(self):
        self.patterns: List[Tuple[str, str, float]] = []  # (pattern, entity_type, confidence)
    
    def add_pattern(self, pattern: str, entity_type: str, confidence: float = 0.8):
        """添加模式"""
        try:
            # 验证正则表达式
            re.compile(pattern)
            self.patterns.append((pattern, entity_type, confidence))
        except re.error as e:
            print(f"⚠️ 无效的正则表达式 {pattern}: {e}")
    
    def match(self, term: str) -> List[IndexEntry]:
        """模式匹配"""
        results = []
        
        for pattern, entity_type, confidence in self.patterns:
            try:
                if re.match(pattern, term, re.IGNORECASE):
                    entry = IndexEntry(term, entity_type, confidence, 'pattern')
                    results.append(entry)
            except re.error:
                continue
        
        return results

class MultiLevelIndex:
    """多级索引系统"""
    
    def __init__(self, index_dir: str = "indexing/data"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # 第1级：倒排索引（关键词 -> 实体类型）
        self.inverted_index = InvertedIndex()
        
        # 第2级：前缀树（快速前缀匹配）
        self.trie_index = TrieIndex()
        
        # 第3级：模式索引（正则表达式匹配）
        self.pattern_index = PatternIndex()
        
        # 统计信息
        self.stats = {
            'total_terms': 0,
            'total_patterns': 0,
            'last_updated': time.time()
        }
    
    def build_indexes(self, domain_vocabulary: Dict[str, Dict[str, List[str]]]):
        """构建所有索引"""
        print("🔨 构建多级索引...")
        
        for domain_name, vocabulary in domain_vocabulary.items():
            print(f"  📚 处理领域: {domain_name}")
            
            # 构建关键词索引
            if 'keywords' in vocabulary:
                for entity_type, keywords in vocabulary['keywords'].items():
                    for keyword in keywords:
                        self.inverted_index.add(keyword, entity_type, 1.0, 'keyword')
                        self.trie_index.insert(keyword, entity_type, 0.9, 'keyword')
                        self.stats['total_terms'] += 1
            
            # 构建模式索引
            if 'patterns' in vocabulary:
                for entity_type, patterns in vocabulary['patterns'].items():
                    for pattern in patterns:
                        self.pattern_index.add_pattern(pattern, entity_type, 0.8)
                        self.stats['total_patterns'] += 1
        
        self.stats['last_updated'] = time.time()
        print(f"✅ 索引构建完成: {self.stats['total_terms']} 个词条, {self.stats['total_patterns']} 个模式")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """多级检索"""
        results = []
        query_lower = query.lower()
        
        # 第1级：精确匹配
        exact_matches = self.inverted_index.get(query)
        for entry in exact_matches:
            results.append((entry.entity_type, entry.confidence))
        
        # 第2级：前缀匹配
        if len(results) < top_k:
            prefix_matches = self.trie_index.search_prefix(query, top_k - len(results))
            for entry in prefix_matches:
                results.append((entry.entity_type, entry.confidence * 0.9))  # 稍微降低置信度
        
        # 第3级：模式匹配
        if len(results) < top_k:
            pattern_matches = self.pattern_index.match(query)
            for entry in pattern_matches:
                results.append((entry.entity_type, entry.confidence))
        
        # 第4级：部分匹配
        if len(results) < top_k:
            partial_matches = self.inverted_index.search_partial(query)
            for entry in partial_matches:
                results.append((entry.entity_type, entry.confidence * 0.7))  # 进一步降低置信度
        
        return self._deduplicate_and_rank(results, top_k)
    
    def _deduplicate_and_rank(self, results: List[Tuple[str, float]], top_k: int) -> List[Tuple[str, float]]:
        """去重并排序"""
        # 按实体类型分组，取最高置信度
        type_scores = {}
        for entity_type, confidence in results:
            if entity_type not in type_scores or confidence > type_scores[entity_type]:
                type_scores[entity_type] = confidence
        
        # 排序并返回top_k
        sorted_results = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def add_learned_term(self, term: str, entity_type: str, confidence: float, source: str = 'learned'):
        """添加学习到的词条"""
        self.inverted_index.add(term, entity_type, confidence, source)
        self.trie_index.insert(term, entity_type, confidence, source)
        self.stats['total_terms'] += 1
    
    def batch_update(self, updates: List[Dict]):
        """批量更新索引"""
        for update in updates:
            if update['action'] == 'add':
                self.add_learned_term(
                    update['term'], 
                    update['entity_type'], 
                    update.get('confidence', 0.8),
                    update.get('source', 'learned')
                )
        
        self.stats['last_updated'] = time.time()
        print(f"🔄 批量更新完成: {len(updates)} 项")
    
    def save_indexes(self):
        """保存索引到磁盘"""
        try:
            # 保存倒排索引
            with open(self.index_dir / 'inverted_index.pkl', 'wb') as f:
                pickle.dump(self.inverted_index.index, f)
            
            # 保存前缀树（简化版）
            trie_data = self._serialize_trie()
            with open(self.index_dir / 'trie_index.json', 'w', encoding='utf-8') as f:
                json.dump(trie_data, f, ensure_ascii=False, indent=2)
            
            # 保存模式索引
            with open(self.index_dir / 'pattern_index.json', 'w', encoding='utf-8') as f:
                json.dump(self.pattern_index.patterns, f, ensure_ascii=False, indent=2)
            
            # 保存统计信息
            with open(self.index_dir / 'stats.json', 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            
            print(f"💾 索引已保存到: {self.index_dir}")
            
        except Exception as e:
            print(f"❌ 保存索引失败: {e}")
    
    def load_indexes(self):
        """从磁盘加载索引"""
        try:
            # 加载倒排索引
            inverted_file = self.index_dir / 'inverted_index.pkl'
            if inverted_file.exists():
                with open(inverted_file, 'rb') as f:
                    self.inverted_index.index = pickle.load(f)
            
            # 加载模式索引
            pattern_file = self.index_dir / 'pattern_index.json'
            if pattern_file.exists():
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    self.pattern_index.patterns = json.load(f)
            
            # 加载统计信息
            stats_file = self.index_dir / 'stats.json'
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            
            print(f"📂 索引已加载: {self.stats.get('total_terms', 0)} 个词条")
            
        except Exception as e:
            print(f"❌ 加载索引失败: {e}")
    
    def _serialize_trie(self) -> Dict:
        """序列化前缀树（简化版，只保存叶子节点）"""
        # 这里简化实现，只保存完整词条
        # 实际应用中可以实现完整的前缀树序列化
        return {"note": "Trie serialization simplified"}
    
    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        return {
            **self.stats,
            'inverted_index_size': len(self.inverted_index.index),
            'pattern_count': len(self.pattern_index.patterns)
        }

# 全局多级索引实例
multi_level_index = MultiLevelIndex()
