#!/usr/bin/env python3
"""
实体类型缓存管理工具
用于管理和审核实体类型推断缓存
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import argparse
from datetime import datetime
from pipeline.enhanced_entity_inferer import EnhancedEntityTypeInferer
from pipeline.stage_saver import StageSaver

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.inferer = EnhancedEntityTypeInferer()
        self.stage_saver = StageSaver()
    
    def show_cache_stats(self):
        """显示缓存统计信息"""
        stats = self.inferer.get_cache_stats()
        
        print("📊 实体类型缓存统计")
        print("=" * 50)
        print(f"总缓存实体数: {stats['total_cached_entities']}")
        print(f"高频实体数: {stats['high_frequency_entities']}")
        print(f"缓存命中潜力: {stats['cache_hit_potential']:.2%}")
        print()
        
        # 显示缓存详情
        if stats['total_cached_entities'] > 0:
            print("📋 缓存详情:")
            for entity, info in list(self.inferer.entity_cache.verified_entities.items())[:10]:
                print(f"  {entity:<20} | {info['type']:<12} | 使用{info['count']}次 | {info['source']}")
            
            if stats['total_cached_entities'] > 10:
                print(f"  ... 还有 {stats['total_cached_entities'] - 10} 个实体")
    
    def export_for_review(self, output_file: str = None):
        """导出高频实体供人工审核"""
        high_freq_entities = self.inferer.entity_cache.export_for_review()
        
        if not high_freq_entities:
            print("📭 没有高频实体需要审核")
            return
        
        # 创建审核文件
        review_file = self.stage_saver.create_manual_review_file(
            "高频实体类型审核",
            high_freq_entities
        )
        
        print(f"📋 高频实体审核文件已创建: {review_file}")
        print(f"📝 包含 {len(high_freq_entities)} 个高频实体")
        print("📝 请编辑文件，设置 approved 字段为 true/false")
        
        return review_file
    
    def import_reviewed_entities(self, review_file: str):
        """导入审核后的实体类型"""
        try:
            with open(review_file, 'r', encoding='utf-8') as f:
                review_data = json.load(f)
            
            approved_count = 0
            rejected_count = 0
            
            for item in review_data.get("items", []):
                if item.get("approved") is True:
                    entity_data = item["data"]
                    self.inferer.entity_cache.add_verified_entity(
                        entity_data["entity"],
                        entity_data["type"],
                        1.0,  # 人工审核的置信度设为1.0
                        "human_approved"
                    )
                    approved_count += 1
                elif item.get("approved") is False:
                    rejected_count += 1
            
            print(f"✅ 导入完成: {approved_count} 个实体通过审核, {rejected_count} 个被拒绝")
            
        except Exception as e:
            print(f"❌ 导入失败: {e}")
    
    def clean_cache(self, min_confidence: float = 0.5, min_usage: int = 1):
        """清理低质量缓存项"""
        original_count = len(self.inferer.entity_cache.verified_entities)
        
        # 过滤低质量项
        filtered_entities = {}
        for entity, info in self.inferer.entity_cache.verified_entities.items():
            if info['confidence'] >= min_confidence and info['count'] >= min_usage:
                filtered_entities[entity] = info
        
        self.inferer.entity_cache.verified_entities = filtered_entities
        cleaned_count = original_count - len(filtered_entities)
        
        print(f"🧹 缓存清理完成: 移除了 {cleaned_count} 个低质量项")
        print(f"📊 剩余缓存项: {len(filtered_entities)}")
    
    def backup_cache(self, backup_file: str = None):
        """备份缓存"""
        if not backup_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"cache_backup_{timestamp}.json"
        
        backup_data = {
            "backup_time": datetime.now().isoformat(),
            "total_entities": len(self.inferer.entity_cache.verified_entities),
            "entities": self.inferer.entity_cache.verified_entities
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 缓存已备份到: {backup_file}")
        return backup_file
    
    def restore_cache(self, backup_file: str):
        """恢复缓存"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            self.inferer.entity_cache.verified_entities = backup_data["entities"]
            
            print(f"🔄 缓存已恢复: {backup_data['total_entities']} 个实体")
            print(f"📅 备份时间: {backup_data['backup_time']}")
            
        except Exception as e:
            print(f"❌ 恢复失败: {e}")
    
    def analyze_cache_performance(self):
        """分析缓存性能"""
        entities = self.inferer.entity_cache.verified_entities
        
        if not entities:
            print("📭 缓存为空，无法分析")
            return
        
        # 按来源分组统计
        source_stats = {}
        confidence_stats = []
        usage_stats = []
        
        for info in entities.values():
            source = info['source']
            source_stats[source] = source_stats.get(source, 0) + 1
            confidence_stats.append(info['confidence'])
            usage_stats.append(info['count'])
        
        print("📈 缓存性能分析")
        print("=" * 50)
        
        print("📊 按来源统计:")
        for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(entities) * 100
            print(f"  {source:<25} | {count:>4} 个 ({percentage:>5.1f}%)")
        
        print(f"\n📊 置信度统计:")
        avg_confidence = sum(confidence_stats) / len(confidence_stats)
        print(f"  平均置信度: {avg_confidence:.3f}")
        print(f"  最高置信度: {max(confidence_stats):.3f}")
        print(f"  最低置信度: {min(confidence_stats):.3f}")
        
        print(f"\n📊 使用频率统计:")
        avg_usage = sum(usage_stats) / len(usage_stats)
        print(f"  平均使用次数: {avg_usage:.1f}")
        print(f"  最高使用次数: {max(usage_stats)}")
        print(f"  单次使用实体: {sum(1 for u in usage_stats if u == 1)}")

def main():
    parser = argparse.ArgumentParser(description="实体类型缓存管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 显示统计信息
    subparsers.add_parser('stats', help='显示缓存统计信息')
    
    # 导出审核文件
    export_parser = subparsers.add_parser('export', help='导出高频实体供审核')
    export_parser.add_argument('--output', help='输出文件路径')
    
    # 导入审核结果
    import_parser = subparsers.add_parser('import', help='导入审核后的实体类型')
    import_parser.add_argument('review_file', help='审核文件路径')
    
    # 清理缓存
    clean_parser = subparsers.add_parser('clean', help='清理低质量缓存项')
    clean_parser.add_argument('--min-confidence', type=float, default=0.5, help='最低置信度')
    clean_parser.add_argument('--min-usage', type=int, default=1, help='最低使用次数')
    
    # 备份缓存
    backup_parser = subparsers.add_parser('backup', help='备份缓存')
    backup_parser.add_argument('--output', help='备份文件路径')
    
    # 恢复缓存
    restore_parser = subparsers.add_parser('restore', help='恢复缓存')
    restore_parser.add_argument('backup_file', help='备份文件路径')
    
    # 性能分析
    subparsers.add_parser('analyze', help='分析缓存性能')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = CacheManager()
    
    if args.command == 'stats':
        manager.show_cache_stats()
    elif args.command == 'export':
        manager.export_for_review(args.output)
    elif args.command == 'import':
        manager.import_reviewed_entities(args.review_file)
    elif args.command == 'clean':
        manager.clean_cache(args.min_confidence, args.min_usage)
    elif args.command == 'backup':
        manager.backup_cache(args.output)
    elif args.command == 'restore':
        manager.restore_cache(args.backup_file)
    elif args.command == 'analyze':
        manager.analyze_cache_performance()

if __name__ == "__main__":
    main()
