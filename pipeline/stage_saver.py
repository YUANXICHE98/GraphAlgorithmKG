"""
阶段性保存管理器
支持知识图谱构建过程中的中间结果保存和恢复
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict

@dataclass
class StageData:
    """阶段数据"""
    stage_name: str
    timestamp: str
    session_id: str
    data: Any
    metadata: Dict[str, Any]
    file_path: str

class StageSaver:
    """阶段性保存管理器"""
    
    def __init__(self, base_path: str = "stages", session_id: str = None):
        self.base_path = Path(base_path)
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_path = self.base_path / self.session_id
        
        # 创建目录
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        # 阶段定义
        self.stages = {
            "raw_extraction": "LLM原始抽取结果",
            "validated_triples": "验证后的三元组",
            "cleaned_triples": "清理后的三元组", 
            "mapped_triples": "映射后的三元组",
            "final_kg": "最终知识图谱"
        }
        
        print(f"📁 阶段保存器初始化: {self.session_path}")
    
    def save_stage(self, stage_name: str, data: Any, metadata: Dict[str, Any] = None) -> str:
        """保存阶段数据"""
        timestamp = datetime.now().isoformat()
        
        # 构建文件路径
        safe_stage_name = stage_name.replace(" ", "_").lower()
        file_path = self.session_path / f"{safe_stage_name}.json"
        
        # 准备保存数据
        stage_data = {
            "stage_name": stage_name,
            "timestamp": timestamp,
            "session_id": self.session_id,
            "data": data,
            "metadata": metadata or {},
            "data_count": len(data) if isinstance(data, (list, dict)) else 1
        }
        
        # 保存到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stage_data, f, indent=2, ensure_ascii=False, default=str)
        
        # 记录日志
        stage_desc = self.stages.get(safe_stage_name, stage_name)
        data_count = stage_data["data_count"]
        print(f"💾 保存阶段: {stage_desc} ({data_count} 项) -> {file_path.name}")
        
        return str(file_path)
    
    def load_stage(self, stage_name: str, session_id: str = None) -> Optional[StageData]:
        """加载阶段数据"""
        target_session = session_id or self.session_id
        target_path = self.base_path / target_session
        
        safe_stage_name = stage_name.replace(" ", "_").lower()
        file_path = target_path / f"{safe_stage_name}.json"
        
        if not file_path.exists():
            print(f"⚠️ 阶段文件不存在: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                stage_data = json.load(f)
            
            print(f"📂 加载阶段: {stage_data['stage_name']} ({stage_data.get('data_count', 0)} 项)")
            
            return StageData(
                stage_name=stage_data["stage_name"],
                timestamp=stage_data["timestamp"],
                session_id=stage_data["session_id"],
                data=stage_data["data"],
                metadata=stage_data["metadata"],
                file_path=str(file_path)
            )
            
        except Exception as e:
            print(f"❌ 加载阶段失败: {e}")
            return None
    
    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        if not self.base_path.exists():
            return []
        
        sessions = []
        for item in self.base_path.iterdir():
            if item.is_dir():
                sessions.append(item.name)
        
        return sorted(sessions, reverse=True)  # 最新的在前
    
    def list_stages(self, session_id: str = None) -> List[Dict[str, Any]]:
        """列出会话中的所有阶段"""
        target_session = session_id or self.session_id
        target_path = self.base_path / target_session
        
        if not target_path.exists():
            return []
        
        stages = []
        for file_path in target_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    stage_data = json.load(f)
                
                stages.append({
                    "stage_name": stage_data["stage_name"],
                    "timestamp": stage_data["timestamp"],
                    "data_count": stage_data.get("data_count", 0),
                    "file_name": file_path.name,
                    "file_size": file_path.stat().st_size
                })
            except Exception as e:
                print(f"⚠️ 读取阶段文件失败 {file_path}: {e}")
        
        return sorted(stages, key=lambda x: x["timestamp"])
    
    def create_manual_review_file(self, stage_name: str, data: List[Dict], 
                                 output_path: str = None) -> str:
        """创建手工审核文件"""
        if not output_path:
            safe_name = stage_name.replace(" ", "_").lower()
            output_path = self.session_path / f"{safe_name}_review.json"
        
        review_data = {
            "review_info": {
                "stage_name": stage_name,
                "created_at": datetime.now().isoformat(),
                "total_items": len(data),
                "instructions": "请审核以下数据项，将approved字段设为true/false"
            },
            "items": []
        }
        
        # 为每个数据项添加审核字段
        for i, item in enumerate(data, 1):
            review_item = {
                "id": i,
                "approved": None,  # 待审核
                "comments": "",    # 审核意见
                "data": item
            }
            review_data["items"].append(review_item)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📋 创建审核文件: {output_path} ({len(data)} 项待审核)")
        return str(output_path)
    
    def load_reviewed_data(self, review_file_path: str) -> List[Dict]:
        """加载审核后的数据"""
        try:
            with open(review_file_path, 'r', encoding='utf-8') as f:
                review_data = json.load(f)
            
            approved_items = []
            total_items = len(review_data["items"])
            approved_count = 0
            
            for item in review_data["items"]:
                if item.get("approved") is True:
                    approved_items.append(item["data"])
                    approved_count += 1
            
            print(f"✅ 审核结果: {approved_count}/{total_items} 项通过审核")
            return approved_items
            
        except Exception as e:
            print(f"❌ 加载审核文件失败: {e}")
            return []
    
    def print_session_summary(self, session_id: str = None):
        """打印会话摘要"""
        target_session = session_id or self.session_id
        stages = self.list_stages(target_session)
        
        if not stages:
            print(f"📭 会话 {target_session} 中没有保存的阶段")
            return
        
        print(f"\n📊 会话摘要: {target_session}")
        print("=" * 60)
        
        for stage in stages:
            timestamp = datetime.fromisoformat(stage["timestamp"]).strftime("%H:%M:%S")
            size_kb = stage["file_size"] / 1024
            print(f"  {timestamp} | {stage['stage_name']:<20} | {stage['data_count']:>4} 项 | {size_kb:>6.1f}KB")
        
        print("=" * 60)
    
    def cleanup_old_sessions(self, keep_days: int = 7):
        """清理旧会话"""
        if not self.base_path.exists():
            return
        
        cutoff_time = time.time() - (keep_days * 24 * 60 * 60)
        cleaned_count = 0
        
        for session_dir in self.base_path.iterdir():
            if session_dir.is_dir() and session_dir.stat().st_mtime < cutoff_time:
                import shutil
                shutil.rmtree(session_dir)
                cleaned_count += 1
                print(f"🗑️ 清理旧会话: {session_dir.name}")
        
        if cleaned_count > 0:
            print(f"✅ 清理完成: 删除了 {cleaned_count} 个旧会话")
        else:
            print("✅ 无需清理: 没有超过保留期的会话")

# 全局实例
stage_saver = StageSaver()
