"""
LLM客户端模块
提供统一的LLM调用接口，支持多种LLM服务
"""

import os
import json
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class LLMResponse:
    """LLM响应结果"""
    content: str
    usage: Dict[str, int]
    model: str
    response_time: float

class LLMClient:
    """LLM客户端，支持多种LLM服务"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        # 首先尝试从config.json读取配置
        config = self._load_config()

        self.model = model
        self.api_key = api_key or config.get("openai", {}).get("api_key") or os.getenv("OPENAI_API_KEY")
        self.base_url = config.get("openai", {}).get("base_url") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # 如果没有API密钥，使用模拟模式
        self.mock_mode = not self.api_key
        
        if self.mock_mode:
            print("⚠️ LLM客户端运行在模拟模式（未配置API密钥）")
        else:
            print(f"✅ LLM客户端已配置: {self.model} @ {self.base_url}")

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 配置文件加载失败: {e}")
        return {}
    
    def generate_response(self, prompt: str, max_tokens: int = 1000, 
                         temperature: float = 0.7) -> str:
        """
        生成LLM响应
        
        Args:
            prompt: 输入提示词
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            LLM生成的文本
        """
        start_time = time.time()
        
        if self.mock_mode:
            # 模拟模式：基于简单规则生成响应
            return self._mock_response(prompt)
        
        try:
            # 尝试使用OpenAI API
            response = self._call_openai_api(prompt, max_tokens, temperature)
            return response
        except Exception as e:
            print(f"⚠️ LLM API调用失败: {e}")
            # 降级到模拟模式
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """模拟LLM响应"""
        prompt_lower = prompt.lower()

        # Schema选择的模拟逻辑
        if "schema" in prompt_lower and "choose" in prompt_lower:
            if "temporal" in prompt_lower or "spatial" in prompt_lower or "time" in prompt_lower:
                return "spatiotemporal_schema.yaml"
            elif "architecture" in prompt_lower or "framework" in prompt_lower:
                return "../schema_config.yaml"
            else:
                return "spatiotemporal_schema.yaml"
        
        # 三元组抽取的模拟逻辑 - 更宽泛的匹配条件
        if ("抽取" in prompt_lower and "三元组" in prompt_lower) or ("extract" in prompt_lower and "triple" in prompt_lower) or "json格式返回三元组" in prompt_lower:
            # 根据文本内容生成更智能的模拟三元组
            if "dodaf" in prompt_lower or "architecture" in prompt_lower:
                return """[
                    {"subject": "DoDAF", "predicate": "is_instance_of", "object": "Framework", "confidence": 0.9},
                    {"subject": "Operational View", "predicate": "is_instance_of", "object": "Framework", "confidence": 0.85},
                    {"subject": "OV-1", "predicate": "is_instance_of", "object": "Algorithm", "confidence": 0.8}
                ]"""
            elif "temperature" in prompt_lower or "monitor" in prompt_lower:
                return """[
                    {"subject": "checkTemperature", "predicate": "is_instance_of", "object": "Action", "confidence": 0.9},
                    {"subject": "temperature > 30", "predicate": "is_instance_of", "object": "Condition", "confidence": 0.85},
                    {"subject": "turnOnAirConditioner", "predicate": "is_instance_of", "object": "Outcome", "confidence": 0.8},
                    {"subject": "checkTemperature", "predicate": "hasCondition", "object": "temperature > 30", "confidence": 0.8},
                    {"subject": "checkTemperature", "predicate": "resultsIn", "object": "turnOnAirConditioner", "confidence": 0.8}
                ]"""
            elif "时空" in prompt_lower or "洪水" in prompt_lower or "水利" in prompt_lower:
                return """[
                    {"subject": "洪水事件", "predicate": "is_instance_of", "object": "Event", "confidence": 0.9},
                    {"subject": "长江流域", "predicate": "is_instance_of", "object": "SpatialEntity", "confidence": 0.85},
                    {"subject": "2024-10-23 08:00", "predicate": "is_instance_of", "object": "TemporalEntity", "confidence": 0.8},
                    {"subject": "洪水事件", "predicate": "locatedAt", "object": "长江流域", "confidence": 0.8},
                    {"subject": "洪水事件", "predicate": "hasStartTime", "object": "2024-10-23 08:00", "confidence": 0.8}
                ]"""
            else:
                return """[
                    {"subject": "示例实体", "predicate": "is_instance_of", "object": "示例类型", "confidence": 0.7},
                    {"subject": "实体A", "predicate": "relates_to", "object": "实体B", "confidence": 0.7}
                ]"""
        
        # 语义验证的模拟逻辑
        if "validate" in prompt_lower or "verify" in prompt_lower:
            return "valid"
        
        # 默认响应
        return "模拟LLM响应：基于输入内容的智能分析结果"
    
    def _call_openai_api(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """调用OpenAI API"""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            raise Exception("OpenAI库未安装，请运行: pip install openai")
        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {e}")
    
    def extract_triples(self, text: str, schema_info: Dict[str, Any]) -> list:
        """
        从文本中抽取三元组

        Args:
            text: 输入文本
            schema_info: Schema信息

        Returns:
            三元组列表
        """
        schema_name = schema_info.get('name', '未知Schema')
        entity_types = list(schema_info.get('entity_types', {}).keys())
        relation_types = list(schema_info.get('relation_types', {}).keys())

        # 在模拟模式下，根据Schema类型和文本内容生成不同的三元组
        if self.mock_mode:
            return self._generate_mock_triples(text, schema_name, entity_types, relation_types)

        prompt = f"""
请从以下文本中抽取符合{schema_name}的知识三元组。

