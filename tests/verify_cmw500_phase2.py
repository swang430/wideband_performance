#!/usr/bin/env python3
"""
CMW500 驱动 Phase 2 功能验证脚本

测试信令控制功能：附着、数据传输激活、状态轮询
"""

import sys
sys.path.insert(0, '/Users/Simon/Tools/WideBand_Performance/backend')

from drivers.rohde_schwarz.cmw500 import CMW500_Driver

def test_phase2_signaling():
    """测试 Phase 2 信令控制功能"""
    print("=" * 70)
    print("CMW500 Phase 2 功能验证（信令控制）")
    print("=" * 70)
    
    # 初始化驱动（模拟模式）
    print("\n[1] 初始化 CMW500 驱动...")
    cmw = CMW500_Driver(
        resource_name="TCPIP::192.168.1.100::INSTR",
        simulation_mode=True
    )
    print("    ✓ 驱动初始化成功")
    
    # 配置NR小区（复用 Phase 1 功能）
    print("\n[2] 配置 NR 小区参数...")
    try:
        cmw.configure_nr_cell(
            freq_dl_hz=3.5e9,
            freq_ul_hz=3.5e9,
            bandwidth_mhz=100,
            subcarrier_spacing_khz=30,
            pci=1
        )
        cmw.set_dl_power(rs_epre_dbm=-98.0, enable_ocng=True)
        print("    ✓ 小区配置完成")
    except Exception as e:
        print(f"    ✗ 失败: {e}")
        return False
    
    # 测试 attach_ue() 增强版
    print("\n[3] 测试 attach_ue() 增强版（带超时轮询）...")
    try:
        import time
        start = time.time()
        result = cmw.attach_ue(timeout_s=5.0)
        elapsed = time.time() - start
        
        if result:
            print(f"    ✓ UE 附着成功，用时: {elapsed:.2f}s")
        else:
            print(f"    ✗ UE 附着失败（超时）")
            return False
    except Exception as e:
        print(f"    ✗ 异常: {e}")
        return False
    
    # 测试 activate_data_transfer()
    print("\n[4] 测试 activate_data_transfer()...")
    try:
        result = cmw.activate_data_transfer()
        if result:
            print("    ✓ 数据传输激活成功")
        else:
            print("    ✗ 数据传输激活失败")
            return False
    except Exception as e:
        print(f"    ✗ 异常: {e}")
        return False
    
    # 测试完整流程：配置 -> 附着 -> 激活 -> 测量
    print("\n[5] 测试完整信令流程...")
    try:
        # 重新附着
        print("    > 重新附着 UE...")
        cmw.detach_ue()
        time.sleep(0.2)
        
        if not cmw.attach_ue(timeout_s=5.0):
            print("    ✗ 重新附着失败")
            return False
        
        # 激活数据传输
        print("    > 激活数据传输...")
        if not cmw.activate_data_transfer():
            print("    ✗ 数据传输激活失败")
            return False
        
        # 进行测量
        print("    > 进行性能测量...")
        throughput = cmw.get_throughput()
        bler = cmw.get_bler()
        rsrp = cmw.get_rsrp()
        sinr = cmw.get_sinr()
        
        print(f"      - 吞吐量: {throughput:.2f} Mbps")
        print(f"      - BLER: {bler*100:.2f}%")
        print(f"      - RSRP: {rsrp:.1f} dBm")
        print(f"      - SINR: {sinr:.1f} dB")
        
        print("    ✓ 完整流程测试成功")
    except Exception as e:
        print(f"    ✗ 流程测试失败: {e}")
        return False
    
    # 测试错误处理
    print("\n[6] 测试错误场景...")
    try:
        # 测试无效参数
        cmw.detach_ue()
        print("    ✓ detach_ue() 正常执行")
        
        # 测试连接状态查询
        status = cmw.get_connection_status()
        print(f"    ✓ 连接状态查询: {status}")
    except Exception as e:
        print(f"    ✗ 错误处理测试失败: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✓ 所有 Phase 2 功能验证通过！")
    print("=" * 70)
    
    # 总结
    print("\n【Phase 2 新增功能总结】")
    print("  1. attach_ue() - 增强版，支持真实超时轮询")
    print("  2. activate_data_transfer() - 激活RRC CONNECTED状态")
    print("  3. wait_for_connection_state() - 通用状态等待方法")
    print("  4. 完整信令流程：配置 -> 附着 -> 激活 -> 测量")
    
    return True

if __name__ == "__main__":
    success = test_phase2_signaling()
    sys.exit(0 if success else 1)
