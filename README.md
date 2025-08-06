# GraphAlgorithmKG

🚀 基于LLM的动态知识图谱构建系统，专门用于图算法领域的知识抽取和管理。

## ✨ 最新更新 (v2.1)

- 🧠 **LLM语义验证**: 结合规则验证和LLM语义判断的智能验证系统
- 📊 **实时进度监控**: 详细的阶段输出和处理状态监控
- 🔄 **更换推理模型**: 使用 `gpt-3.5-turbo` 替代 `gpt-4o`，降低成本
- 🛠️ **完善环境支持**: 支持多种Python环境，完整的依赖管理

## ✨ 核心功能

- 📄 **多格式文档处理**: PDF、Word、Markdown、HTML、CSV等
- 🧠 **智能知识抽取**: 基于LLM的三元组抽取
- 🔄 **动态本体管理**: 自动发现和扩展实体/关系类型
- 👥 **人工复核机制**: 新类型的审核和批准
- 🔍 **智能检索**: 模糊搜索和子图检索
- 🌐 **Neo4j集成**: 无缝数据库导入导出

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 快速演示
python quick_start.py demo

# 3. 处理文档
python main.py your_document.pdf

# 4. 处理三元组文件
python main.py data/graph_algorithm_triples.csv

# 5. 导出到Neo4j
python main.py --export-neo4j --neo4j-clear
```

## 📁 项目结构

```
KnowledgeGraphBuilder/
├── README.md                    # 主文档
├── main.py                      # 统一主程序
├── quick_start.py               # 快速启动
├── config.json                  # 配置文件
├── requirements.txt             # 依赖包
├── kg_expansion_tool.py         # KG扩展工具
│
├── docs/                        # 文档目录
│   ├── README.md               # 文档索引
│   ├── NEO4J_SETUP.md          # Neo4j设置指南
│   └── ONTOLOGY_GUIDE.md       # 本体使用指南
│
├── ontology/                    # 本体管理
│   ├── dynamic_schema.py        # 动态本体核心
│   └── config/                  # 本体配置文件
│
├── pipeline/                    # 处理流水线
│   ├── document_processor.py    # 文档处理
│   ├── text_splitter.py         # 文本切片
│   ├── llm_extractor.py         # LLM抽取
│   ├── schema_reviewer.py       # 人工复核
│   ├── dynamic_mapper.py        # 本体映射
│   ├── kg_updater.py            # 图谱更新
│   ├── kg_retriever.py          # 图谱检索
│   ├── neo4j_connector.py       # Neo4j连接
│   ├── triple_cleaner.py        # 三元组清理
│   └── entity_type_inferer.py   # 实体类型推断
│
├── data/                        # 数据目录
│   ├── documents/               # 原始文档
│   └── *.csv                    # 示例数据文件
│
├── dynamic_kg_storage/          # 动态KG存储（运行时生成）
│   ├── entities.json
│   ├── relations.json
│   ├── triples.json
│   ├── ontology_snapshot.json
│   └── statistics.json
│
└── logs/                        # 日志文件（运行时生成）
```

## 🚀 快速开始

### 环境设置

```bash
# 1. 克隆仓库
git clone https://github.com/YUANXICHE98/GraphAlgorithmKG.git
cd GraphAlgorithmKG

# 2. 创建环境（推荐）
conda create -n GraphAlgorithmKG python=3.10
conda activate GraphAlgorithmKG

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置API
cp config.json.template config.json
# 编辑 config.json，填入你的VimsAI API密钥

# 5. 测试运行
python quick_start.py demo
```

详细环境设置请参考 [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)

## 💻 使用方法

### 命令行使用

```bash
# 处理文档
python main.py document.pdf
python main.py data/documents/

# 处理三元组文件
python main.py data/graph_algorithm_triples.csv

# 自定义存储路径
python main.py document.pdf --storage-path my_kg

# 搜索查询
python main.py --search "深度学习" --search-hops 2

# Neo4j操作
python main.py data/graph_algorithm_triples.csv --export-neo4j --neo4j-clear
```

### Python API

```python
from main import KnowledgeGraphBuilder

# 创建构建器
builder = KnowledgeGraphBuilder()

# 处理文档
result = builder.process_documents(["document.pdf"])

# 处理三元组文件
result = builder.process_triples_file("data/triples.csv")

# 搜索知识图谱
search_result = builder.search_knowledge_graph("机器学习")

# 导出到Neo4j
builder.export_to_neo4j(clear_existing=True)
```

## ⚙️ 配置文件

编辑 `config.json`:

```json
{
  "storage_path": "dynamic_kg_storage",
  "llm_model": "gpt-3.5-turbo",
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "yuanxi98"
  },
  "ontology": {
    "entity_type_threshold": 5,
    "relation_type_threshold": 3,
    "auto_update": true
  }
}
```

## 📚 详细文档

- [Neo4j集成指南](docs/NEO4J_SETUP.md)
- [本体管理指南](docs/ONTOLOGY_GUIDE.md)

## 🔧 开发指南

### 添加新文档格式
在 `pipeline/document_processor.py` 中扩展支持的格式

### 自定义LLM抽取
修改 `pipeline/llm_extractor.py` 的prompt模板

### 扩展本体规则
编辑 `ontology/dynamic_schema.py` 中的识别规则

## 📄 许可证

MIT License

---

**快速链接**: [安装](#快速开始) | [使用](#使用方法) | [配置](#配置文件) | [文档](docs/)