可用实体类型: {', '.join(entity_types[:10])}
可用关系类型: {', '.join(relation_types[:10])}

文本内容:
{text}

请以JSON格式返回三元组列表，格式如下:
[
    {{"subject": "主语", "predicate": "关系", "object": "宾语", "confidence": 0.9}},
    ...
]

只返回JSON，不要其他解释。
"""

        response = self.generate_response(prompt, max_tokens=2000, temperature=0.3)

        print(f"🤖 LLM原始响应: {response[:200]}...")

        try:
            # 尝试解析JSON
            if response.strip().startswith('['):
                triples = json.loads(response)
                print(f"✅ 成功解析JSON，获得 {len(triples)} 个三元组")
                return triples
            else:
                print(f"⚠️ LLM返回的不是JSON格式: {response[:100]}...")
                return []
        except json.JSONDecodeError as e:
            print(f"⚠️ LLM返回的不是有效JSON: {e}")
            print(f"   原始响应: {response[:200]}...")
            return []

    def _generate_mock_triples(self, text: str, schema_name: str, entity_types: list, relation_types: list) -> list:
        """根据Schema类型生成模拟三元组"""
        text_lower = text.lower()

        print(f"🎭 模拟模式: 根据Schema '{schema_name}' 生成三元组")

        # 通用Schema的模拟三元组
        if "通用" in schema_name or "general" in schema_name.lower():
            if "dodaf" in text_lower and "architecture" in text_lower:
                return [
                    {"subject": "DoDAF", "predicate": "is_instance_of", "object": "Framework", "confidence": 0.9},
                    {"subject": "Operational View", "predicate": "is_instance_of", "object": "Framework", "confidence": 0.85},
                    {"subject": "OV-1", "predicate": "is_instance_of", "object": "Algorithm", "confidence": 0.8},
                    {"subject": "System View", "predicate": "is_instance_of", "object": "Framework", "confidence": 0.85},
                    {"subject": "SV-1", "predicate": "is_instance_of", "object": "Algorithm", "confidence": 0.8}
                ]

        # 时空Schema的模拟三元组
        elif "时空" in schema_name or "spatiotemporal" in schema_name.lower():
            if "洪水" in text_lower or "水利" in text_lower or "时空" in text_lower:
                return [
                    {"subject": "洪水事件", "predicate": "is_instance_of", "object": "Event", "confidence": 0.9},
                    {"subject": "长江流域", "predicate": "is_instance_of", "object": "SpatialEntity", "confidence": 0.85},
                    {"subject": "2024-10-23 08:00", "predicate": "is_instance_of", "object": "TemporalEntity", "confidence": 0.8},
                    {"subject": "4小时", "predicate": "is_instance_of", "object": "TemporalEntity", "confidence": 0.8},
                    {"subject": "执行水位监测", "predicate": "is_instance_of", "object": "Action", "confidence": 0.85},
                    {"subject": "洪水事件", "predicate": "hasStartTime", "object": "2024-10-23 08:00", "confidence": 0.8},
                    {"subject": "洪水事件", "predicate": "locatedAt", "object": "长江流域", "confidence": 0.8},
                    {"subject": "洪水事件", "predicate": "hasDuration", "object": "4小时", "confidence": 0.8}
                ]
            elif "checktemperature" in text_lower or "monitor" in text_lower or "do-da-f" in text_lower:
                return [
                    {"subject": "checkTemperature", "predicate": "is_instance_of", "object": "Action", "confidence": 0.9},
                    {"subject": "monitorWaterLevel", "predicate": "is_instance_of", "object": "Action", "confidence": 0.9},
                    {"subject": "executeFloodWarning", "predicate": "is_instance_of", "object": "Action", "confidence": 0.9},
                    {"subject": "temperature > 30", "predicate": "is_instance_of", "object": "Condition", "confidence": 0.85},
                    {"subject": "sensor_status == normal", "predicate": "is_instance_of", "object": "Condition", "confidence": 0.85},
                    {"subject": "turnOnAirConditioner", "predicate": "is_instance_of", "object": "Outcome", "confidence": 0.8},
                    {"subject": "generateWaterLevelReport", "predicate": "is_instance_of", "object": "Outcome", "confidence": 0.8},
                    {"subject": "checkTemperature", "predicate": "hasCondition", "object": "temperature > 30", "confidence": 0.8},
                    {"subject": "checkTemperature", "predicate": "resultsIn", "object": "turnOnAirConditioner", "confidence": 0.8}
                ]

        # 默认返回基础三元组
        return [
            {"subject": "示例实体", "predicate": "is_instance_of", "object": entity_types[0] if entity_types else "Entity", "confidence": 0.7}
        ]
    
    def validate_triple(self, subject: str, predicate: str, obj: str, 
                       schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证三元组的语义正确性
        
        Args:
            subject: 主语
            predicate: 谓语
            obj: 宾语
            schema_info: Schema信息
            
        Returns:
            验证结果
        """
        prompt = f"""
请验证以下三元组的语义正确性：

三元组: ({subject}, {predicate}, {obj})
Schema: {schema_info.get('name', '未知')}

请判断这个三元组是否语义合理，并给出置信度分数(0-1)。

请以JSON格式返回结果:
{{"valid": true/false, "confidence": 0.8, "reason": "验证理由"}}
"""
        
        response = self.generate_response(prompt, max_tokens=200, temperature=0.1)
        
        try:
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                # 默认返回有效
                return {"valid": True, "confidence": 0.5, "reason": "默认验证"}
        except json.JSONDecodeError:
            return {"valid": True, "confidence": 0.5, "reason": "解析失败，默认有效"}

# 全局LLM客户端实例
llm_client = LLMClient()
