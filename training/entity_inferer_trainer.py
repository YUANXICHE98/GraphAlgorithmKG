"""
实体推断模型训练器
用于训练更准确的实体类型推断模型
"""

import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from typing import Dict, List, Any, Optional, Tuple
import re

from .base_trainer import BaseTrainer, TrainingConfig, TrainingResult

class EntityInfererTrainer(BaseTrainer):
    """实体推断器训练器"""
    
    def __init__(self, config: TrainingConfig):
        super().__init__(config)
        self.vectorizer = None
        self.label_encoder = {}
        self.reverse_label_encoder = {}
        self.feature_extractors = {}
    
    def extract_features(self, entity_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """提取实体特征"""
        features = {}
        
        # 基础文本特征
        features['length'] = len(entity_name)
        features['word_count'] = len(entity_name.split())
        features['has_uppercase'] = any(c.isupper() for c in entity_name)
        features['has_digits'] = any(c.isdigit() for c in entity_name)
        features['has_special_chars'] = bool(re.search(r'[^a-zA-Z0-9\s]', entity_name))
        
        # 词汇特征
        name_lower = entity_name.lower()
        features['starts_with_capital'] = entity_name[0].isupper() if entity_name else False
        features['is_all_caps'] = entity_name.isupper()
        features['contains_id'] = 'id' in name_lower or '_' in name_lower
        
        # 领域特定关键词
        temporal_keywords = ['time', 'date', '时间', '日期', '小时', '分钟', '秒', 'hour', 'minute', 'second']
        spatial_keywords = ['location', 'place', 'position', '位置', '地点', '空间', 'space', 'area']
        action_keywords = ['action', 'execute', 'perform', '执行', '动作', '操作', 'monitor', 'check']
        condition_keywords = ['condition', 'threshold', 'limit', '条件', '阈值', '限制', 'status', 'state']
        
        features['is_temporal'] = any(kw in name_lower for kw in temporal_keywords)
        features['is_spatial'] = any(kw in name_lower for kw in spatial_keywords)
        features['is_action'] = any(kw in name_lower for kw in action_keywords)
        features['is_condition'] = any(kw in name_lower for kw in condition_keywords)
        
        # 模式匹配
        features['is_camel_case'] = bool(re.search(r'[a-z][A-Z]', entity_name))
        features['is_snake_case'] = '_' in entity_name
        features['is_id_pattern'] = bool(re.search(r'ID_\d+|id_\d+|\d+', entity_name))
        features['is_event_pattern'] = entity_name.endswith('Event') or '事件' in entity_name
        
        # 上下文特征（如果提供）
        if context:
            features['schema_type'] = context.get('schema', 'unknown')
            features['confidence'] = context.get('confidence', 0.5)
        
        return features
    
    def prepare_data(self) -> Tuple[Any, Any, Any, Any]:
        """准备训练数据"""
        print("📊 加载实体推断训练数据...")
        
        # 加载训练数据
        with open(self.config.training_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取特征和标签
        features_list = []
        labels = []
        entity_names = []
        
        for sample in data:
            entity_name = sample['entity_name']
            entity_type = sample['entity_type']
            
            # 跳过Unknown类型（噪声数据）
            if entity_type == 'Unknown':
                continue
            
            # 提取特征
            context = {
                'schema': sample.get('schema', 'unknown'),
                'confidence': sample.get('confidence', 0.5)
            }
            features = self.extract_features(entity_name, context)
            
            features_list.append(features)
            labels.append(entity_type)
            entity_names.append(entity_name)
        
        print(f"   📝 实体样本: {len(features_list)}")
        print(f"   🏷️ 标签分布: {dict(zip(*np.unique(labels, return_counts=True)))}")
        
        # 创建标签编码器
        unique_labels = list(set(labels))
        self.label_encoder = {label: idx for idx, label in enumerate(unique_labels)}
        self.reverse_label_encoder = {idx: label for label, idx in self.label_encoder.items()}
        
        # 编码标签
        encoded_labels = [self.label_encoder[label] for label in labels]
        
        # 转换特征为数值矩阵
        feature_names = list(features_list[0].keys())
        X = []
        
        for features in features_list:
            feature_vector = []
            for name in feature_names:
                value = features[name]
                if isinstance(value, bool):
                    feature_vector.append(1.0 if value else 0.0)
                elif isinstance(value, (int, float)):
                    feature_vector.append(float(value))
                elif isinstance(value, str):
                    # 简单的字符串编码
                    feature_vector.append(hash(value) % 1000 / 1000.0)
                else:
                    feature_vector.append(0.0)
            X.append(feature_vector)
        
        X = np.array(X)
        y = np.array(encoded_labels)
        
        # 保存特征名称
        self.feature_names = feature_names
        
        # 分割训练集和验证集
        test_size = self.config.hyperparameters.get('test_size', 0.2)
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        print(f"   🎯 训练集: {X_train.shape[0]} 样本, {X_train.shape[1]} 特征")
        print(f"   📊 验证集: {X_val.shape[0]} 样本")
        
        return X_train, y_train, X_val, y_val
    
    def build_model(self) -> GradientBoostingClassifier:
        """构建梯度提升分类器"""
        print("🚀 构建梯度提升分类器...")
        
        model = GradientBoostingClassifier(
            n_estimators=self.config.hyperparameters.get('n_estimators', 100),
            learning_rate=self.config.hyperparameters.get('learning_rate', 0.1),
            max_depth=self.config.hyperparameters.get('max_depth', 6),
            min_samples_split=self.config.hyperparameters.get('min_samples_split', 10),
            min_samples_leaf=self.config.hyperparameters.get('min_samples_leaf', 4),
            random_state=42
        )
        
        return model
    
    def train_model(self, X_train: Any, y_train: Any, X_val: Any, y_val: Any) -> TrainingResult:
        """训练模型"""
        print("🎯 开始训练...")
        
        # 训练模型
        self.model.fit(X_train, y_train)
        
        # 预测
        y_train_pred = self.model.predict(X_train)
        y_val_pred = self.model.predict(X_val)
        
        # 计算准确率
        train_accuracy = accuracy_score(y_train, y_train_pred)
        val_accuracy = accuracy_score(y_val, y_val_pred)
        
        print(f"   📈 训练准确率: {train_accuracy:.4f}")
        print(f"   📊 验证准确率: {val_accuracy:.4f}")
        
        # 详细分类报告
        print("\n📋 分类报告:")
        target_names = [self.reverse_label_encoder[i] for i in range(len(self.reverse_label_encoder))]
        print(classification_report(y_val, y_val_pred, target_names=target_names))
        
        # 特征重要性
        importances = self.model.feature_importances_
        top_features = sorted(zip(self.feature_names, importances), key=lambda x: x[1], reverse=True)
        
        print("\n🔍 重要特征 (Top 15):")
        for feature, importance in top_features[:15]:
            print(f"   {feature}: {importance:.4f}")
        
        # 构建训练结果
        result = TrainingResult(
            model_path="",  # 将在保存时设置
            training_time=0.0,  # 将在外部设置
            final_accuracy=train_accuracy,
            validation_accuracy=val_accuracy,
            training_history=[{
                'epoch': 1,
                'train_accuracy': train_accuracy,
                'val_accuracy': val_accuracy
            }],
            model_metadata={
                'model_type': 'GradientBoostingClassifier',
                'feature_count': X_train.shape[1],
                'feature_names': self.feature_names,
                'label_encoder': self.label_encoder,
                'reverse_label_encoder': self.reverse_label_encoder,
                'top_features': top_features[:10]
            }
        )
        
        return result
    
    def evaluate_model(self, X_test: Any, y_test: Any) -> Dict[str, float]:
        """评估模型"""
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        return {
            'accuracy': accuracy,
            'sample_count': len(y_test)
        }
    
    def predict_entity_type(self, entity_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """预测实体类型"""
        if self.model is None:
            raise ValueError("模型未训练或未加载")
        
        # 提取特征
        features = self.extract_features(entity_name, context)
        
        # 转换为特征向量
        feature_vector = []
        for name in self.feature_names:
            value = features.get(name, 0)
            if isinstance(value, bool):
                feature_vector.append(1.0 if value else 0.0)
            elif isinstance(value, (int, float)):
                feature_vector.append(float(value))
            elif isinstance(value, str):
                feature_vector.append(hash(value) % 1000 / 1000.0)
            else:
                feature_vector.append(0.0)
        
        X = np.array([feature_vector])
        
        # 预测
        pred_proba = self.model.predict_proba(X)[0]
        pred_label_idx = np.argmax(pred_proba)
        pred_label = self.reverse_label_encoder[pred_label_idx]
        confidence = pred_proba[pred_label_idx]
        
        # 所有类别的概率
        all_probabilities = {
            self.reverse_label_encoder[i]: prob 
            for i, prob in enumerate(pred_proba)
        }
        
        return {
            'predicted_type': pred_label,
            'confidence': confidence,
            'all_probabilities': all_probabilities,
            'features_used': features
        }

def create_entity_inferer_config(
    training_data_path: str,
    output_model_path: str = "training/models/entity_inferer/latest.pkl",
    hyperparameters: Dict[str, Any] = None
) -> TrainingConfig:
    """创建实体推断器训练配置"""
    
    if hyperparameters is None:
        hyperparameters = {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 6,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'test_size': 0.2
        }
    
    return TrainingConfig(
        model_name="实体类型推断器",
        model_type="entity_inferer",
        training_data_path=training_data_path,
        validation_data_path=None,
        output_model_path=output_model_path,
        hyperparameters=hyperparameters,
        training_metadata={
            'description': '基于特征工程和梯度提升的实体类型推断器',
            'input_format': 'entity_name + context',
            'output_format': 'entity_type',
            'feature_types': ['textual', 'lexical', 'pattern', 'domain_specific']
        }
    )

def train_entity_inferer(
    training_data_path: str = None,
    output_model_path: str = "training/models/entity_inferer/latest.pkl",
    hyperparameters: Dict[str, Any] = None
) -> TrainingResult:
    """训练实体推断器的便捷函数"""
    
    # 如果没有提供训练数据路径，自动收集
    if training_data_path is None:
        from .base_trainer import training_data_manager
        training_data_path = training_data_manager.collect_entity_training_data()
    
    # 创建配置
    config = create_entity_inferer_config(
        training_data_path=training_data_path,
        output_model_path=output_model_path,
        hyperparameters=hyperparameters
    )
    
    # 创建训练器并训练
    trainer = EntityInfererTrainer(config)
    result = trainer.run_full_training()
    
    return result

if __name__ == "__main__":
    # 示例：训练实体推断器
    result = train_entity_inferer()
    print(f"🎉 实体推断器训练完成!")
    print(f"📁 模型路径: {result.model_path}")
    print(f"📈 验证准确率: {result.validation_accuracy:.4f}")
