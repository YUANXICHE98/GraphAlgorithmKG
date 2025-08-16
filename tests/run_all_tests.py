#!/usr/bin/env python3
"""
测试套件主入口
运行所有测试并生成报告
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

def run_all_tests():
    """运行所有测试"""
    print("🧪 GraphAlgorithmKG 测试套件")
    print("=" * 80)
    
    tests_dir = Path(__file__).parent
    
    # 测试文件列表
    test_files = [
        ("system/test_complete_pipeline.py", "完整Pipeline系统测试"),
        ("unit/test_kg_builder.py", "KG构建器单元测试"),
        ("integration/test_multi_schema_kg.py", "多Schema集成测试"),
        ("unit/test_schema_system.py", "Schema系统单元测试"),
        ("unit/test_session_system.py", "会话系统单元测试"),
    ]
    
    results = []
    
    for test_file, description in test_files:
        test_path = tests_dir / test_file
        if test_path.exists():
            print(f"\n🔍 运行: {description}")
            print("-" * 60)
            
            try:
                # 设置Python路径
                env = os.environ.copy()
                env['PYTHONPATH'] = str(tests_dir.parent)

                # 运行测试
                result = subprocess.run([
                    sys.executable, str(test_path)
                ], capture_output=True, text=True, cwd=tests_dir.parent, env=env)
                
                if result.returncode == 0:
                    print("✅ 测试通过")
                    results.append((test_file, "PASS", ""))
                else:
                    print("❌ 测试失败")
                    print(result.stderr)
                    results.append((test_file, "FAIL", result.stderr))
                    
            except Exception as e:
                print(f"❌ 运行错误: {e}")
                results.append((test_file, "ERROR", str(e)))
        else:
            print(f"⚠️ 测试文件不存在: {test_file}")
            results.append((test_file, "MISSING", "文件不存在"))
    
    # 生成测试报告
    generate_test_report(results)
    
    # 统计结果
    passed = sum(1 for _, status, _ in results if status == "PASS")
    total = len(results)
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️ 部分测试失败")
        return 1

def generate_test_report(results):
    """生成测试报告"""
    report_path = Path(__file__).parent / "test_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 测试报告\n\n")
        f.write(f"生成时间: {datetime.now().isoformat()}\n\n")
        f.write("## 测试结果\n\n")
        f.write("| 测试文件 | 状态 | 错误信息 |\n")
        f.write("|----------|------|----------|\n")
        
        for test_file, status, error in results:
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥", "MISSING": "⚠️"}
            icon = status_icon.get(status, "❓")
            error_brief = error[:50] + "..." if len(error) > 50 else error
            f.write(f"| {test_file} | {icon} {status} | {error_brief} |\n")
    
    print(f"📄 测试报告已生成: {report_path}")

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
