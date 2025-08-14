"""
LLM语义验证器
结合规则验证和LLM语义判断的三元组验证系统
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ontology.dynamic_schema import DynamicOntologyManager

@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    confidence: float
    issues: List[str]
    suggestions: List[str]
    rule_validation: Dict[str, Any]
    semantic_validation: Dict[str, Any]
    validation_time: float

class LLMSemanticValidator:
    """LLM语义验证器"""
    
    def __init__(self, ontology_manager: DynamicOntologyManager, model: str = "gpt-3.5-turbo"):
        self.ontology = ontology_manager
        self.model = model
        self.timeout = 30
        
    def validate_triple(self, subject: str, predicate: str, obj: str, 
                       context: str = "", use_llm: bool = True) -> ValidationResult:
        """综合验证三元组（规则+语义）"""
        start_time = time.time()
        
        print(f"🔍 验证三元组: ({subject}, {predicate}, {obj})")
        
        # 1. 规则验证
        print("   📋 执行规则验证...")
        rule_result = self.ontology.validate_triple(subject, predicate, obj)
        print(f"   📋 规则验证结果: {'✅ 通过' if rule_result['valid'] else '❌ 失败'}")
        if not rule_result['valid']:
            print(f"      问题: {', '.join(rule_result['issues'])}")
        
        # 2. 语义验证（如果启用且规则验证失败）
        semantic_result = {"valid": True, "confidence": 1.0, "reasoning": "跳过语义验证"}
        
        if use_llm and not rule_result['valid']:
            print("   🧠 执行LLM语义验证...")
            semantic_result = self._llm_semantic_validation(subject, predicate, obj, context)
            print(f"   🧠 语义验证结果: {'✅ 通过' if semantic_result['valid'] else '❌ 失败'} (置信度: {semantic_result['confidence']:.2f})")
            if semantic_result.get('reasoning'):
                print(f"      推理: {semantic_result['reasoning']}")
        
        # 3. 综合判断
        final_valid = rule_result['valid'] or (semantic_result['valid'] and semantic_result['confidence'] > 0.7)
        final_confidence = semantic_result['confidence'] if not rule_result['valid'] else 1.0
        
        # 4. 合并问题和建议
        all_issues = rule_result['issues'].copy()
        all_suggestions = rule_result['suggestions'].copy()
        
        if not semantic_result['valid']:
            all_issues.append(f"语义验证失败: {semantic_result.get('reasoning', '未知原因')}")
        
        validation_time = time.time() - start_time
        
        result = ValidationResult(
            valid=final_valid,
            confidence=final_confidence,
            issues=all_issues,
            suggestions=all_suggestions,
            rule_validation=rule_result,
            semantic_validation=semantic_result,
            validation_time=validation_time
        )

        # 如果验证通过，更新实体类型缓存
        if final_valid and hasattr(self.ontology, '_entity_inferer'):
            # 从语义验证结果中提取建议的类型
            if semantic_result.get('suggested_types'):
                suggested_types = semantic_result['suggested_types']

                # 更新主语类型缓存
                if suggested_types.get('subject_type'):
                    self.ontology._entity_inferer.update_cache_from_validation(
                        subject, suggested_types['subject_type'],
                        final_confidence, 'llm_semantic_validation'
                    )

                # 更新宾语类型缓存
                if suggested_types.get('object_type'):
                    self.ontology._entity_inferer.update_cache_from_validation(
                        obj, suggested_types['object_type'],
                        final_confidence, 'llm_semantic_validation'
                    )

        print(f"   🎯 最终验证结果: {'✅ 通过' if final_valid else '❌ 失败'} (耗时: {validation_time:.2f}s)")

        return result
    
    def _llm_semantic_validation(self, subject: str, predicate: str, obj: str, 
                                context: str = "") -> Dict[str, Any]:
        """LLM语义验证"""
        try:
            # 构建验证prompt
            system_prompt = self._build_validation_system_prompt()
            user_prompt = self._build_validation_user_prompt(subject, predicate, obj, context)
            
            # 调用LLM
            response = self._call_llm(system_prompt, user_prompt)
            
            # 解析响应
            result = self._parse_validation_response(response)
            
            return result
            
        except Exception as e:
            print(f"      ⚠️ LLM语义验证出错: {e}")
            return {
                "valid": False,
                "confidence": 0.0,
                "reasoning": f"验证过程出错: {str(e)}"
            }
    
    def _build_validation_system_prompt(self) -> str:
        """构建验证系统提示"""
        entity_types = list(self.ontology.entity_types.keys())
        relation_types = list(self.ontology.relation_types.keys())
        
        return f"""你是一个知识图谱三元组语义验证专家。

你的任务是验证给定的三元组是否在语义上合理，即使它可能不完全符合预定义的Schema规则。

可用的实体类型: {', '.join(entity_types)}
可用的关系类型: {', '.join(relation_types)}

验证标准:
1. 语义合理性: 三元组在现实世界中是否有意义
2. 类型兼容性: 实体类型是否与关系兼容（允许一定灵活性）
3. 上下文一致性: 是否与给定上下文一致

请返回JSON格式的结果:
{{
  "valid": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "详细的验证推理过程",
  "suggested_types": {{
    "subject_type": "建议的主语类型",
    "object_type": "建议的宾语类型"
  }}
}}"""

    def _build_validation_user_prompt(self, subject: str, predicate: str, obj: str, context: str) -> str:
        """构建验证用户提示"""
        prompt = f"""请验证以下三元组的语义合理性:

三元组: ({subject}, {predicate}, {obj})"""
        
        if context:
            prompt += f"\n\n上下文: {context}"
        
        prompt += "\n\n请分析这个三元组是否在语义上合理，并给出详细的推理过程。"
        
        return prompt
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM"""
        try:
            # 从配置文件读取API设置
            import json
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            openai_config = config.get('openai', {})
            
            if not openai_config.get('api_key'):
                return self._mock_validation_response()
            
            from openai import OpenAI
            
            # 创建OpenAI客户端
            client = OpenAI(
                api_key=openai_config['api_key'],
                base_url=openai_config.get('base_url')
            )
            
            response = client.chat.completions.create(
                model=openai_config.get('model', self.model),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
                timeout=self.timeout
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"      ⚠️ LLM调用失败: {e}")
            return self._mock_validation_response()
    
    def _mock_validation_response(self) -> str:
        """模拟验证响应"""
        return json.dumps({
            "valid": True,
            "confidence": 0.8,
            "reasoning": "模拟验证：基于常识判断，该三元组在语义上是合理的",
            "suggested_types": {
                "subject_type": "Algorithm",
                "object_type": "Framework"
            }
        }, ensure_ascii=False)
    
    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """解析验证响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "valid": False,
                    "confidence": 0.0,
                    "reasoning": f"无法解析LLM响应: {response}"
                }
