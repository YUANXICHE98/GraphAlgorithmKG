# 测试文件目录

这个目录包含项目的测试文件和测试脚本。

## 文件说明

- `test_fixes.py` - 测试修复脚本
- 其他测试文件可以放在这里

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试文件
python tests/test_fixes.py
```

## 测试规范

- 测试文件以 `test_` 开头
- 测试函数以 `test_` 开头
- 使用 pytest 框架进行测试
