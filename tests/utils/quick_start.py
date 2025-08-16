"""
快速启动脚本
用于快速测试和演示系统功能
"""

import os
import sys
from pathlib import Path
from main import KnowledgeGraphBuilder

def create_sample_data():
    """创建示例数据"""
    data_dir = Path("data/documents/samples")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建示例文本文件
    sample_text = """
# 图神经网络简介

图神经网络（Graph Neural Networks, GNN）是一类用于处理图结构数据的深度学习模型。

## 主要算法

### GraphSAGE
GraphSAGE是一种归纳式图神经网络算法。它使用采样和聚合的方法来学习节点表示。

### Graph Attention Network
GAT使用注意力机制来聚合邻居节点的信息。它可以为不同的邻居分配不同的权重。

### Graph Convolutional Network
GCN是最早的图卷积网络之一。它通过图卷积操作来学习节点的特征表示。

## 应用领域

图神经网络广泛应用于：
- 社交网络分析
- 推荐系统
- 知识图谱
- 分子性质预测
"""
    
    sample_file = data_dir / "gnn_intro.md"
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write(sample_text)
    
    print(f"✅ 创建示例文件: {sample_file}")
    return str(sample_file)

def quick_demo():
    """快速演示"""
    print("🚀 知识图谱构建系统 - 快速演示")
    print("=" * 50)
    
    # 创建示例数据
    sample_file = create_sample_data()
    
    # 创建构建器
    config = {
        'storage_path': 'demo_kg_storage',
        'chunk_size': 1000,
        'chunk_overlap': 100
    }
    
    builder = KnowledgeGraphBuilder(config)
    
    try:
        # 处理文档
        print("\n📄 处理示例文档...")
        result = builder.process_documents(
            input_paths=[sample_file],
            enable_review=False,  # 跳过人工复核
            auto_approve=True
        )
        
        print(f"\n✅ 处理完成!")
        print(f"   存储路径: {result['storage_path']}")
        print(f"   本体版本: {result['ontology_version']}")
        
        # 搜索演示
        print("\n🔍 搜索演示...")
        search_result = builder.search_knowledge_graph("GraphSAGE")
        
        if search_result['nodes']:
            print(f"   找到 {len(search_result['nodes'])} 个相关节点")
            for node in search_result['nodes'][:3]:
                print(f"   - {node.get('name', 'Unknown')}: {node.get('type', 'Unknown')}")
        else:
            print("   未找到相关节点")
        
        # Neo4j导出演示
        print("\n📤 尝试导出到Neo4j...")
        try:
            success = builder.export_to_neo4j(clear_existing=True)
            if success:
                print("   ✅ 导出成功! 访问 http://localhost:7474")
            else:
                print("   ⚠️ Neo4j未运行或连接失败")
        except Exception as e:
            print(f"   ⚠️ Neo4j导出失败: {e}")
        
        print("\n🎉 演示完成!")
        print(f"\n📁 生成的文件:")
        print(f"   - 知识图谱存储: {config['storage_path']}/")
        print(f"   - 示例文档: {sample_file}")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False
    
    return True

def interactive_mode():
    """交互模式"""
    print("🎮 交互模式")
    print("输入文档路径，或输入 'quit' 退出")
    
    builder = KnowledgeGraphBuilder()
    
    while True:
        try:
            user_input = input("\n📂 文档路径: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 再见!")
                break
            
            if not user_input:
                continue
            
            if not Path(user_input).exists():
                print("❌ 文件不存在")
                continue
            
            # 处理文档
            result = builder.process_documents(
                input_paths=[user_input],
                enable_review=False,
                auto_approve=True
            )
            
            print(f"✅ 处理完成: {result['stats']['triples_generated']} 个三元组")
            
            # 询问是否搜索
            search_query = input("🔍 搜索查询 (回车跳过): ").strip()
            if search_query:
                search_result = builder.search_knowledge_graph(search_query)
                print(f"   找到 {len(search_result['nodes'])} 个节点")
            
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 处理出错: {e}")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            quick_demo()
        elif sys.argv[1] == "interactive":
            interactive_mode()
        else:
            print("用法:")
            print("  python quick_start.py demo        # 快速演示")
            print("  python quick_start.py interactive # 交互模式")
    else:
        print("🚀 知识图谱构建系统 - 快速启动")
        print("\n选择模式:")
        print("1. 快速演示")
        print("2. 交互模式")
        
        choice = input("\n请选择 (1/2): ").strip()
        
        if choice == "1":
            quick_demo()
        elif choice == "2":
            interactive_mode()
        else:
            print("❌ 无效选择")

if __name__ == "__main__":
    main()