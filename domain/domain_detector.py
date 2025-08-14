"""
领域检测器
基于文本内容自动检测所属领域
"""

import re
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass

from domain.domain_template import DomainTemplateManager, template_manager

@dataclass
class DomainDetectionResult:
    """领域检测结果"""
    domain_name: str
    confidence: float
    method: str  # 'keyword', 'pattern', 'context', 'hybrid'
    evidence: List[str]  # 支持证据

class DomainDetector:
    """基于文本内容自动检测领域"""
    
    def __init__(self, template_manager: DomainTemplateManager = None):
        if template_manager is None:
            from domain.domain_template import template_manager as default_manager
            self.template_manager = default_manager
        else:
            self.template_manager = template_manager
        self.domain_classifiers = {}
        self._build_classifiers()
    
    def _build_classifiers(self):
        """构建各领域的分类器"""
        for domain_name in self.template_manager.list_templates():
            template = self.template_manager.get_template(domain_name)
            if template:
                self.domain_classifiers[domain_name] = {
                    'keywords': self._flatten_keywords(template.keywords),
                    'patterns': self._flatten_patterns(template.patterns),
                    'context_indicators': self._flatten_context_indicators(template.context_indicators)
                }
    
    def _flatten_keywords(self, keywords: Dict[str, List[str]]) -> List[str]:
        """展平关键词字典"""
        all_keywords = []
        for keyword_list in keywords.values():
            all_keywords.extend(keyword_list)
        return list(set(all_keywords))
    
    def _flatten_patterns(self, patterns: Dict[str, List[str]]) -> List[str]:
        """展平模式字典"""
        all_patterns = []
        for pattern_list in patterns.values():
            all_patterns.extend(pattern_list)
        return list(set(all_patterns))
    
    def _flatten_context_indicators(self, context_indicators: Dict[str, List[str]]) -> List[str]:
        """展平上下文指示词字典"""
        all_indicators = []
        for indicator_list in context_indicators.values():
            all_indicators.extend(indicator_list)
        return list(set(all_indicators))
    
    def detect_domain(self, text: str, top_k: int = 3) -> List[DomainDetectionResult]:
        """检测文本所属领域及置信度"""
        text_lower = text.lower()
        domain_scores = {}
        domain_evidence = defaultdict(list)
        
        # 方法1：关键词频率分析
        keyword_scores = self._keyword_based_detection(text_lower, domain_evidence)
        
        # 方法2：模式匹配分析
        pattern_scores = self._pattern_based_detection(text, domain_evidence)
        
        # 方法3：上下文指示词分析
        context_scores = self._context_based_detection(text_lower, domain_evidence)
        
        # 加权融合
        for domain in self.domain_classifiers.keys():
            domain_scores[domain] = (
                0.4 * keyword_scores.get(domain, 0) +
                0.3 * pattern_scores.get(domain, 0) +
                0.3 * context_scores.get(domain, 0)
            )
        
        # 排序并返回top_k结果
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for domain_name, score in sorted_domains[:top_k]:
            if score > 0:  # 只返回有得分的领域
                results.append(DomainDetectionResult(
                    domain_name=domain_name,
                    confidence=min(score, 1.0),  # 确保置信度不超过1.0
                    method='hybrid',
                    evidence=domain_evidence[domain_name][:5]  # 最多5个证据
                ))
        
        return results
    
    def _keyword_based_detection(self, text_lower: str, evidence: Dict) -> Dict[str, float]:
        """基于关键词的领域检测"""
        scores = {}
        
        for domain_name, classifier in self.domain_classifiers.items():
            keywords = classifier['keywords']
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                # 计算得分：匹配关键词数 / 总关键词数
                score = len(matched_keywords) / len(keywords)
                scores[domain_name] = score
                evidence[domain_name].extend([f"关键词: {kw}" for kw in matched_keywords[:3]])
        
        return scores
    
    def _pattern_based_detection(self, text: str, evidence: Dict) -> Dict[str, float]:
        """基于模式匹配的领域检测"""
        scores = {}
        
        # 提取文本中的专有名词（简单的启发式方法）
        # 匹配大写字母开头的词、连字符词、缩写等
        potential_entities = re.findall(r'\b[A-Z][a-zA-Z]*(?:[A-Z][a-zA-Z]*)*\b|\b[A-Z]{2,}\b|\w+[-_]\w+', text)
        
        for domain_name, classifier in self.domain_classifiers.items():
            patterns = classifier['patterns']
            matched_patterns = []
            
            for entity in potential_entities:
                for pattern in patterns:
                    try:
                        if re.match(pattern, entity, re.IGNORECASE):
                            matched_patterns.append(f"{entity}({pattern})")
                            break
                    except re.error:
                        continue  # 忽略无效的正则表达式
            
            if matched_patterns:
                # 计算得分：匹配实体数 / 潜在实体数
                score = len(matched_patterns) / max(len(potential_entities), 1)
                scores[domain_name] = min(score, 1.0)
                evidence[domain_name].extend([f"模式: {mp}" for mp in matched_patterns[:3]])
        
        return scores
    
    def _context_based_detection(self, text_lower: str, evidence: Dict) -> Dict[str, float]:
        """基于上下文指示词的领域检测"""
        scores = {}
        
        for domain_name, classifier in self.domain_classifiers.items():
            indicators = classifier['context_indicators']
            matched_indicators = []
            
            for indicator in indicators:
                if indicator.lower() in text_lower:
                    matched_indicators.append(indicator)
            
            if matched_indicators:
                # 计算得分：匹配指示词数 / 总指示词数
                score = len(matched_indicators) / len(indicators)
                scores[domain_name] = score
                evidence[domain_name].extend([f"上下文: {ind}" for ind in matched_indicators[:3]])
        
        return scores
    
    def detect_domain_simple(self, text: str) -> Optional[str]:
        """简单的领域检测，返回最可能的领域"""
        results = self.detect_domain(text, top_k=1)
        if results and results[0].confidence > 0.1:  # 最低置信度阈值
            return results[0].domain_name
        return None
    
    def get_domain_suggestions(self, text: str) -> Dict[str, str]:
        """获取领域建议和理由"""
        results = self.detect_domain(text, top_k=3)
        suggestions = {}
        
        for result in results:
            template = self.template_manager.get_template(result.domain_name)
            if template:
                reason = f"置信度: {result.confidence:.2f}, 证据: {', '.join(result.evidence[:2])}"
                suggestions[template.display_name] = reason
        
        return suggestions
    
    def add_domain_feedback(self, text: str, correct_domain: str, user_feedback: str = ""):
        """添加用户反馈以改进检测（为未来的机器学习做准备）"""
        # 这里可以记录用户反馈，用于后续的模型训练
        feedback_data = {
            'text': text,
            'predicted_domains': [r.domain_name for r in self.detect_domain(text)],
            'correct_domain': correct_domain,
            'user_feedback': user_feedback,
            'timestamp': __import__('time').time()
        }
        
        # 可以保存到文件或数据库中
        print(f"📝 记录用户反馈: {correct_domain} (预测: {feedback_data['predicted_domains']})")
    
    def update_classifiers(self):
        """更新分类器（当模板发生变化时调用）"""
        self._build_classifiers()
        print("🔄 领域分类器已更新")

# 全局领域检测器实例
domain_detector = DomainDetector()
