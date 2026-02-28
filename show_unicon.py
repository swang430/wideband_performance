import time
import logging
from unicon.instruments.rohde_schwarz.cmw500 import CMW500
from unicon.instruments.spirent.vertex import Vertex
from unicon.instruments.keysight.mxg import KeysightMXG

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

def demonstrate_unicon():
    print("\n" + "="*50)
    print("🚀 UniCon (Universal Control) HAL 核心能力展示")
    print("="*50)
    
    # 1. 实例化仪表 (开启模拟模式)
    print("\n[1] 实例化仪表底层驱动并连接...")
    tester = CMW500("TCPIP0::192.168.1.100::INSTR", simulation_mode=True)
    fader = Vertex("TCPIP0::192.168.1.101::INSTR", simulation_mode=True)
    vsg = KeysightMXG("TCPIP0::192.168.1.102::INSTR", simulation_mode=True)
    
    tester.connect()
    fader.connect()
    vsg.connect()
    
    print("\n[2] 演示 CMW500 高阶 LTE 控制 (深度扩展)...")
    # 一行代码配置 LTE 频段、信道和 MIMO 模式
    tester.lte.configure_rf(band="OB1", dl_channel=300, tx_power_dbm=-40)
    tester.lte.configure_network(bandwidth="B100", cell_id=1, mimo_mode="TXM4")
    # 一行代码指定物理资源块 (RB) 分配
    tester.lte.configure_resource_blocks(num_rb=50, start_rb=0, link_dir="DL")
    tester.lte.start_signaling()
    
    print("\n[3] 演示 Spirent Vertex 信道仿真器控制...")
    fader.load_scenario("5G_MIMO_SCENARIO")
    fader.set_channel_fading_model(link_id="1", model_name="TDL-C")
    fader.start_emulation()
    
    print("\n[4] 演示 Keysight MXG 信号源干扰注入...")
    vsg.set_frequency(3500e6)
    vsg.set_power(-30)
    vsg.set_rf_output(True)
    
    print("\n[5] 演示硬件级错误队列轮询 (健壮性)...")
    errors = tester.check_system_errors()
    print(f"CMW500 系统报错队列: {errors}")
    
    print("\n[6] 测试结束，安全断开所有资源...")
    tester.disconnect()
    fader.disconnect()
    vsg.disconnect()
    
    print("\n✅ 展示完成！UniCon 提供了一套极其纯粹、强类型且内置防呆机制的 Python API。")

if __name__ == "__main__":
    demonstrate_unicon()
