#!/usr/bin/env python3
"""
CMW500 驱动功能验证脚本（模拟模式）

用于快速验证 Phase 1 功能的基本逻辑正确性
"""

import sys
sys.path.insert(0, '/Users/Simon/Tools/WideBand_Performance/backend')

from drivers.rohde_schwarz.cmw500 import CMW500_Driver

def test_phase1_basic():
    """测试 Phase 1 基础功能"""
    print("=" * 60)
    print("CMW500 Phase 1 功能验证（模拟模式）")
    print("=" * 60)
    
    # 初始化驱动（模拟模式）
    print("\n[1] 初始化 CMW500 驱动（模拟模式）...")
    cmw = CMW500_Driver(
        resource_name="TCPIP::192.168.1.100::INSTR",
        simulation_mode=True
    )
    print(f"    ✓ 驱动初始化成功，技术制式: {cmw._tech_mode}")
    
    # 测试 configure_nr_cell
    print("\n[2] 测试 configure_nr_cell() 方法...")
    try:
        cmw.configure_nr_cell(
            freq_dl_hz=3.5e9,
            freq_ul_hz=3.5e9,
            bandwidth_mhz=100,
            subcarrier_spacing_khz=30,
            pci=1
        )
        print(f"    ✓ NR 小区配置成功")
        print(f"    配置缓存: {cmw._cell_config}")
    except Exception as e:
        print(f"    ✗ 失败: {e}")
        return False
    
    # 测试参数验证
    print("\n[3] 测试参数验证...")
    try:
        cmw.configure_nr_cell(
            freq_dl_hz=3.5e9,
            freq_ul_hz=3.5e9,
            bandwidth_mhz=99,  # 无效带宽
            subcarrier_spacing_khz=30,
            pci=1
        )
        print("    ✗ 参数验证失败（应该抛出异常）")
        return False
    except ValueError as e:
        print(f"    ✓ 参数验证正常: {e}")
    
    # 测试 set_dl_power
    print("\n[4] 测试 set_dl_power() 方法...")
    try:
        cmw.set_dl_power(
            rs_epre_dbm=-98.0,
            enable_ocng=True
        )
        print(f"    ✓ 下行功率配置成功")
        print(f"    RS EPRE: {cmw._cell_config.get('rs_epre_dbm')} dBm")
        print(f"    OCNG: {cmw._cell_config.get('ocng_enabled')}")
    except Exception as e:
        print(f"    ✗ 失败: {e}")
        return False
    
    # 测试测量接口
    print("\n[5] 测试测量接口...")
    try:
        throughput = cmw.get_throughput()
        bler = cmw.get_bler()
        rsrp = cmw.get_rsrp()
        sinr = cmw.get_sinr()
        
        print(f"    ✓ 吞吐量: {throughput:.2f} Mbps")
        print(f"    ✓ BLER: {bler*100:.2f}%")
        print(f"    ✓ RSRP: {rsrp:.1f} dBm")
        print(f"    ✓ SINR: {sinr:.1f} dB")
    except Exception as e:
        print(f"    ✗ 测量接口失败: {e}")
        return False
    
    # 测试信令控制
    print("\n[6] 测试信令控制...")
    try:
        result = cmw.attach_ue(timeout_s=5.0)
        print(f"    ✓ attach_ue() 返回: {result}")
        
        cmw.detach_ue()
        print(f"    ✓ detach_ue() 成功")
    except Exception as e:
        print(f"    ✗ 信令控制失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ 所有 Phase 1 功能验证通过！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_phase1_basic()
    sys.exit(0 if success else 1)
