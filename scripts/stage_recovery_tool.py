#!/usr/bin/env python3
"""
阶段恢复工具
用于从保存的阶段数据恢复和继续处理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from pipeline.stage_saver import StageSaver
from main import KnowledgeGraphBuilder

def list_sessions():
    """列出所有会话"""
    saver = StageSaver()
    sessions = saver.list_sessions()
    
    if not sessions:
        print("📭 没有找到保存的会话")
        return
    
    print("📋 可用会话:")
    for i, session in enumerate(sessions, 1):
        print(f"  {i}. {session}")
        
        # 显示会话中的阶段
        stages = saver.list_stages(session)
        if stages:
            print(f"     阶段: {len(stages)} 个")
            for stage in stages[-3:]:  # 显示最后3个阶段
                print(f"       - {stage['stage_name']} ({stage['data_count']} 项)")
        print()

def show_session_details(session_id: str):
    """显示会话详情"""
    saver = StageSaver()
    saver.print_session_summary(session_id)

def resume_from_stage(session_id: str, stage_name: str):
    """从指定阶段恢复处理"""
    saver = StageSaver()
    stage_data = saver.load_stage(stage_name, session_id)
    
    if not stage_data:
        print(f"❌ 无法加载阶段: {stage_name}")
        return
    
    print(f"🔄 从阶段 '{stage_name}' 恢复处理...")
    print(f"   数据量: {len(stage_data.data)} 项")
    print(f"   时间戳: {stage_data.timestamp}")
    
    # 创建知识图谱构建器
    builder = KnowledgeGraphBuilder()
    
    # 根据阶段类型继续处理
    if stage_name == "raw_extraction":
        print("🚀 从原始抽取结果继续...")
        # 跳过LLM抽取，直接进行验证
        # 这里需要实现验证逻辑
        
    elif stage_name == "validated_triples":
        print("🚀 从验证后的三元组继续...")
        result = builder._process_triples_pipeline(stage_data.data)
        
    elif stage_name == "cleaned_triples":
        print("🚀 从清理后的三元组继续...")
        # 跳过清理，直接进行映射
        result = builder._process_triples_pipeline(stage_data.data)
        
    elif stage_name == "mapped_triples":
        print("🚀 从映射后的三元组继续...")
        # 直接更新知识图谱
        update_result = builder.kg_updater.update_kg_from_triples(stage_data.data)
        print(f"✅ 知识图谱更新完成: {update_result.new_entities} 实体, {update_result.new_relations} 关系")
        
    else:
        print(f"⚠️ 不支持从阶段 '{stage_name}' 恢复")

def create_manual_review(session_id: str, stage_name: str):
    """创建手工审核文件"""
    saver = StageSaver()
    stage_data = saver.load_stage(stage_name, session_id)
    
    if not stage_data:
        print(f"❌ 无法加载阶段: {stage_name}")
        return
    
    review_file = saver.create_manual_review_file(stage_name, stage_data.data)
    print(f"📋 手工审核文件已创建: {review_file}")
    print(f"📝 请编辑文件，设置 approved 字段为 true/false")

def process_reviewed_data(review_file_path: str):
    """处理审核后的数据"""
    saver = StageSaver()
    approved_data = saver.load_reviewed_data(review_file_path)
    
    if not approved_data:
        print("❌ 没有通过审核的数据")
        return
    
    print(f"✅ 加载了 {len(approved_data)} 项通过审核的数据")
    
    # 继续处理审核通过的数据
    builder = KnowledgeGraphBuilder()
    result = builder._process_triples_pipeline(approved_data)
    
    print("🎉 审核数据处理完成!")

def main():
    parser = argparse.ArgumentParser(description="阶段恢复工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 列出会话
    subparsers.add_parser('list', help='列出所有会话')
    
    # 显示会话详情
    detail_parser = subparsers.add_parser('show', help='显示会话详情')
    detail_parser.add_argument('session_id', help='会话ID')
    
    # 从阶段恢复
    resume_parser = subparsers.add_parser('resume', help='从指定阶段恢复')
    resume_parser.add_argument('session_id', help='会话ID')
    resume_parser.add_argument('stage_name', help='阶段名称')
    
    # 创建审核文件
    review_parser = subparsers.add_parser('review', help='创建手工审核文件')
    review_parser.add_argument('session_id', help='会话ID')
    review_parser.add_argument('stage_name', help='阶段名称')
    
    # 处理审核数据
    process_parser = subparsers.add_parser('process', help='处理审核后的数据')
    process_parser.add_argument('review_file', help='审核文件路径')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_sessions()
    elif args.command == 'show':
        show_session_details(args.session_id)
    elif args.command == 'resume':
        resume_from_stage(args.session_id, args.stage_name)
    elif args.command == 'review':
        create_manual_review(args.session_id, args.stage_name)
    elif args.command == 'process':
        process_reviewed_data(args.review_file)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
