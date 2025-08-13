"""
动态本体模式管理系统 v2.0
基于YAML配置文件的统一Schema管理
"""

import json
import yaml
from typing import Dict, List, Set, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict
import re

@dataclass
class EntityTypeConfig:
    """实体类型配置"""
    name: str
    description: str
    examples: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    color: str = "#CCCCCC"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0

@dataclass
class RelationTypeConfig:
    """关系类型配置"""
    name: str
    description: str
    examples: List[str] = field(default_factory=list)
    subject_types: List[str] = field(default_factory=list)
    object_types: List[str] = field(default_factory=list)
    is_symmetric: bool = False
    inverse_relation: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    is_boolean: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0

@dataclass
class Entity:
    """实体实例"""
    name: str
    entity_type: str
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class Relation:
    """关系实例"""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

class DynamicOntologyManager:
    """动态本体管理器 v2.0"""
    
    def __init__(self, schema_config_path: str = "ontology/schema_config.yaml"):
        self.schema_config_path = Path(schema_config_path)

        # 本体配置
        self.entity_types: Dict[str, EntityTypeConfig] = {}
        self.relation_types: Dict[str, RelationTypeConfig] = {}
        self.expansion_config: Dict = {}
        self.llm_prompts: Dict = {}

        # 实际数据存储
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []

        # 版本和元数据
        self.metadata: Dict = {}
        self.current_version = "2.0.0"

        # 统计信息
        self.processing_stats = {
            "processed_triples": 0,
            "last_update_at": None,
            "pending_entities": defaultdict(int),
            "pending_relations": defaultdict(int)
        }

        # 加载Schema配置
        self._load_schema_config()
    
    def _load_schema_config(self):
        """从YAML配置文件加载Schema"""
        if not self.schema_config_path.exists():
            raise FileNotFoundError(f"Schema配置文件不存在: {self.schema_config_path}")
        
        with open(self.schema_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 加载元数据
        self.metadata = config.get('metadata', {})
        self.current_version = self.metadata.get('version', '2.0.0')
        
        # 加载实体类型
        for name, entity_config in config.get('entity_types', {}).items():
            self.entity_types[name] = EntityTypeConfig(
                name=name,
                **entity_config
            )
        
        # 加载关系类型
        for name, relation_config in config.get('relation_types', {}).items():
            self.relation_types[name] = RelationTypeConfig(
                name=name,
                **relation_config
            )
        
        # 加载扩展配置
        self.expansion_config = config.get('expansion_config', {})
        
        # 加载LLM Prompt模板
        self.llm_prompts = config.get('llm_prompts', {})
        
        print(f"✅ 已加载Schema配置: {self.metadata.get('name', 'Unknown')} v{self.current_version}")
        print(f"   实体类型: {len(self.entity_types)}")
        print(f"   关系类型: {len(self.relation_types)}")
    
    def get_llm_extraction_prompt(self, text: str) -> Dict[str, str]:
        """获取LLM抽取的完整Prompt"""
        # 生成实体类型描述
        entity_descriptions = []
        for name, config in self.entity_types.items():
            desc = f"- **{name}**: {config.description}"
            if config.examples:
                desc += f"\n  示例: {', '.join(config.examples[:3])}"
            entity_descriptions.append(desc)
        
        # 生成关系类型描述
        relation_descriptions = []
        for name, config in self.relation_types.items():
            desc = f"- **{name}**: {config.description}"
            if config.examples:
                desc += f"\n  示例: {config.examples[0]}"
            if config.subject_types and config.subject_types != ["*"]:
                desc += f"\n  主语类型: {', '.join(config.subject_types)}"
            if config.object_types and config.object_types != ["*"]:
                desc += f"\n  宾语类型: {', '.join(config.object_types)}"
            relation_descriptions.append(desc)
        
        # 格式化Prompt
        system_prompt = self.llm_prompts.get('extraction_system_prompt', '').format(
            entity_types_description='\n'.join(entity_descriptions),
            relation_types_description='\n'.join(relation_descriptions)
        )
        
        user_prompt = self.llm_prompts.get('extraction_user_prompt', '').format(
            text=text
        )
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    def validate_triple(self, subject: str, predicate: str, obj: str) -> Dict[str, Any]:
        """验证三元组是否符合Schema约束"""
        validation_result = {
            "valid": True,
            "issues": [],
            "suggestions": []
        }
        
        # 检查关系类型是否存在
        if predicate not in self.relation_types:
            validation_result["valid"] = False
            validation_result["issues"].append(f"未知关系类型: {predicate}")
            # 寻找相似关系
            similar_relations = self._find_similar_relations(predicate)
            if similar_relations:
                validation_result["suggestions"].extend(
                    [f"建议使用: {rel}" for rel in similar_relations[:3]]
                )
        else:
            relation_config = self.relation_types[predicate]
            
            # 检查主语类型约束
            subject_type = self._identify_entity_type(subject)
            if (relation_config.subject_types and 
                relation_config.subject_types != ["*"] and
                subject_type not in relation_config.subject_types):
                validation_result["valid"] = False
                validation_result["issues"].append(
                    f"主语类型不匹配: {subject}({subject_type}) 不在允许的类型 {relation_config.subject_types} 中"
                )
            
            # 检查宾语类型约束
            if not self._is_literal(obj):
                object_type = self._identify_entity_type(obj)
                if (relation_config.object_types and 
                    relation_config.object_types != ["*"] and
                    object_type not in relation_config.object_types):
                    validation_result["valid"] = False
                    validation_result["issues"].append(
                        f"宾语类型不匹配: {obj}({object_type}) 不在允许的类型 {relation_config.object_types} 中"
                    )
        
        return validation_result
    
    def _find_similar_relations(self, relation: str) -> List[str]:
        """查找相似的关系类型"""
        from difflib import SequenceMatcher
        
        similarities = []
        for rel_name in self.relation_types.keys():
            similarity = SequenceMatcher(None, relation.lower(), rel_name.lower()).ratio()
            if similarity > 0.3:
                similarities.append((rel_name, similarity))
        
        return [rel for rel, _ in sorted(similarities, key=lambda x: x[1], reverse=True)]
    
    def _identify_entity_type(self, entity_name: str) -> Optional[str]:
        """识别实体类型"""
        entity_lower = entity_name.lower()

        for type_name, config in self.entity_types.items():
            # 检查关键词
            for keyword in config.keywords:
                if keyword in entity_lower:
                    config.usage_count += 1
                    return type_name

            # 检查正则模式
            for pattern in config.patterns:
                if re.match(pattern, entity_name, re.IGNORECASE):
                    config.usage_count += 1
                    return type_name

        # 如果Schema配置中找不到，尝试使用EntityTypeInferer
        return self._extract_type_from_name(entity_name)

    def _extract_type_from_name(self, entity_name: str) -> Optional[str]:
        """从实体名称提取类型（使用EntityTypeInferer）"""
        from pipeline.entity_type_inferer import EntityTypeInferer
        inferer = EntityTypeInferer()
        return inferer._infer_type_from_name(entity_name)

    def _identify_relation_type(self, predicate: str) -> Optional[str]:
        """识别关系类型"""
        predicate_lower = predicate.lower().strip()

        # 直接匹配
        if predicate in self.relation_types:
            return predicate

        # 模糊匹配
        for relation_name in self.relation_types.keys():
            if predicate_lower == relation_name.lower():
                return relation_name

        # 别名匹配
        for relation_name, config in self.relation_types.items():
            if predicate_lower in [alias.lower() for alias in config.aliases]:
                return relation_name

        # 相似度匹配
        import difflib
        matches = difflib.get_close_matches(predicate_lower,
                                          [r.lower() for r in self.relation_types.keys()],
                                          n=1, cutoff=0.8)
        if matches:
            # 找到对应的原始关系名
            for relation_name in self.relation_types.keys():
                if relation_name.lower() == matches[0]:
                    return relation_name

        return None

    def _is_literal(self, value: str) -> bool:
        """判断是否为字面值"""
        # 数字
        try:
            float(value)
            return True
        except ValueError:
            pass
        
        # 百分比
        if value.endswith('%'):
            return True
        
        # 布尔值
        if value.lower() in ['true', 'false']:
            return True
        
        # 其他字面值模式
        literal_patterns = [
            r'^\d+$',  # 纯数字
            r'^\d+\.\d+$',  # 小数
            r'^".*"$',  # 引号包围
            r"^'.*'$",  # 单引号包围
        ]
        
        for pattern in literal_patterns:
            if re.match(pattern, value):
                return True
        
        return False
    
    def export_schema_documentation(self, output_path: str = "docs/SCHEMA_REFERENCE.md"):
        """导出Schema文档"""
        doc_content = f"""# {self.metadata.get('name', 'Knowledge Graph Schema')}

版本: {self.current_version}  
更新时间: {self.metadata.get('updated_at', 'Unknown')}  
描述: {self.metadata.get('description', '')}

## 实体类型

| 类别 | 说明 | 示例 | 关键词 |
|------|------|------|--------|
"""
        
        for name, config in self.entity_types.items():
            examples = ', '.join(config.examples[:3]) if config.examples else "无"
            keywords = ', '.join(config.keywords[:5]) if config.keywords else "无"
            doc_content += f"| {name} | {config.description} | {examples} | {keywords} |\n"
        
        doc_content += "\n## 关系类型\n\n"
        doc_content += "| 关系 | 语义 | 主语类型 | 宾语类型 | 示例 |\n"
        doc_content += "|------|------|----------|----------|------|\n"
        
        for name, config in self.relation_types.items():
            subject_types = ', '.join(config.subject_types) if config.subject_types else "任意"
            object_types = ', '.join(config.object_types) if config.object_types else "任意"
            example = config.examples[0] if config.examples else "无"
            doc_content += f"| {name} | {config.description} | {subject_types} | {object_types} | {example} |\n"
        
        # 写入文件
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        print(f"📄 Schema文档已导出到: {output_path}")
    
    def get_ontology_summary(self) -> Dict[str, Any]:
        """获取本体摘要"""
        return {
            "metadata": self.metadata,
            "version": self.current_version,
            "entity_types": len(self.entity_types),
            "relation_types": len(self.relation_types),
            "processing_stats": dict(self.processing_stats),
            "expansion_config": self.expansion_config
        }

# 全局实例
DYNAMIC_ONTOLOGY = DynamicOntologyManager() 
