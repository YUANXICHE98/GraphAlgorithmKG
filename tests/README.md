# 测试配置文件

## 测试环境设置
- Python 3.10+
- 所有依赖包已安装
- 可选: OpenAI API密钥 (无密钥时使用模拟模式)

## 测试数据
测试数据位于 `data/test_documents/` 目录:
- `dodaf_enterprise_architecture.json` - 通用架构文档
- `dodaf_spatiotemporal.json` - 时空描述文档  
- `pure_dodaf_structure.json` - DO-DA-F结构文档

## 运行测试

### 运行所有测试
```bash
python tests/run_all_tests.py
```

### 运行单个测试
```bash
# 系统测试
python tests/system/test_complete_pipeline.py

# 单元测试
python tests/unit/test_kg_builder.py
python tests/unit/test_schema_system.py
python tests/unit/test_session_system.py

# 集成测试
python tests/integration/test_multi_schema_kg.py
```

### 使用测试工具
```bash
# 清理结果目录
python tests/utils/cleanup_results.py

# 重组Schema分类
python tests/utils/reorganize_by_schema.py

# 快速启动
python tests/utils/quick_start.py
```

## 测试结果
- 测试报告: `tests/test_report.md`
- 测试日志: `logs/` 目录
- 测试数据: `tests/data/` 目录

## 预期结果
- Schema检测准确率: 100%
- 实体推断准确率: >80%
- 关系验证准确率: 100%
- 端到端处理时间: <5s/文档
