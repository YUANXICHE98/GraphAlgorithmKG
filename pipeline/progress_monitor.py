"""
进度监控器
实时监控知识图谱构建的各个阶段
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class StageResult:
    """阶段结果"""
    stage_name: str
    start_time: float
    end_time: float
    duration: float
    status: str  # "running", "completed", "failed"
    input_count: int
    output_count: int
    success_rate: float
    details: Dict[str, Any]
    errors: List[str]

class ProgressMonitor:
    """进度监控器"""
    
    def __init__(self):
        self.stages: List[StageResult] = []
        self.current_stage: Optional[StageResult] = None
        self.session_start_time = time.time()
        self.total_documents = 0
        self.total_chunks = 0
        self.total_triples = 0
        
    def start_stage(self, stage_name: str, input_count: int = 0, details: Dict[str, Any] = None) -> None:
        """开始一个新阶段"""
        if self.current_stage and self.current_stage.status == "running":
            self.end_stage("interrupted")
        
        print(f"\n{'='*60}")
        print(f"🚀 开始阶段: {stage_name}")
        print(f"📊 输入数量: {input_count}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        self.current_stage = StageResult(
            stage_name=stage_name,
            start_time=time.time(),
            end_time=0,
            duration=0,
            status="running",
            input_count=input_count,
            output_count=0,
            success_rate=0.0,
            details=details or {},
            errors=[]
        )
    
    def update_stage(self, output_count: int = None, details: Dict[str, Any] = None, 
                    error: str = None) -> None:
        """更新当前阶段"""
        if not self.current_stage:
            return
        
        if output_count is not None:
            self.current_stage.output_count = output_count
            
        if details:
            self.current_stage.details.update(details)
            
        if error:
            self.current_stage.errors.append(error)
            print(f"❌ 阶段错误: {error}")
        
        # 实时输出进度
        if output_count is not None:
            success_rate = (output_count / self.current_stage.input_count * 100) if self.current_stage.input_count > 0 else 0
            elapsed = time.time() - self.current_stage.start_time
            print(f"📈 进度更新: {output_count}/{self.current_stage.input_count} ({success_rate:.1f}%) - 耗时: {elapsed:.1f}s")
    
    def end_stage(self, status: str = "completed", final_output_count: int = None) -> StageResult:
        """结束当前阶段"""
        if not self.current_stage:
            return None
        
        self.current_stage.end_time = time.time()
        self.current_stage.duration = self.current_stage.end_time - self.current_stage.start_time
        self.current_stage.status = status
        
        if final_output_count is not None:
            self.current_stage.output_count = final_output_count
        
        if self.current_stage.input_count > 0:
            self.current_stage.success_rate = self.current_stage.output_count / self.current_stage.input_count
        
        # 输出阶段总结
        print(f"\n{'='*60}")
        status_emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⚠️"
        print(f"{status_emoji} 阶段完成: {self.current_stage.stage_name}")
        print(f"📊 处理结果: {self.current_stage.output_count}/{self.current_stage.input_count} ({self.current_stage.success_rate*100:.1f}%)")
        print(f"⏱️  耗时: {self.current_stage.duration:.2f}秒")
        
        if self.current_stage.errors:
            print(f"❌ 错误数量: {len(self.current_stage.errors)}")
            for error in self.current_stage.errors[-3:]:  # 只显示最后3个错误
                print(f"   - {error}")
        
        if self.current_stage.details:
            print("📋 详细信息:")
            for key, value in self.current_stage.details.items():
                print(f"   {key}: {value}")
        
        print(f"{'='*60}\n")
        
        # 保存到历史记录
        self.stages.append(self.current_stage)
        completed_stage = self.current_stage
        self.current_stage = None
        
        return completed_stage
    
    def log_item_processing(self, item_name: str, status: str, details: str = "") -> None:
        """记录单个项目的处理"""
        status_emoji = "✅" if status == "success" else "❌" if status == "failed" else "⚠️"
        print(f"   {status_emoji} {item_name}: {details}")
    
    def print_session_summary(self) -> None:
        """打印会话总结"""
        total_duration = time.time() - self.session_start_time
        
        print(f"\n{'='*80}")
        print(f"🎯 会话总结")
        print(f"{'='*80}")
        print(f"⏱️  总耗时: {total_duration:.2f}秒")
        print(f"📊 总阶段数: {len(self.stages)}")
        
        # 统计各阶段
        completed_stages = [s for s in self.stages if s.status == "completed"]
        failed_stages = [s for s in self.stages if s.status == "failed"]
        
        print(f"✅ 成功阶段: {len(completed_stages)}")
        print(f"❌ 失败阶段: {len(failed_stages)}")
        
        # 详细阶段信息
        print(f"\n📋 阶段详情:")
        for i, stage in enumerate(self.stages, 1):
            status_emoji = "✅" if stage.status == "completed" else "❌" if stage.status == "failed" else "⚠️"
            success_rate = stage.success_rate * 100 if stage.success_rate else 0
            print(f"   {i}. {status_emoji} {stage.stage_name}")
            print(f"      处理: {stage.output_count}/{stage.input_count} ({success_rate:.1f}%)")
            print(f"      耗时: {stage.duration:.2f}s")
            if stage.errors:
                print(f"      错误: {len(stage.errors)}个")
        
        # 性能统计
        if completed_stages:
            avg_duration = sum(s.duration for s in completed_stages) / len(completed_stages)
            total_processed = sum(s.output_count for s in completed_stages)
            print(f"\n📈 性能统计:")
            print(f"   平均阶段耗时: {avg_duration:.2f}秒")
            print(f"   总处理项目: {total_processed}")
            if total_duration > 0:
                print(f"   处理速度: {total_processed/total_duration:.1f} 项目/秒")
        
        print(f"{'='*80}\n")
    
    def save_report(self, filepath: str = None) -> str:
        """保存详细报告"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"logs/progress_report_{timestamp}.json"
        
        report = {
            "session_info": {
                "start_time": self.session_start_time,
                "end_time": time.time(),
                "total_duration": time.time() - self.session_start_time,
                "total_stages": len(self.stages)
            },
            "stages": [asdict(stage) for stage in self.stages],
            "summary": {
                "completed_stages": len([s for s in self.stages if s.status == "completed"]),
                "failed_stages": len([s for s in self.stages if s.status == "failed"]),
                "total_errors": sum(len(s.errors) for s in self.stages)
            }
        }
        
        # 确保目录存在
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 进度报告已保存: {filepath}")
        return filepath

# 全局监控器实例
monitor = ProgressMonitor()
