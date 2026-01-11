#!/bin/bash
# 终端宽带标准信道验证系统 - 自动设置脚本

echo "=== 终端宽带标准信道验证系统 - 环境配置 ==="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3"
    exit 1
fi

echo "Python 版本: $(python3 --version)"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
else
    echo "虚拟环境已存在"
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "正在安装依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=== 设置完成 ==="
echo "使用方法:"
echo "  1. 激活环境: source venv/bin/activate"
echo "  2. 运行测试: python main.py --simulate --verbose"
echo ""
