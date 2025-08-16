"""
Schema分类模型训练器
用于训练更准确的Schema检测模型
"""

import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from typing import Dict, List, Any, Optional, Tuple

from .base_trainer import BaseTrainer, TrainingConfig, TrainingResult

class SchemaClassifierTrainer(BaseTrainer):
    """Schema分类器训练器"""
    
    def __init__(self, config: TrainingConfig):
        super().__init__(config)
        self.vectorizer = None
        self.label_encoder = {}
        self.reverse_label_encoder = {}
    
    def prepare_data(self) -> Tuple[Any, Any, Any, Any]:
        """准备训练数据"""
        print("📊 加载Schema分类训练数据...")
        
        # 加载训练数据
        with open(self.config.training_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取文本和标签
        texts = []
        labels = []
        
        for sample in data:
            texts.append(sample['text'])
            schema_path = sample['schema']
            
            # 简化Schema标签
            if 'spatiotemporal' in schema_path.lower():
                label = 'spatiotemporal'
            elif 'schema_config' in schema_path.lower() or 'general' in schema_path.lower():
                label = 'general'
            else:
                label = 'mixed'
            
            labels.append(label)
        
        # 创建标签编码器
        unique_labels = list(set(labels))
        self.label_encoder = {label: idx for idx, label in enumerate(unique_labels)}
        self.reverse_label_encoder = {idx: label for label, idx in self.label_encoder.items()}
        
        # 编码标签
        encoded_labels = [self.label_encoder[label] for label in labels]
        
        print(f"   📝 文本样本: {len(texts)}")
        print(f"   🏷️ 标签分布: {dict(zip(*np.unique(labels, return_counts=True)))}")
        
        # 文本向量化
        print("🔤 文本向量化...")
        self.vectorizer = TfidfVectorizer(
            max_features=self.config.hyperparameters.get('max_features', 5000),
            ngram_range=self.config.hyperparameters.get('ngram_range', (1, 2)),
            stop_words='english'
        )
        
        X = self.vectorizer.fit_transform(texts)
        y = np.array(encoded_labels)
        
        # 分割训练集和验证集
        test_size = self.config.hyperparameters.get('test_size', 0.2)
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        print(f"   🎯 训练集: {X_train.shape[0]} 样本")
        print(f"   📊 验证集: {X_val.shape[0]} 样本")
        
        return X_train, y_train, X_val, y_val
    
    def build_model(self) -> RandomForestClassifier:
        """构建随机森林分类器"""
        print("🌲 构建随机森林分类器...")
        
        model = RandomForestClassifier(
            n_estimators=self.config.hyperparameters.get('n_estimators', 100),
            max_depth=self.config.hyperparameters.get('max_depth', 10),
            min_samples_split=self.config.hyperparameters.get('min_samples_split', 5),
            min_samples_leaf=self.config.hyperparameters.get('min_samples_leaf', 2),
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
        feature_names = self.vectorizer.get_feature_names_out()
        importances = self.model.feature_importances_
        top_features = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:20]
        
        print("\n🔍 重要特征 (Top 20):")
        for feature, importance in top_features:
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
                'model_type': 'RandomForestClassifier',
                'feature_count': X_train.shape[1],
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
    
    def predict_schema(self, text: str) -> Dict[str, Any]:
        """预测文本的Schema类型"""
        if self.model is None or self.vectorizer is None:
            raise ValueError("模型未训练或未加载")
        
        # 向量化文本
        X = self.vectorizer.transform([text])
        
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
            'predicted_schema': pred_label,
            'confidence': confidence,
            'all_probabilities': all_probabilities
        }

def create_schema_classifier_config(
    training_data_path: str,
    output_model_path: str = "training/models/schema_classifier/latest.pkl",
    hyperparameters: Dict[str, Any] = None
) -> TrainingConfig:
    """创建Schema分类器训练配置"""
    
    if hyperparameters is None:
        hyperparameters = {
            'max_features': 5000,
            'ngram_range': (1, 2),
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'test_size': 0.2
        }
    
    return TrainingConfig(
        model_name="Schema分类器",
        model_type="schema_classifier",
        training_data_path=training_data_path,
        validation_data_path=None,
        output_model_path=output_model_path,
        hyperparameters=hyperparameters,
        training_metadata={
            'description': '基于TF-IDF和随机森林的Schema分类器',
            'input_format': 'text',
            'output_format': 'schema_type',
            'supported_schemas': ['general', 'spatiotemporal', 'mixed']
        }
    )

def train_schema_classifier(
    training_data_path: str = None,
    output_model_path: str = "training/models/schema_classifier/latest.pkl",
    hyperparameters: Dict[str, Any] = None
) -> TrainingResult:
    """训练Schema分类器的便捷函数"""
    
    # 如果没有提供训练数据路径，自动收集
    if training_data_path is None:
        from .base_trainer import training_data_manager
        training_data_path = training_data_manager.collect_schema_training_data()
    
    # 创建配置
    config = create_schema_classifier_config(
        training_data_path=training_data_path,
        output_model_path=output_model_path,
        hyperparameters=hyperparameters
    )
    
    # 创建训练器并训练
    trainer = SchemaClassifierTrainer(config)
    result = trainer.run_full_training()
    
    return result

if __name__ == "__main__":
    # 示例：训练Schema分类器
    result = train_schema_classifier()
    print(f"🎉 Schema分类器训练完成!")
    print(f"📁 模型路径: {result.model_path}")
    print(f"📈 验证准确率: {result.validation_accuracy:.4f}")
