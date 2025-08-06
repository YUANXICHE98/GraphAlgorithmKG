#!/usr/bin/env python3
"""
GraphAlgorithmKG 快速设置脚本
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """安装依赖包"""
    print("📦 安装Python依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖包安装完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败: {e}")
        return False
    return True

def setup_config():
    """设置配置文件"""
    print("\n⚙️  设置配置文件...")
    
    config_file = Path("config.json")
    template_file = Path("config.json.template")
    
    if config_file.exists():
        print("✅ config.json 已存在")
        return True
    
    if not template_file.exists():
        print("❌ config.json.template 不存在")
        return False
    
    # 复制模板文件
    with open(template_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 交互式配置
    print("\n请输入配置信息（直接回车使用默认值）:")
    
    api_key = input(f"VimsAI API Key [{config['openai']['api_key']}]: ").strip()
    if api_key:
        config['openai']['api_key'] = api_key
    
    model = input(f"LLM模型 [{config['openai']['model']}]: ").strip()
    if model:
        config['openai']['model'] = model
    
    # 保存配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ 配置文件创建完成")
    return True

def create_directories():
    """创建必要的目录"""
    print("\n📁 创建目录结构...")
    
    directories = [
        "data/documents",
        "dynamic_kg_storage",
        "logs"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {dir_path}")

def test_installation():
    """测试安装"""
    print("\n🧪 测试安装...")
    
    try:
        # 测试API连接
        result = subprocess.run([sys.executable, "test_vimsai_api.py"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ API连接测试通过")
        else:
            print("⚠️  API连接测试失败，请检查配置")
            print(result.stderr)
    
    except subprocess.TimeoutExpired:
        print("⚠️  API测试超时")
    except FileNotFoundError:
        print("⚠️  测试文件不存在")

def main():
    """主函数"""
    print("🚀 GraphAlgorithmKG 快速设置")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 设置配置
    if not setup_config():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 测试安装
    test_installation()
    
    print("\n🎉 设置完成！")
    print("\n📋 下一步:")
    print("1. 编辑 config.json 文件，填入你的API密钥")
    print("2. 运行 python quick_start.py demo 进行快速测试")
    print("3. 运行 python main.py data/graph_algorithm_triples.csv 处理数据")

if __name__ == "__main__":
    main()
