# 环境设置指南

## 🐍 Python环境要求

- **Python版本**: 3.10+ (推荐 3.10.9)
- **推荐使用**: Conda 环境管理

## 🚀 快速设置

### 方法1: 使用Conda（推荐）

```bash
# 创建新环境
conda create -n GraphAlgorithmKG python=3.10
conda activate GraphAlgorithmKG

# 安装依赖
pip install -r requirements.txt
```

### 方法2: 使用现有环境

```bash
# 激活现有环境（如KG4AI）
conda activate KG4AI

# 安装依赖
pip install -r requirements.txt
```

### 方法3: 使用自动设置脚本

```bash
python setup.py
```

## 📦 核心依赖说明

### 必需依赖
- **pandas**: 数据处理
- **numpy**: 数值计算
- **pyyaml**: 配置文件解析
- **networkx**: 图结构处理
- **openai**: LLM API调用

### 文档处理
- **PyPDF2**: PDF文档解析
- **python-docx**: Word文档解析
- **lxml**: XML/HTML解析

### 数据库
- **neo4j**: Neo4j图数据库连接

### 可选依赖
- **matplotlib, plotly**: 可视化
- **pytest, black, flake8**: 开发工具

## ⚙️ 配置文件

1. 复制配置模板:
```bash
cp config.json.template config.json
```

2. 编辑配置文件，填入API密钥:
```json
{
  "openai": {
    "api_key": "your_vimsai_api_key_here",
    "base_url": "https://vir.vimsai.com/v1",
    "model": "gpt-3.5-turbo"
  }
}
```

## 🧪 验证安装

```bash
# 测试API连接
python test_vimsai_api.py

# 快速演示
python quick_start.py demo

# 处理示例数据
python main.py data/graph_algorithm_triples.csv
```

## 🔧 常见问题

### 1. OpenAI版本兼容性
如果遇到OpenAI API版本问题，确保使用 `openai>=1.0.0`

### 2. 依赖冲突
建议使用独立的conda环境避免依赖冲突

### 3. 内存不足
处理大文档时可能需要调整 `chunk_size` 参数

## 📝 环境信息

当前测试环境:
- Python 3.10.9
- macOS (Intel)
- Conda 环境: KG4AI

支持的操作系统:
- macOS
- Linux
- Windows (需要额外配置)
