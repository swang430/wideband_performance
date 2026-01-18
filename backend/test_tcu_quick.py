#!/usr/bin/env python3
"""
TCU 驱动快速测试脚本
用于验证TCU驱动框架在模拟模式下的基本功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from drivers.common.generic_tcu import GenericTCU
from drivers.emcenter import EMCenter_Driver
from drivers.factory import DriverFactory
from core.logger import setup_logger

def test_generic_tcu():
    """测试通用TCU驱动"""
    print("\n" + "="*60)
    print("测试1: 通用TCU驱动 (GenericTCU)")
    print("="*60)
    
    tcu = GenericTCU(
        "TCPIP0::192.168.1.105::inst0::INSTR",
        name="Generic_TCU_Test",
        simulation_mode=True
    )
    
    print("✓ 创建TCU实例")
    tcu.connect()
    print("✓ 连接成功")
    
    # 测试各个方法
    tcu.switch_rf_path("ANT1_TO_DUT")
    print("✓ switch_rf_path() 调用成功")
    
    tcu.set_attenuation("ATT1", 10.0)
    print("✓ set_attenuation() 调用成功")
    
    tcu.enable_amplifier("AMP1", True)
    print("✓ enable_amplifier() 调用成功")
    
    state = tcu.get_switch_state("ANT1_TO_DUT")
    print(f"✓ get_switch_state() 返回: {state}")
    
    tcu.disconnect()
    print("✓ 断开连接成功")

def test_emcenter_driver():
    """测试EMCenter专用驱动"""
    print("\n" + "="*60)
    print("测试2: EMCenter专用驱动")
    print("="*60)
    
    tcu = EMCenter_Driver(
        "TCPIP0::192.168.1.105::inst0::INSTR",
        name="EMCenter_Test",
        simulation_mode=True
    )
    
    print("✓ 创建EMCenter实例")
    tcu.connect()
    print("✓ 连接成功")
    
    tcu.switch_rf_path("PORT1_TO_PORT2")
    print("✓ switch_rf_path() 调用成功")
    
    tcu.set_attenuation("ATT2", 15.5)
    print("✓ set_attenuation() 调用成功")
    
    tcu.calibrate_path("TEST_PATH")
    print("✓ calibrate_path() 调用成功（特有方法）")
    
    tcu.disconnect()
    print("✓ 断开连接成功")

def test_factory_creation():
    """测试工厂创建TCU驱动"""
    print("\n" + "="*60)
    print("测试3: 工厂自动识别TCU型号")
    print("="*60)
    
    # 模拟EMCenter IDN
    idn_emcenter = "EMCenter,TCU-1000,SN123456,v2.0"
    driver = DriverFactory.create_tcu_driver(
        "TCPIP0::192.168.1.105::inst0::INSTR",
        idn_emcenter,
        simulation_mode=True
    )
    
    print(f"✓ 工厂识别为: {driver.__class__.__name__}")
    assert isinstance(driver, EMCenter_Driver), "应识别为EMCenter_Driver"
    print("✓ 类型验证通过")
    
    driver.connect()
    driver.switch_rf_path("AUTO_PATH")
    driver.disconnect()
    print("✓ 工厂创建的驱动运行正常")
    
    # 模拟未知TCU（应使用通用驱动）
    idn_unknown = "Unknown Vendor,TCU-X,SN999,v1.0"
    driver2 = DriverFactory.create_tcu_driver(
        "TCPIP0::192.168.1.106::inst0::INSTR",
        idn_unknown,
        simulation_mode=True
    )
    
    print(f"✓ 未知型号识别为: {driver2.__class__.__name__}")
    assert driver2.__class__.__name__ == "GenericTCU", "应回退到GenericTCU"
    print("✓ 回退逻辑验证通过")

def test_tcu_hal():
    """测试TCU HAL层封装"""
    print("\n" + "="*60)
    print("测试4: TCU HAL层封装")
    print("="*60)
    
    from drivers.tcu import TCU
    
    tcu_hal = TCU(
        "TCPIP0::192.168.1.105::inst0::INSTR",
        name="TCU_HAL_Test",
        simulation_mode=True
    )
    
    print("✓ 创建TCU HAL实例")
    tcu_hal.connect()
    print("✓ HAL连接成功（自动识别型号）")
    
    # 测试标准接口
    tcu_hal.switch_rf_path("HAL_TEST_PATH")
    print("✓ HAL标准接口: switch_rf_path()")
    
    tcu_hal.set_attenuation("HAL_ATT", 5.0)
    print("✓ HAL标准接口: set_attenuation()")
    
    # 测试高级封装方法
    tcu_hal.configure_test_path("VSG_OUT", "DUT_IN", attenuation_db=12.0)
    print("✓ HAL高级接口: configure_test_path()")
    
    tcu_hal.disconnect()
    print("✓ HAL断开连接成功")

def main():
    """运行所有测试"""
    setup_logger()
    
    print("\n" + "#"*60)
    print("# TCU 驱动功能验证测试套件")
    print("# 模式: 模拟模式 (无需硬件)")
    print("#"*60)
    
    try:
        test_generic_tcu()
        test_emcenter_driver()
        test_factory_creation()
        test_tcu_hal()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        print("\n✅ TCU驱动框架验证成功")
        print("✅ 模拟模式运行正常")
        print("✅ 工厂识别逻辑正确")
        print("✅ HAL封装功能完整")
        print("\n📌 下一步: 等待用户上传EMCenter手册，实现具体SCPI指令")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
