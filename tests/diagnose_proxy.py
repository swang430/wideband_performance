#!/usr/bin/env python3
"""
代理使用验证脚本
检查当前环境是否会使用代理访问本地服务
"""

import os
import sys
import socket

def check_environment_variables():
    """检查环境变量"""
    print("=" * 60)
    print("  1. 环境变量检查")
    print("=" * 60)
    
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'no_proxy', 'NO_PROXY']
    
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: (未设置)")
    
    print()

def check_proxy_connectivity():
    """检查代理服务器连通性"""
    print("=" * 60)
    print("  2. 代理服务器连通性")
    print("=" * 60)
    
    proxy_host = "127.0.0.1"
    proxy_port = 7897
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((proxy_host, proxy_port))
        sock.close()
        
        if result == 0:
            print(f"✅ 代理服务器 {proxy_host}:{proxy_port} 可访问")
        else:
            print(f"❌ 代理服务器 {proxy_host}:{proxy_port} 不可访问")
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
    
    print()

def check_localhost_bypass():
    """检查 localhost 是否会绕过代理"""
    print("=" * 60)
    print("  3. localhost 绕过检查")
    print("=" * 60)
    
    no_proxy = os.environ.get('no_proxy', '') + os.environ.get('NO_PROXY', '')
    
    localhost_variants = ['localhost', '127.0.0.1', '::1']
    
    for variant in localhost_variants:
        if variant in no_proxy:
            print(f"✅ {variant} 在 no_proxy 列表中（会绕过代理）")
        else:
            print(f"❌ {variant} 不在 no_proxy 列表中（可能走代理！）")
    
    print()

def simulate_connection():
    """模拟浏览器工具的连接行为"""
    print("=" * 60)
    print("  4. 连接行为模拟")
    print("=" * 60)
    
    http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
    no_proxy = os.environ.get('no_proxy', '') + os.environ.get('NO_PROXY', '')
    
    target = "127.0.0.1:9222"
    
    print(f"目标: {target} (Chrome DevTools Protocol)")
    print(f"代理设置: {http_proxy if http_proxy else '(无)'}")
    print(f"no_proxy: {no_proxy if no_proxy else '(无)'}")
    print()
    
    if http_proxy and '127.0.0.1' not in no_proxy and 'localhost' not in no_proxy:
        print("⚠️  预测：会尝试通过代理连接 127.0.0.1:9222")
        print("   这会导致 CDP 连接失败！")
        print()
        print("   原因：代理服务器不理解 CDP 协议")
        print("   解决：添加 'export no_proxy=localhost,127.0.0.1'")
    elif http_proxy and ('127.0.0.1' in no_proxy or 'localhost' in no_proxy):
        print("✅ 预测：会绕过代理，直连 127.0.0.1:9222")
        print("   CDP 连接应该成功")
    else:
        print("✅ 预测：无代理设置，直连 127.0.0.1:9222")
        print("   CDP 连接应该成功")
    
    print()

def main():
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "代理诊断工具" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    check_environment_variables()
    check_proxy_connectivity()
    check_localhost_bypass()
    simulate_connection()
    
    print("=" * 60)
    print("  诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
