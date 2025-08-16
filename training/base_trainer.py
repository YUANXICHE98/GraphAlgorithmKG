"""
训练模型基础框架
提供统一的训练接口和模型管理
"""

import os
import json
import pickle
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class TrainingConfig:
    """训练配置"""
    model_name: str
    model_type: str  # schema_classifier, entity_inferer, relation_extractor, entity_merger
    training_data_path: str
    validation_data_path: Optional[str]
    output_model_path: str
    hyperparameters: Dict[str, Any]
    training_metadata: Dict[str, Any]

@dataclass
class TrainingResult:
    """训练结果"""
    model_path: str
    training_time: float
    final_accuracy: float
    validation_accuracy: Optional[float]
    training_history: List[Dict[str, float]]
    model_metadata: Dict[str, Any]

class BaseTrainer(ABC):
    """训练器基类"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.model = None
        self.training_history = []
        
        # 确保输出目录存在
        Path(config.output_model_path).parent.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def prepare_data(self) -> Tuple[Any, Any, Any, Any]:
        """
        准备训练数据
        Returns: (X_train, y_train, X_val, y_val)
        """
        pass
    
    @abstractmethod
    def build_model(self) -> Any:
        """构建模型"""
        pass
    
    @abstractmethod
    def train_model(self, X_train: Any, y_train: Any, X_val: Any, y_val: Any) -> TrainingResult:
        """训练模型"""
        pass
    
    @abstractmethod
    def evaluate_model(self, X_test: Any, y_test: Any) -> Dict[str, float]:
        """评估模型"""
        pass
    
    def save_model(self, model_path: str = None) -> str:
        """保存模型"""
        if model_path is None:
            model_path = self.config.output_model_path
        
        # 保存模型
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # 保存元数据
        metadata = {
            'model_name': self.config.model_name,
            'model_type': self.config.model_type,
            'training_time': datetime.now().isoformat(),
            'hyperparameters': self.config.hyperparameters,
            'training_history': self.training_history,
            'config': self.config.__dict__
        }
        
        metadata_path = model_path.replace('.pkl', '_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"💾 模型已保存: {model_path}")
        print(f"📋 元数据已保存: {metadata_path}")
        
        return model_path
    
    def load_model(self, model_path: str) -> Any:
        """加载模型"""
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        # 加载元数据
        metadata_path = model_path.replace('.pkl', '_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                self.training_history = metadata.get('training_history', [])
        
        print(f"📂 模型已加载: {model_path}")
        return self.model
    
    def run_full_training(self) -> TrainingResult:
        """运行完整的训练流程"""
        print(f"🚀 开始训练模型: {self.config.model_name}")
        print(f"📋 模型类型: {self.config.model_type}")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # 1. 准备数据
        print("📊 准备训练数据...")
        X_train, y_train, X_val, y_val = self.prepare_data()
        train_size = X_train.shape[0] if hasattr(X_train, 'shape') else len(X_train) if X_train is not None else 0
        val_size = X_val.shape[0] if hasattr(X_val, 'shape') else len(X_val) if X_val is not None else 0
        print(f"   训练集大小: {train_size}")
        print(f"   验证集大小: {val_size}")
        
        # 2. 构建模型
        print("🏗️ 构建模型...")
        self.model = self.build_model()
        
        # 3. 训练模型
        print("🎯 开始训练...")
        result = self.train_model(X_train, y_train, X_val, y_val)
        
        # 4. 保存模型
        print("💾 保存模型...")
        model_path = self.save_model()
        result.model_path = model_path
        
        training_time = (datetime.now() - start_time).total_seconds()
        result.training_time = training_time
        
        print(f"✅ 训练完成!")
        print(f"   ⏱️ 训练时间: {training_time:.2f}s")
        print(f"   📈 最终准确率: {result.final_accuracy:.4f}")
        if result.validation_accuracy:
            print(f"   📊 验证准确率: {result.validation_accuracy:.4f}")
        print("=" * 80)
        
        return result

class TrainingDataManager:
    """训练数据管理器"""
    
    def __init__(self, data_dir: str = "training/data/raw"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_schema_training_data(self) -> str:
        """收集Schema分类训练数据"""
        print("📊 收集Schema分类训练数据...")
        
        # 从会话记录中收集数据
        sessions_dir = Path("results/sessions")
        training_data = []
        
        if sessions_dir.exists():
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir() and session_dir.name != "latest":
                    try:
                        # 读取文档输入
                        doc_input_file = session_dir / "01_document_input.json"
                        schema_detection_file = session_dir / "02_schema_detection.json"
                        
                        if doc_input_file.exists() and schema_detection_file.exists():
                            with open(doc_input_file, 'r', encoding='utf-8') as f:
                                doc_data = json.load(f)
                            
                            with open(schema_detection_file, 'r', encoding='utf-8') as f:
                                schema_data = json.load(f)
                            
                            # 构建训练样本
                            sample = {
                                'text': doc_data['data']['content'],
                                'schema': schema_data['data']['selected_schema'],
                                'session_id': session_dir.name
                            }
                            training_data.append(sample)
                    
                    except Exception as e:
                        print(f"⚠️ 处理会话 {session_dir.name} 失败: {e}")
        
        # 保存训练数据
        output_file = self.data_dir / "schema_classification_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 收集到 {len(training_data)} 个Schema分类样本")
        print(f"💾 保存到: {output_file}")
        
        return str(output_file)
    
    def collect_entity_training_data(self) -> str:
        """收集实体推断训练数据"""
        print("📊 收集实体推断训练数据...")
        
        sessions_dir = Path("results/sessions")
        training_data = []
        
        if sessions_dir.exists():
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir() and session_dir.name != "latest":
                    try:
                        # 读取实体推断结果
                        entity_file = session_dir / "04_entity_inference.json"
                        
                        if entity_file.exists():
                            with open(entity_file, 'r', encoding='utf-8') as f:
                                entity_data = json.load(f)
                            
                            # 提取实体训练样本
                            for entity in entity_data['data']['entities']:
                                sample = {
                                    'entity_name': entity['name'],
                                    'entity_type': entity['type'],
                                    'confidence': entity['confidence'],
                                    'schema': entity['schema'],
                                    'properties': entity['properties'],
                                    'session_id': session_dir.name
                                }
                                training_data.append(sample)
                    
                    except Exception as e:
                        print(f"⚠️ 处理会话 {session_dir.name} 失败: {e}")
        
        # 保存训练数据
        output_file = self.data_dir / "entity_inference_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 收集到 {len(training_data)} 个实体推断样本")
        print(f"💾 保存到: {output_file}")
        
        return str(output_file)
    
    def collect_relation_training_data(self) -> str:
        """收集关系抽取训练数据"""
        print("📊 收集关系抽取训练数据...")
        
        sessions_dir = Path("results/sessions")
        training_data = []
        
        if sessions_dir.exists():
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir() and session_dir.name != "latest":
                    try:
                        # 读取三元组抽取结果
                        triple_file = session_dir / "03_triple_extraction.json"
                        
                        if triple_file.exists():
                            with open(triple_file, 'r', encoding='utf-8') as f:
                                triple_data = json.load(f)
                            
                            # 提取关系训练样本
                            for triple in triple_data['data']['triples']:
                                sample = {
                                    'subject': triple['subject'],
                                    'predicate': triple['predicate'],
                                    'object': triple['object'],
                                    'confidence': triple.get('confidence', 0.8),
                                    'method': triple.get('method', 'unknown'),
                                    'session_id': session_dir.name
                                }
                                training_data.append(sample)
                    
                    except Exception as e:
                        print(f"⚠️ 处理会话 {session_dir.name} 失败: {e}")
        
        # 保存训练数据
        output_file = self.data_dir / "relation_extraction_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 收集到 {len(training_data)} 个关系抽取样本")
        print(f"💾 保存到: {output_file}")
        
        return str(output_file)

# 全局训练数据管理器
training_data_manager = TrainingDataManager()
