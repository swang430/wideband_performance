#!/bin/bash
# 浏览器自动化测试启动脚本
# 临时禁用代理，运行测试后恢复

echo "=== 浏览器自动化测试准备 ==="
echo ""

# 保存当前代理设置
SAVED_HTTP_PROXY="$http_proxy"
SAVED_HTTPS_PROXY="$https_proxy"
SAVED_NO_PROXY="$no_proxy"

echo "📝 当前代理设置："
echo "   http_proxy: $http_proxy"
echo "   https_proxy: $https_proxy"
echo ""

# 临时禁用代理
echo "🔧 临时禁用代理（仅本次会话）..."
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY

# 添加本地地址到 no_proxy
export no_proxy="localhost,127.0.0.1,::1"

echo "✅ 代理已禁用"
echo ""

# 提示用户
echo "================================================"
echo "  现在可以使用 Antigravity 浏览器工具了！"
echo "================================================"
echo ""
echo "请在 Antigravity 中运行浏览器自动化测试。"
echo "测试完成后，运行以下命令恢复代理："
echo ""
echo "  export http_proxy=\"$SAVED_HTTP_PROXY\""
echo "  export https_proxy=\"$SAVED_HTTPS_PROXY\""
echo ""
echo "或者直接重新打开终端窗口。"
echo ""

# 保持 shell 打开
exec $SHELL
