"""
三元组清理模块
负责对原始三元组数据进行标准化和清理
"""

import re
import csv
import json
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import pandas as pd

# 移除已删除的静态schema导入
# from ontology.schema import RelationType, EntityType

@dataclass
class CleaningRule:
    """清理规则定义"""
    rule_type: str  # "normalize", "filter", "transform"
    pattern: Optional[str] = None
    replacement: Optional[str] = None
    condition: Optional[callable] = None

class TripleCleaner:
    """三元组清理器"""
    
    def __init__(self):
        self.cleaning_rules = self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> List[CleaningRule]:
        """初始化默认清理规则"""
        return [
            # 标准化实体名称（去除多余空格，统一下划线）
            CleaningRule("normalize", r"\s+", "_"),
            CleaningRule("normalize", r"[^\w\-_]", ""),
            
            # 过滤无效三元组
            CleaningRule("filter", condition=lambda triple: len(triple) == 3),
            CleaningRule("filter", condition=lambda triple: all(str(item).strip() for item in triple)),
        ]
    
    def clean_triples(self, raw_triples: List[Union[Tuple, Dict, List]]) -> List[Dict]:
        """清理三元组列表"""
        cleaned_triples = []
        
        for raw_triple in raw_triples:
            try:
                # 标准化三元组格式
                standardized = self._standardize_triple_format(raw_triple)
                if not standardized:
                    continue
                
                # 应用清理规则
                cleaned = self._apply_cleaning_rules(standardized)
                if cleaned:
                    cleaned_triples.append(cleaned)
                    
            except Exception as e:
                print(f"清理三元组时出错: {raw_triple}, 错误: {e}")
                continue
        
        return cleaned_triples
    
    def _standardize_triple_format(self, triple: Union[Tuple, Dict, List]) -> Optional[Dict]:
        """标准化三元组格式为字典"""
        try:
            if isinstance(triple, dict):
                # 已经是字典格式
                return {
                    "subject": str(triple.get("subject", "")),
                    "predicate": str(triple.get("predicate", "")),
                    "object": str(triple.get("object", "")),
                    "confidence": float(triple.get("confidence", 1.0)),
                    "source": str(triple.get("source", "unknown"))
                }
            elif isinstance(triple, (tuple, list)) and len(triple) >= 3:
                # 元组或列表格式
                result = {
                    "subject": str(triple[0]),
                    "predicate": str(triple[1]), 
                    "object": str(triple[2]),
                    "confidence": 1.0,
                    "source": "unknown"
                }
                
                # 如果有更多字段
                if len(triple) > 3:
                    try:
                        result["confidence"] = float(triple[3])
                    except:
                        pass
                if len(triple) > 4:
                    result["source"] = str(triple[4])
                
                return result
            else:
                return None
        except Exception:
            return None
    
    def _apply_cleaning_rules(self, triple_dict: Dict) -> Optional[Dict]:
        """应用清理规则到三元组"""
        try:
            # 应用标准化规则
            triple_dict["subject"] = self._normalize_entity_name(triple_dict["subject"])
            triple_dict["predicate"] = self._normalize_predicate_name(triple_dict["predicate"])
            triple_dict["object"] = self._normalize_entity_name(triple_dict["object"])
            
            # 验证三元组有效性
            if not self._is_valid_triple(triple_dict):
                return None
                
            return triple_dict
            
        except Exception:
            return None
    
    def _normalize_entity_name(self, name: str) -> str:
        """标准化实体名称"""
        # 去除首尾空格
        name = name.strip()
        # 替换多个空格为单个下划线
        name = re.sub(r'\s+', '_', name)
        # 去除特殊字符，保留字母数字下划线连字符
        name = re.sub(r'[^\w\-_]', '', name)
        # 首字母大写
        return name.replace('_', ' ').title().replace(' ', '_')
    
    def _normalize_predicate_name(self, predicate: str) -> str:
        """标准化谓词名称"""
        predicate = predicate.strip().lower()
        # 替换空格为下划线
        predicate = re.sub(r'\s+', '_', predicate)
        return predicate
    
    def _is_valid_triple(self, triple_dict: Dict) -> bool:
        """验证三元组是否有效"""
        # 检查必要字段是否存在且非空
        required_fields = ["subject", "predicate", "object"]
        for field in required_fields:
            if not triple_dict.get(field) or not str(triple_dict[field]).strip():
                return False
        
        # 检查置信度是否在有效范围内
        confidence = triple_dict.get("confidence", 1.0)
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            return False
            
        return True
    
    def load_from_csv(self, csv_file: str) -> List[Dict]:
        """从CSV文件加载并清理三元组"""
        try:
            df = pd.read_csv(csv_file)
            raw_triples = df.to_dict('records')
            return self.clean_triples(raw_triples)
        except Exception as e:
            print(f"从CSV加载三元组失败: {e}")
            return []
    
    def save_to_csv(self, cleaned_triples: List[Dict], output_file: str):
        """保存清理后的三元组到CSV文件"""
        try:
            df = pd.DataFrame(cleaned_triples)
            df.to_csv(output_file, index=False)
            print(f"已保存 {len(cleaned_triples)} 个清理后的三元组到 {output_file}")
        except Exception as e:
            print(f"保存三元组到CSV失败: {e}")

# 使用示例
if __name__ == "__main__":
    from data.sample_triples import SAMPLE_TRIPLES, DETAILED_TRIPLES
    
    cleaner = TripleCleaner()
    
    # 清理示例数据
    cleaned = cleaner.clean_triples(SAMPLE_TRIPLES)
    print(f"清理了 {len(cleaned)} 个三元组")
    
    # 显示前几个清理后的三元组
    for i, triple in enumerate(cleaned[:5]):
        print(f"{i+1}: {triple}") 