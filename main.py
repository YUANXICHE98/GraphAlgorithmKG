"""
知识图谱构建系统 - 统一主程序
整合文档处理、LLM抽取、动态本体扩展、Neo4j集成的完整流程
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 核心模块
from ontology.dynamic_schema import DynamicOntologyManager
from pipeline.document_processor import DocumentProcessor
from pipeline.text_splitter import TextSplitter
from pipeline.llm_extractor import LLMKGExtractor
from pipeline.schema_reviewer import SchemaReviewer
from pipeline.dynamic_mapper import DynamicOntologyMapper
from pipeline.kg_updater import KnowledgeGraphUpdater
from pipeline.kg_retriever import KGRetriever
from pipeline.neo4j_connector import import_storage_to_neo4j, export_neo4j_to_files
from pipeline.triple_cleaner import TripleCleaner

class KnowledgeGraphBuilder:
    """统一知识图谱构建器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._load_default_config()
        
        # 统一使用动态存储路径
        storage_path = self.config.get('storage_path', 'dynamic_kg_storage')
        
        # 初始化核心组件
        self.ontology = DynamicOntologyManager()
        self.document_processor = DocumentProcessor()
        self.text_splitter = TextSplitter(
            max_tokens=self.config.get('chunk_size', 2000),
            overlap=self.config.get('chunk_overlap', 200)
        )
        self.llm_extractor = LLMKGExtractor(self.ontology)
        self.schema_reviewer = SchemaReviewer()
        self.triple_cleaner = TripleCleaner()
        self.mapper = DynamicOntologyMapper(self.ontology)
        self.kg_updater = KnowledgeGraphUpdater(self.ontology, storage_path)
        self.retriever = KGRetriever(self.ontology, storage_path)
        
        # 会话统计
        self.session_stats = {
            "start_time": datetime.now().isoformat(),
            "documents_processed": 0,
            "chunks_extracted": 0,
            "triples_generated": 0,
            "entities_created": 0,
            "relations_created": 0,
            "ontology_updates": 0
        }

    def process_documents(self, input_paths: List[str], **kwargs) -> Dict[str, Any]:
        """处理文档的完整流程"""
        print("🚀 开始文档处理流程...")
        
        # 文档处理 -> 文本切片 -> LLM抽取 -> 本体映射 -> 图谱更新
        all_triples = []
        
        for path in input_paths:
            print(f"📄 处理文档: {path}")
            
            # 1. 文档处理
            doc = self.document_processor.process_document(path)
            self.session_stats["documents_processed"] += 1
            
            # 2. 文本切片
            chunks = self.text_splitter.split_text(doc.content)
            self.session_stats["chunks_extracted"] += len(chunks)
            
            # 3. LLM抽取
            for chunk in chunks:
                extraction_result = self.llm_extractor.extract_from_text(chunk)
                if extraction_result.success:
                    all_triples.extend(extraction_result.triples)
                else:
                    print(f"警告: 文本块抽取失败: {extraction_result.error_message}")
        
        return self._process_triples_pipeline(all_triples, **kwargs)

    def process_triples_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """处理三元组文件"""
        print(f"📂 加载三元组文件: {file_path}")
        
        triples = self._load_triples_from_file(file_path)
        return self._process_triples_pipeline(triples, **kwargs)

    def _process_triples_pipeline(self, triples: List[Dict], **kwargs) -> Dict[str, Any]:
        """三元组处理流水线"""
        if not triples:
            print("⚠️  没有三元组需要处理")
            return {"status": "no_data"}
        
        print(f"🔄 开始处理 {len(triples)} 个三元组...")
        
        # 1. 清理三元组
        cleaned_triples = self.triple_cleaner.clean_triples(triples)
        print(f"   ✅ 清理后: {len(cleaned_triples)} 个三元组")
        
        # 2. 本体映射（包含动态扩展）
        mapping_results = self.mapper.map_triples(cleaned_triples)
        mapped_triples = [r.mapped_triple for r in mapping_results if r.success]
        print(f"   ✅ 映射成功: {len(mapped_triples)} 个三元组")
        
        # 3. 更新知识图谱
        update_result = self.kg_updater.update_kg_from_triples(mapped_triples)
        
        self.session_stats["triples_generated"] = len(triples)
        self.session_stats["entities_created"] = update_result.new_entities
        self.session_stats["relations_created"] = update_result.new_relations
        
        print(f"   ✅ 新增实体: {update_result.new_entities}")
        print(f"   ✅ 新增关系: {update_result.new_relations}")
        
        print("\n🎉 知识图谱构建完成!")
        self._print_session_summary()
        
        return {
            "status": "completed",
            "stats": self.session_stats,
            "ontology_version": self.ontology.current_version,
            "storage_path": self.config.get('storage_path', 'dynamic_kg_storage')
        }

    def search_knowledge_graph(self, query: str, max_hops: int = 2) -> Dict[str, Any]:
        """搜索知识图谱"""
        search_result = self.retriever.retrieve_subgraph(query, hops=max_hops)
        return {
            'nodes': search_result.subgraph.get('nodes', []),
            'edges': search_result.subgraph.get('edges', []),
            'matched_entities': search_result.matched_entities,
            'search_time': search_result.search_time,
            'total_nodes': search_result.total_nodes,
            'total_edges': search_result.total_edges
        }

    def export_to_neo4j(self, clear_existing: bool = False, **neo4j_config) -> bool:
        """导出到Neo4j数据库"""
        config = self.config.get('neo4j', {})
        config.update(neo4j_config)
        
        return import_storage_to_neo4j(
            storage_path=self.config.get('storage_path', 'dynamic_kg_storage'),
            uri=config.get('uri', 'bolt://localhost:7687'),
            user=config.get('user', 'neo4j'),
            password=config.get('password', 'yuanxi98'),
            clear_existing=clear_existing
        )

    def _load_triples_from_file(self, file_path: str) -> List[Dict]:
        """从文件加载三元组"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.csv':
            import pandas as pd
            df = pd.read_csv(file_path)
            return [
                {"subject": row['subject'], "predicate": row['predicate'], "object": row['object']}
                for _, row in df.iterrows()
            ]
        elif file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")

    def _load_default_config(self) -> Dict:
        """加载默认配置"""
        config_file = Path("config.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'chunk_size': 2000,
            'chunk_overlap': 200,
            'storage_path': 'dynamic_kg_storage',
            'llm_model': 'gpt-3.5-turbo',
            'max_tokens': 4000,
            'temperature': 0.1
        }

    def _print_session_summary(self):
        """打印会话摘要"""
        print(f"\n📊 处理摘要:")
        print(f"   文档数量: {self.session_stats['documents_processed']}")
        print(f"   文本块数: {self.session_stats['chunks_extracted']}")
        print(f"   三元组数: {self.session_stats['triples_generated']}")
        print(f"   新增实体: {self.session_stats['entities_created']}")
        print(f"   新增关系: {self.session_stats['relations_created']}")
        print(f"   本体版本: {self.ontology.current_version}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="知识图谱构建系统")
    
    # 输入参数
    parser.add_argument("input_paths", nargs="*", help="输入文件或目录路径")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--storage-path", default="dynamic_kg_storage", help="存储路径")
    
    # 处理选项
    parser.add_argument("--no-review", action="store_true", help="跳过人工复核")
    parser.add_argument("--auto-approve", action="store_true", help="自动批准所有更新")
    
    # 搜索选项
    parser.add_argument("--search", help="搜索知识图谱")
    parser.add_argument("--search-hops", type=int, default=2, help="搜索跳数")
    
    # Neo4j选项
    parser.add_argument("--export-neo4j", action="store_true", help="导出到Neo4j")
    parser.add_argument("--neo4j-clear", action="store_true", help="清空Neo4j数据库")
    parser.add_argument("--neo4j-uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--neo4j-user", default="neo4j", help="Neo4j用户名")
    parser.add_argument("--neo4j-password", default="yuanxi98", help="Neo4j密码")
    
    args = parser.parse_args()
    
    # 加载配置
    config = None
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # 更新存储路径
    if config:
        config['storage_path'] = args.storage_path
    else:
        config = {'storage_path': args.storage_path}
    
    # 创建构建器
    builder = KnowledgeGraphBuilder(config)
    
    try:
        # 搜索模式
        if args.search:
            print(f"🔍 搜索知识图谱: {args.search}")
            results = builder.search_knowledge_graph(args.search, args.search_hops)
            print(json.dumps(results, ensure_ascii=False, indent=2))
            return
        
        # Neo4j导出模式
        if args.export_neo4j:
            if args.input_paths:
                # 先处理数据再导出
                if args.input_paths[0].endswith(('.csv', '.json')):
                    builder.process_triples_file(args.input_paths[0])
                else:
                    builder.process_documents(args.input_paths)
            
            # 导出到Neo4j
            print("📤 导出到Neo4j数据库...")
            success = builder.export_to_neo4j(
                clear_existing=args.neo4j_clear,
                uri=args.neo4j_uri,
                user=args.neo4j_user,
                password=args.neo4j_password
            )
            if success:
                print(f"🌐 Neo4j浏览器: http://localhost:7474")
            return
        
        # 标准处理模式
        if not args.input_paths:
            print("❌ 请提供输入文件或指定操作")
            parser.print_help()
            return
        
        # 判断输入类型并处理
        if args.input_paths[0].endswith(('.csv', '.json')):
            # 三元组文件
            for file_path in args.input_paths:
                builder.process_triples_file(file_path)
        else:
            # 文档文件
            builder.process_documents(args.input_paths)
            
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
