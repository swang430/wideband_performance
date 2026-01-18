#!/usr/bin/env python3
"""
EMCenter HAL层快速验证测试

测试所有EMCenter模块的HAL封装是否正常工作。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drivers.power_meter import PowerMeter
from drivers.signal_generator import SignalGenerator
from drivers.field_probe import FieldProbe
from drivers.positioner import Positioner

def test_power_meter():
    """测试功率计HAL"""
    print("\n" + "="*60)
    print("测试1: 功率计HAL (PowerMeter)")
    print("="*60)
    
    pm = PowerMeter(
        "TCPIP0::192.168.1.105::inst0::INSTR",
        name="TestPowerMeter",
        simulation_mode=True,
        slot=2,
        port="A"
    )
    
    print("✓ 创建功率计实例")
    pm.connect()
    print("✓ 连接成功")
    
    # 基本功能测试
    pm.set_frequency(2400e6)
    print("✓ set_frequency() 调用成功")
    
    power = pm.read_power()
    print(f"✓ read_power() 返回: {power:.2f} dBm")
    
    powers = pm.read_power_burst(5)
    print(f"✓ read_power_burst(5) 返回: {len(powers)} 个值")
    
    # 高级功能测试
    pm.configure(freq_hz=1000e6, offset_db=10.0, filter_mode=5)
    print("✓ configure() 高级配置成功")
    
    avg = pm.measure_average(count=10)
    print(f"✓ measure_average() 返回: {avg:.2f} dBm")
    
    pm.disconnect()
    print("✓ 断开连接成功")


def test_signal_generator():
    """测试信号发生器HAL"""
    print("\n" + "="*60)
    print("测试2: 信号发生器HAL (SignalGenerator)")
    print("="*60)
    
    gen = SignalGenerator(
        "TCPIP0::192.168.1.105::inst0::INSTR",
        name="TestSigGen",
        simulation_mode=True,
        slot=3
    )
    
    print("✓ 创建信号源实例")
    gen.connect()
    print("✓ 连接成功")
    
    # 基本功能测试
    gen.set_frequency(1000e6)
    gen.set_power(-10.0)
    print("✓ set_frequency/power() 调用成功")
    
    gen.enable_output(True)
    state = gen.get_output_state()
    print(f"✓ enable_output() 返回状态: {state}")
    
    # 调制功能测试
    gen.configure_am(True, depth_percent=50.0, freq_hz=1000.0)
    print("✓ configure_am() AM调制配置成功")
    
    gen.configure_fm(True, deviation_hz=10000.0, freq_hz=1000.0)
    print("✓ configure_fm() FM调制配置成功")
    
    gen.configure_pulse(True, width_us=10.0, prf_hz=1000.0)
    print("✓ configure_pulse() 脉冲调制配置成功")
    
    # 高级功能测试
    gen.configure_cw(freq_hz=2400e6, power_dbm=-5.0, output_on=True)
    print("✓ configure_cw() CW配置成功")
    
    gen.configure_modulated_carrier(
        freq_hz=1000e6,
        power_dbm=0.0,
        mod_type="AM",
        mod_params={'depth': 80.0, 'freq': 5000.0}
    )
    print("✓ configure_modulated_carrier() 调制载波配置成功")
    
    gen.disconnect()
    print("✓ 断开连接成功")


def test_field_probe():
    """测试电场探头HAL"""
    print("\n" + "="*60)
    print("测试3: 电场探头HAL (FieldProbe)")
    print("="*60)
    
    probe = FieldProbe(
        "TCPIP0::192.168.1.105::inst0::INSTR",
        name="TestFieldProbe",
        simulation_mode=True,
        slot=1
    )
    
    print("✓ 创建电场探头实例")
    probe.connect()
    print("✓ 连接成功")
    
    # 基本功能测试
    field = probe.read_field()
    print(f"✓ read_field() 返回: {field:.2f} V/m")
    
    probe.set_mode("peak")
    print("✓ set_mode('peak') 调用成功")
    
    probe.reset_peak()
    print("✓ reset_peak() 调用成功")
    
    status = probe.get_laser_status()
    print(f"✓ get_laser_status() 返回: {status}")
    
    # 高级功能测试
    probe.set_mode("normal")  # 先切换回正常模式
    peak = probe.measure_peak_field(duration_sec=1.0)
    print(f"✓ measure_peak_field() 返回: {peak:.2f} V/m")
    
    avg = probe.measure_average_field(count=20, interval_ms=50)
    print(f"✓ measure_average_field() 返回: {avg:.2f} V/m")
    
    compliant = probe.check_compliance(limit_vm=50.0)
    print(f"✓ check_compliance() 返回: {compliant}")
    
    probe.disconnect()
    print("✓ 断开连接成功")


def test_positioner():
    """测试定位器HAL"""
    print("\n" + "="*60)
    print("测试4: 定位器HAL (Positioner)")
    print("="*60)
    
    pos = Positioner(
        "TCPIP0::192.168.1.105::inst0::INSTR",
        name="TestPositioner",
        simulation_mode=True,
        slot=5
    )
    
    print("✓ 创建定位器实例")
    pos.connect()
    print("✓ 连接成功")
    
    # 基本功能测试
    pos.move_to(90.0, wait=False)  # 模拟模式不需要等待
    print("✓ move_to(90.0) 调用成功")
    
    current = pos.get_position()
    print(f"✓ get_position() 返回: {current}°")
    
    pos.move_relative(45.0, wait=False)
    print("✓ move_relative(45.0) 调用成功")
    
    pos.set_speed(15.0)
    speed = pos.get_speed()
    print(f"✓ set_speed/get_speed() 返回: {speed}")
    
    is_moving = pos.is_moving()
    print(f"✓ is_moving() 返回: {is_moving}")
    
    # 高级功能测试
    pos.configure_motion(speed=10.0, accel=5.0)
    print("✓ configure_motion() 配置成功")
    
    # 扫描测试（使用小范围）
    positions = pos.scan_range(0.0, 90.0, 30.0, wait_at_each=0.1)
    print(f"✓ scan_range() 返回: {len(positions)} 个位置")
    
    # 天线方向图扫描测试
    def mock_measure(angle):
        import random
        return -50.0 + random.uniform(-10, 10)
    
    pattern = pos.scan_antenna_pattern(
        start_deg=0.0,
        end_deg=180.0,
        step_deg=45.0,
        measure_callback=mock_measure
    )
    print(f"✓ scan_antenna_pattern() 返回: {len(pattern)} 个数据点")
    
    pos.home(0.0)
    print("✓ home() 回归初始位置成功")
    
    pos.disconnect()
    print("✓ 断开连接成功")


def main():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# EMCenter HAL层功能验证测试套件")
    print("# 模式: 模拟模式 (无需硬件)")
    print("#"*60)
    
    try:
        test_power_meter()
        test_signal_generator()
        test_field_probe()
        test_positioner()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        print("\n✅ EMCenter HAL层验证成功")
        print("✅ 功率计HAL正常")
        print("✅ 信号发生器HAL正常")
        print("✅ 电场探头HAL正常")
        print("✅ 定位器HAL正常")
        print("\n📌 下一步: 配置config.yaml并进行实机测试")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
