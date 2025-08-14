#!/usr/bin/env python3
"""
领域管理工具
用于管理多领域知识图谱模板和配置
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import json
from pathlib import Path
from domain.domain_template import (
    template_manager, 
    create_graph_algorithms_template, 
    create_dodaf_template
)
from domain.domain_detector import domain_detector
from indexing.multi_level_index import multi_level_index

class DomainManager:
    """领域管理器"""
    
    def __init__(self):
        self.template_manager = template_manager
        self.domain_detector = domain_detector
        self.multi_index = multi_level_index
    
    def list_domains(self):
        """列出所有可用领域"""
        domains = self.template_manager.list_templates()
        
        if not domains:
            print("📭 没有找到领域模板")
            return
        
        print("📋 可用领域模板:")
        print("=" * 60)
        
        for domain_name in domains:
            template = self.template_manager.get_template(domain_name)
            if template:
                print(f"🏷️  {template.display_name} ({domain_name})")
                print(f"   📝 {template.description}")
                print(f"   📊 实体类型: {len(template.entity_types)}")
                print(f"   🔗 关系类型: {len(template.relation_types)}")
                print(f"   🔤 关键词: {sum(len(kw) for kw in template.keywords.values())}")
                print(f"   🎯 模式: {sum(len(pt) for pt in template.patterns.values())}")
                print()
    
    def show_domain_details(self, domain_name: str):
        """显示领域详情"""
        template = self.template_manager.get_template(domain_name)
        
        if not template:
            print(f"❌ 领域模板不存在: {domain_name}")
            return
        
        print(f"🏷️  领域详情: {template.display_name}")
        print("=" * 60)
        print(f"📝 描述: {template.description}")
        print()
        
        # 实体类型
        print("📊 实体类型:")
        for entity_type, config in template.entity_types.items():
            print(f"  • {entity_type}: {config.get('description', 'N/A')}")
            examples = config.get('examples', [])
            if examples:
                print(f"    示例: {', '.join(examples[:3])}")
        print()
        
        # 关系类型
        print("🔗 关系类型:")
        for relation_type, config in template.relation_types.items():
            print(f"  • {relation_type}: {config.get('description', 'N/A')}")
            subject_types = config.get('subject_types', [])
            object_types = config.get('object_types', [])
            if subject_types and object_types:
                print(f"    约束: {subject_types} -> {object_types}")
        print()
        
        # 外部资源
        if template.external_resources:
            print("🌐 外部资源:")
            for resource_name, resource_url in template.external_resources.items():
                print(f"  • {resource_name}: {resource_url}")
    
    def detect_text_domain(self, text: str):
        """检测文本领域"""
        if not text.strip():
            print("❌ 请提供要检测的文本")
            return
        
        print(f"🔍 检测文本领域...")
        print(f"📄 文本: {text[:100]}{'...' if len(text) > 100 else ''}")
        print()
        
        results = self.domain_detector.detect_domain(text, top_k=3)
        
        if not results:
            print("❓ 未能检测到明确的领域")
            return
        
        print("🎯 检测结果:")
        for i, result in enumerate(results, 1):
            template = self.template_manager.get_template(result.domain_name)
            display_name = template.display_name if template else result.domain_name
            
            print(f"  {i}. {display_name} (置信度: {result.confidence:.2f})")
            print(f"     方法: {result.method}")
            if result.evidence:
                print(f"     证据: {', '.join(result.evidence)}")
            print()
    
    def create_domain_template(self, domain_name: str, display_name: str, 
                             description: str, base_domain: str = None):
        """创建新的领域模板"""
        if self.template_manager.get_template(domain_name):
            print(f"❌ 领域模板已存在: {domain_name}")
            return
        
        if base_domain:
            # 基于现有模板创建
            try:
                template = self.template_manager.create_template_from_existing(
                    base_domain, domain_name, display_name, description
                )
                print(f"✅ 基于 {base_domain} 创建新模板: {display_name}")
            except ValueError as e:
                print(f"❌ 创建失败: {e}")
                return
        else:
            # 创建空模板
            from domain.domain_template import DomainTemplate
            template = DomainTemplate(
                domain_name=domain_name,
                display_name=display_name,
                description=description
            )
            print(f"✅ 创建空模板: {display_name}")
        
        # 保存模板
        self.template_manager.save_template(template)
        
        # 更新检测器
        self.domain_detector.update_classifiers()
    
    def build_indexes(self, domain_names: list = None):
        """构建索引"""
        if not domain_names:
            domain_names = self.template_manager.list_templates()
        
        print(f"🔨 构建索引: {', '.join(domain_names)}")
        
        # 收集所有领域的词汇
        domain_vocabulary = {}
        for domain_name in domain_names:
            template = self.template_manager.get_template(domain_name)
            if template:
                domain_vocabulary[domain_name] = {
                    'keywords': template.keywords,
                    'patterns': template.patterns
                }
        
        # 构建多级索引
        self.multi_index.build_indexes(domain_vocabulary)
        
        # 保存索引
        self.multi_index.save_indexes()
        
        print("✅ 索引构建完成")
    
    def test_entity_inference(self, entity_name: str, domain_name: str = None):
        """测试实体类型推断"""
        from pipeline.enhanced_entity_inferer import EnhancedEntityTypeInferer
        
        if domain_name:
            inferer = EnhancedEntityTypeInferer(domain_name)
        else:
            # 自动检测领域
            detected_domain = self.domain_detector.detect_domain_simple(entity_name)
            if detected_domain:
                inferer = EnhancedEntityTypeInferer(detected_domain)
                print(f"🎯 自动检测领域: {detected_domain}")
            else:
                inferer = EnhancedEntityTypeInferer()
                print("⚠️ 使用默认领域")
        
        print(f"🔍 推断实体类型: {entity_name}")
        
        result = inferer.infer_entity_type(entity_name)
        
        print(f"📊 推断结果:")
        print(f"  实体类型: {result.entity_type or '未知'}")
        print(f"  置信度: {result.confidence:.2f}")
        print(f"  方法: {result.method}")
        print(f"  耗时: {result.inference_time*1000:.1f}ms")
    
    def export_domain_summary(self, output_file: str = None):
        """导出领域摘要"""
        summary = self.template_manager.export_template_summary()
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"📄 领域摘要已导出: {output_file}")
        else:
            print("📊 领域摘要:")
            print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    def initialize_default_domains(self):
        """初始化默认领域"""
        print("🚀 初始化默认领域模板...")
        
        # 创建图算法模板
        graph_template = create_graph_algorithms_template()
        self.template_manager.save_template(graph_template)
        
        # 创建DoDAF模板
        dodaf_template = create_dodaf_template()
        self.template_manager.save_template(dodaf_template)
        
        # 更新检测器
        self.domain_detector.update_classifiers()
        
        # 构建索引
        self.build_indexes()
        
        print("✅ 默认领域初始化完成")

def main():
    parser = argparse.ArgumentParser(description="领域管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 列出领域
    subparsers.add_parser('list', help='列出所有领域模板')
    
    # 显示领域详情
    show_parser = subparsers.add_parser('show', help='显示领域详情')
    show_parser.add_argument('domain_name', help='领域名称')
    
    # 检测文本领域
    detect_parser = subparsers.add_parser('detect', help='检测文本领域')
    detect_parser.add_argument('text', help='要检测的文本')
    
    # 创建领域模板
    create_parser = subparsers.add_parser('create', help='创建新的领域模板')
    create_parser.add_argument('domain_name', help='领域名称')
    create_parser.add_argument('display_name', help='显示名称')
    create_parser.add_argument('description', help='描述')
    create_parser.add_argument('--base', help='基础模板')
    
    # 构建索引
    build_parser = subparsers.add_parser('build', help='构建索引')
    build_parser.add_argument('--domains', nargs='*', help='指定领域')
    
    # 测试推断
    test_parser = subparsers.add_parser('test', help='测试实体类型推断')
    test_parser.add_argument('entity_name', help='实体名称')
    test_parser.add_argument('--domain', help='指定领域')
    
    # 导出摘要
    export_parser = subparsers.add_parser('export', help='导出领域摘要')
    export_parser.add_argument('--output', help='输出文件')
    
    # 初始化默认领域
    subparsers.add_parser('init', help='初始化默认领域')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = DomainManager()
    
    if args.command == 'list':
        manager.list_domains()
    elif args.command == 'show':
        manager.show_domain_details(args.domain_name)
    elif args.command == 'detect':
        manager.detect_text_domain(args.text)
    elif args.command == 'create':
        manager.create_domain_template(args.domain_name, args.display_name, 
                                     args.description, args.base)
    elif args.command == 'build':
        manager.build_indexes(args.domains)
    elif args.command == 'test':
        manager.test_entity_inference(args.entity_name, args.domain)
    elif args.command == 'export':
        manager.export_domain_summary(args.output)
    elif args.command == 'init':
        manager.initialize_default_domains()

if __name__ == "__main__":
    main()
