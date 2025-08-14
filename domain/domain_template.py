"""
领域模板系统
支持多领域知识图谱构建的模板化管理
"""

import yaml
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class DomainTemplate:
    """领域模板定义"""
    domain_name: str
    display_name: str
    description: str
    entity_types: Dict[str, Dict] = field(default_factory=dict)
    relation_types: Dict[str, Dict] = field(default_factory=dict)
    keywords: Dict[str, List[str]] = field(default_factory=dict)
    patterns: Dict[str, List[str]] = field(default_factory=dict)
    external_resources: Dict[str, str] = field(default_factory=dict)
    context_indicators: Dict[str, List[str]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'domain_name': self.domain_name,
            'display_name': self.display_name,
            'description': self.description,
            'entity_types': self.entity_types,
            'relation_types': self.relation_types,
            'keywords': self.keywords,
            'patterns': self.patterns,
            'external_resources': self.external_resources,
            'context_indicators': self.context_indicators
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DomainTemplate':
        """从字典创建模板"""
        return cls(**data)

class DomainTemplateManager:
    """领域模板管理器"""
    
    def __init__(self, templates_dir: str = "domain/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[str, DomainTemplate] = {}
        self._load_all_templates()
    
    def _load_all_templates(self):
        """加载所有领域模板"""
        for template_file in self.templates_dir.glob("*.yaml"):
            try:
                domain_name = template_file.stem
                template = self.load_template(domain_name)
                if template:
                    self.templates[domain_name] = template
                    print(f"✅ 加载领域模板: {template.display_name}")
            except Exception as e:
                print(f"⚠️ 加载模板失败 {template_file}: {e}")
    
    def load_template(self, domain_name: str) -> Optional[DomainTemplate]:
        """加载指定领域模板"""
        template_file = self.templates_dir / f"{domain_name}.yaml"
        
        if not template_file.exists():
            print(f"⚠️ 模板文件不存在: {template_file}")
            return None
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            return DomainTemplate.from_dict(data)
            
        except Exception as e:
            print(f"❌ 加载模板失败: {e}")
            return None
    
    def save_template(self, template: DomainTemplate):
        """保存领域模板"""
        template_file = self.templates_dir / f"{template.domain_name}.yaml"
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                yaml.dump(template.to_dict(), f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            self.templates[template.domain_name] = template
            print(f"✅ 保存领域模板: {template.display_name}")
            
        except Exception as e:
            print(f"❌ 保存模板失败: {e}")
    
    def get_template(self, domain_name: str) -> Optional[DomainTemplate]:
        """获取领域模板"""
        return self.templates.get(domain_name)
    
    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        return list(self.templates.keys())
    
    def create_template_from_existing(self, source_domain: str, 
                                    new_domain: str, 
                                    display_name: str,
                                    description: str) -> DomainTemplate:
        """基于现有模板创建新模板"""
        source_template = self.get_template(source_domain)
        if not source_template:
            raise ValueError(f"源模板不存在: {source_domain}")
        
        new_template = DomainTemplate(
            domain_name=new_domain,
            display_name=display_name,
            description=description,
            entity_types=source_template.entity_types.copy(),
            relation_types=source_template.relation_types.copy(),
            keywords=source_template.keywords.copy(),
            patterns=source_template.patterns.copy(),
            external_resources={},
            context_indicators=source_template.context_indicators.copy()
        )
        
        return new_template
    
    def merge_templates(self, template_names: List[str], 
                       merged_name: str,
                       display_name: str) -> DomainTemplate:
        """合并多个模板"""
        merged_template = DomainTemplate(
            domain_name=merged_name,
            display_name=display_name,
            description=f"合并模板: {', '.join(template_names)}"
        )
        
        for template_name in template_names:
            template = self.get_template(template_name)
            if not template:
                continue
            
            # 合并实体类型
            merged_template.entity_types.update(template.entity_types)
            
            # 合并关系类型
            merged_template.relation_types.update(template.relation_types)
            
            # 合并关键词
            for entity_type, keywords in template.keywords.items():
                if entity_type in merged_template.keywords:
                    merged_template.keywords[entity_type].extend(keywords)
                    # 去重
                    merged_template.keywords[entity_type] = list(set(merged_template.keywords[entity_type]))
                else:
                    merged_template.keywords[entity_type] = keywords.copy()
            
            # 合并模式
            for entity_type, patterns in template.patterns.items():
                if entity_type in merged_template.patterns:
                    merged_template.patterns[entity_type].extend(patterns)
                    merged_template.patterns[entity_type] = list(set(merged_template.patterns[entity_type]))
                else:
                    merged_template.patterns[entity_type] = patterns.copy()
            
            # 合并上下文指示词
            for entity_type, indicators in template.context_indicators.items():
                if entity_type in merged_template.context_indicators:
                    merged_template.context_indicators[entity_type].extend(indicators)
                    merged_template.context_indicators[entity_type] = list(set(merged_template.context_indicators[entity_type]))
                else:
                    merged_template.context_indicators[entity_type] = indicators.copy()
        
        return merged_template
    
    def export_template_summary(self) -> Dict[str, Any]:
        """导出模板摘要"""
        summary = {
            'total_templates': len(self.templates),
            'templates': {}
        }
        
        for domain_name, template in self.templates.items():
            summary['templates'][domain_name] = {
                'display_name': template.display_name,
                'description': template.description,
                'entity_types_count': len(template.entity_types),
                'relation_types_count': len(template.relation_types),
                'keywords_count': sum(len(keywords) for keywords in template.keywords.values()),
                'patterns_count': sum(len(patterns) for patterns in template.patterns.values())
            }
        
        return summary

# 创建默认的图算法模板
def create_graph_algorithms_template() -> DomainTemplate:
    """创建图算法领域模板"""
    return DomainTemplate(
        domain_name="graph_algorithms",
        display_name="图算法",
        description="图算法和图神经网络相关的知识领域",
        entity_types={
            "Algorithm": {
                "description": "算法实体",
                "examples": ["GraphSAGE", "PageRank", "Dijkstra"]
            },
            "Framework": {
                "description": "框架实体", 
                "examples": ["Graph Neural Networks", "TensorFlow"]
            },
            "Task": {
                "description": "任务实体",
                "examples": ["Node Classification", "Link Prediction"]
            }
        },
        relation_types={
            "is_instance_of": {
                "description": "实例关系",
                "subject_types": ["Algorithm", "Framework"],
                "object_types": ["Algorithm", "Framework"]
            },
            "builds_on": {
                "description": "构建关系",
                "subject_types": ["Algorithm"],
                "object_types": ["Framework", "Algorithm"]
            },
            "used_in": {
                "description": "应用关系",
                "subject_types": ["Algorithm", "Framework"],
                "object_types": ["Task"]
            }
        },
        keywords={
            "Algorithm": ["algorithm", "method", "approach", "search", "optimization"],
            "Framework": ["framework", "network", "neural", "system", "platform"],
            "Task": ["task", "problem", "prediction", "classification", "analysis", "分析", "预测", "系统"]
        },
        patterns={
            "Algorithm": [r"^Graph[A-Z][a-zA-Z]*$", r"^[A-Z]{2,}$", r".*[Aa]lgorithm$"],
            "Framework": [r".*[Ff]ramework$", r".*[Nn]etwork$", r".*[Ss]ystem$"],
            "Task": [r".*[Pp]rediction$", r".*[Cc]lassification$", r".*分析$", r".*预测$", r".*系统$"]
        },
        external_resources={
            "wikipedia": "https://en.wikipedia.org/wiki/Category:Graph_algorithms",
            "arxiv": "cs.DS,cs.LG"
        },
        context_indicators={
            "Algorithm": ["algorithm", "method", "implements", "proposes", "solves"],
            "Framework": ["framework", "based on", "built on", "uses", "leverages"],
            "Task": ["task", "used for", "applied to", "addresses", "tackles"]
        }
    )

# 创建DoDAF模板
def create_dodaf_template() -> DomainTemplate:
    """创建DoDAF领域模板"""
    return DomainTemplate(
        domain_name="dodaf",
        display_name="DoDAF架构框架",
        description="美国国防部架构框架相关知识领域",
        entity_types={
            "Architecture": {
                "description": "架构实体",
                "examples": ["Enterprise Architecture", "System Architecture"]
            },
            "View": {
                "description": "视图实体",
                "examples": ["Operational View", "System View", "Technical View"]
            },
            "Model": {
                "description": "模型实体",
                "examples": ["OV-1", "SV-1", "TV-1"]
            },
            "Stakeholder": {
                "description": "利益相关者",
                "examples": ["User", "Developer", "Operator"]
            }
        },
        relation_types={
            "contains": {
                "description": "包含关系",
                "subject_types": ["Architecture", "View"],
                "object_types": ["View", "Model"]
            },
            "supports": {
                "description": "支持关系",
                "subject_types": ["Model", "View"],
                "object_types": ["Stakeholder", "Architecture"]
            }
        },
        keywords={
            "Architecture": ["architecture", "framework", "enterprise", "system"],
            "View": ["view", "perspective", "operational", "system", "technical"],
            "Model": ["model", "diagram", "specification", "ov-", "sv-", "tv-"],
            "Stakeholder": ["stakeholder", "user", "operator", "developer", "customer"]
        },
        patterns={
            "Model": [r"^[A-Z]{2}-\d+$", r".*[Mm]odel$", r".*[Dd]iagram$"],
            "View": [r".*[Vv]iew$", r".*[Pp]erspective$"],
            "Architecture": [r".*[Aa]rchitecture$", r".*[Ff]ramework$"]
        },
        external_resources={
            "dodaf_spec": "https://dodcio.defense.gov/Library/DoD-Architecture-Framework/",
            "togaf": "https://www.opengroup.org/togaf"
        },
        context_indicators={
            "Architecture": ["architecture", "framework", "enterprise", "design"],
            "View": ["view", "perspective", "operational", "technical"],
            "Model": ["model", "diagram", "specification", "represents"],
            "Stakeholder": ["stakeholder", "user", "customer", "interested"]
        }
    )

# 全局模板管理器实例
template_manager = DomainTemplateManager()
