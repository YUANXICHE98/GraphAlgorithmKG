"""
LLM知识图谱抽取器 v2.0
集成动态Schema和Prompt模板
"""

import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ontology.managers.dynamic_schema import DynamicOntologyManager
from pipeline.llm_validator import LLMSemanticValidator
from pipeline.stage_saver import stage_saver

@dataclass
class ExtractionResult:
    """抽取结果"""
    success: bool
    triples: List[Dict] = None
    new_entities: List[str] = None
    new_relations: List[str] = None
    processing_time: float = 0.0
    error_message: str = ""

class LLMKGExtractor:
    """LLM知识图谱抽取器 v2.0"""
    
    def __init__(self, ontology_manager: DynamicOntologyManager, model: str = "gpt-3.5-turbo"):
        self.ontology = ontology_manager
        self.model = model
        self.max_retries = 3
        self.timeout = 30
        self.validator = LLMSemanticValidator(ontology_manager, model)
    
    def extract_from_text(self, text: str, chunk_id: str = "", save_stages: bool = True) -> ExtractionResult:
        """从文本中抽取知识三元组"""
        start_time = time.time()

        try:
            # 获取动态生成的Prompt
            prompts = self.ontology.get_llm_extraction_prompt(text)

            # 调用LLM（这里需要根据你的LLM接口实现）
            response = self._call_llm(prompts["system"], prompts["user"])

            # 解析响应
            result = self._parse_llm_response(response)

            # 保存原始抽取结果
            if save_stages and result.get("triples"):
                raw_metadata = {
                    "text_length": len(text),
                    "chunk_id": chunk_id,
                    "model": self.model,
                    "llm_response_time": time.time() - start_time
                }
                stage_saver.save_stage("raw_extraction", result.get("triples", []), raw_metadata)

                # 创建手工审核文件
                review_file = stage_saver.create_manual_review_file(
                    "LLM原始抽取",
                    result.get("triples", [])
                )
                print(f"📋 手工审核文件: {review_file}")
            
            # 验证抽取的三元组（规则+语义）
            validated_triples = []
            for triple in result.get("triples", []):
                validation = self.validator.validate_triple(
                    triple["subject"],
                    triple["predicate"],
                    triple["object"],
                    context=text[:200],  # 提供上下文
                    use_llm=True
                )

                if validation.valid:
                    # 添加验证信息到三元组
                    triple["validation_confidence"] = validation.confidence
                    triple["validation_method"] = "rule+semantic" if not validation.rule_validation["valid"] else "rule"
                    validated_triples.append(triple)
                else:
                    print(f"⚠️  三元组最终验证失败: {triple}")
                    print(f"   问题: {', '.join(validation.issues)}")

            # 保存验证后的三元组
            if save_stages and validated_triples:
                validation_metadata = {
                    "original_count": len(result.get("triples", [])),
                    "validated_count": len(validated_triples),
                    "validation_rate": len(validated_triples) / len(result.get("triples", [])) if result.get("triples") else 0,
                    "chunk_id": chunk_id
                }
                stage_saver.save_stage("validated_triples", validated_triples, validation_metadata)

            processing_time = time.time() - start_time
            
            return ExtractionResult(
                success=True,
                triples=validated_triples,
                new_entities=result.get("new_entities", []),
                new_relations=result.get("new_relations", []),
                processing_time=processing_time
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM接口"""
        try:
            # 从配置文件读取API设置
            import json
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            openai_config = config.get('openai', {})
            
            if not openai_config.get('api_key'):
                print("⚠️  未配置OpenAI API密钥，使用模拟响应")
                return self._mock_llm_response()
            
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
                max_tokens=4000,
                timeout=self.timeout
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"⚠️  LLM调用失败: {e}")
            print("使用模拟响应继续测试...")
            return self._mock_llm_response()
    
    def _mock_llm_response(self) -> str:
        """模拟LLM响应（用于测试）"""
        return json.dumps({
            "triples": [
                {
                    "subject": "MINERVA",
                    "predicate": "is_instance_of",
                    "object": "Algorithm",
                    "confidence": 0.9,
                    "evidence": "MINERVA is a reinforcement learning algorithm"
                }
            ],
            "new_entities": [],
            "new_relations": []
        }, ensure_ascii=False)
    
    def _parse_llm_response(self, response: str) -> Dict:
        """解析LLM响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError(f"无法解析LLM响应: {response}")
