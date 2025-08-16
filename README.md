# 多领域知识图谱构建系统

🚀 基于LLM的智能知识图谱构建平台，支持多领域Schema自动识别和高精度实体推断。

## ✨ 最新更新 (v3.1)

- 🎯 **100%Schema检测**: 完美识别通用架构、时空描述、DO-DA-F结构三种文档类型
- ⚡ **智能关系映射**: 自动修复关系类型不匹配，100%Schema一致性
- 🔄 **混合抽取架构**: 规则抽取优先，LLM智能兜底，成本效率最优
- 📁 **按Schema分类输出**: 清晰的文件结构，输入混乱输出规范
- 🔧 **完整会话管理**: 5阶段处理记录，全流程可追溯
- 📚 **完整交接文档**: 事无巨细的开发和维护指南

## ✨ 核心功能

### 🎯 **Schema识别**

- **多领域支持**: 通用架构、时空本体、DO-DA-F结构
- **自动检测**: 基于文档内容自动选择最适合的Schema
- **LLM辅助**: 置信度相近时启用LLM智能决策

### ⚡ **实体推断**

- **6层分层推断**: 缓存→Schema→模式→关键词→上下文→LLM
- **毫秒级响应**: 平均推断时间<2ms
- **智能缓存**: 自动缓存高置信度结果

### 🏗️ **知识图谱构建**

- **多格式文档处理**: PDF、Word、Markdown、JSON等
- **智能三元组抽取**: 基于Schema的动态Prompt生成
- **语义验证**: 规则引擎+LLM双重验证
- **实体去重**: 编辑距离+语义相似度
- **增量更新**: 支持知识图谱的动态更新

### 🔧 **企业级特性**

- **KAG兼容**: 预留标准化接口，支持无缝集成
- **实时监控**: 性能指标、质量评估、异常检测
- **模拟模式**: 无API密钥时自动降级，保证系统可用性

## 🛠️ 环境设置

### **Python环境要求**

- **Python版本**: 3.10+ (推荐 3.10.9)
- **推荐使用**: Conda 环境管理

### **快速设置**

#### 方法1: 使用Conda（推荐）

```bash
# 创建新环境
conda create -n GraphAlgorithmKG python=3.10
conda activate GraphAlgorithmKG

# 安装依赖
pip install -r requirements.txt
```

#### 方法2: 使用现有环境

```bash
# 激活现有环境
conda activate your_env

# 安装依赖
pip install -r requirements.txt
```

### **可选配置**

```bash
# 配置OpenAI API（可选，无配置时自动使用模拟模式）
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
```

## 🚀 快速开始

### **基础使用**

```bash
# 1. 快速演示
python quick_start.py demo

# 2. 测试Schema系统
python test_schema_system.py

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


## 🧪 测试

### 运行所有测试
```bash
python tests/run_all_tests.py
```

### 运行特定测试
```bash
# 完整系统测试
python tests/system/test_complete_pipeline.py

# Schema系统测试
python tests/unit/test_schema_system.py

# 会话管理测试
python tests/unit/test_session_system.py
```

### 测试工具
```bash
# 清理和重组结果
python tests/utils/cleanup_results.py

# 快速启动演示
python tests/utils/quick_start.py
```

详细测试说明请参考 `tests/README.md`
