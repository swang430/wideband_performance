"""
Cellular (LTE/5G) Fading Channel Throughput Test Wrapper.
组合 CMW500 (小区建立与吞吐量统计), SMW200A (AWGN / 邻频干扰), Vertex (衰落信道).
"""

import time
import logging
from typing import Dict, Any

from unicon.instruments.rohde_schwarz.cmw500 import CMW500
from unicon.instruments.rohde_schwarz.smw200a import SMW200A
from unicon.instruments.spirent.vertex import Vertex

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("CellularFadingTest")

def run_fading_throughput_test(
    cmw: CMW500,
    smw: SMW200A,
    vertex: Vertex,
    band: str = "OB1",
    dl_channel: int = 300,
    tx_power_dbm: float = -40.0,
    fading_model: str = "TDL-C",
    snr_db: float = 10.0,
    test_duration_s: int = 10
) -> Dict[str, Any]:
    """
    执行一次包含衰落和噪声注入的蜂窝网吞吐量打点测试。
    """
    results = {
        "status": "Running",
        "throughput_mbps": 0.0,
        "fading_model": fading_model,
        "snr_db": snr_db
    }

    try:
        # 1. 仪器初始化配置
        logger.info(">>> 1. 配置测试仪器 <<<")
        
        # 配置 CMW500 (LTE 小区)
        cmw.lte.set_routing(scenario="STANdard", rf_in="RF1C", rf_out="RF1C")
        cmw.lte.configure_rf(band=band, dl_channel=dl_channel, tx_power_dbm=tx_power_dbm)
        cmw.lte.configure_network(bandwidth="B100")
        cmw.lte.start_signaling()
        
        # 配置 Vertex 信道仿真器
        vertex.load_scenario("LTE_FADING_SCENARIO_1")
        vertex.set_channel_fading_model(link_id="1", model_name=fading_model)
        vertex.set_port_input_power(port_id=1, power_dbm=tx_power_dbm)
        
        # 配置 SMW200A (注入 AWGN)
        smw.set_awgn_snr(snr_db=snr_db, channel=1)
        smw.set_awgn_state(True, channel=1)
        smw.set_rf_output(True, channel=1)
        
        # 2. 等待终端附着
        logger.info(">>> 2. 等待终端附着网络 <<<")
        if not cmw.lte.wait_for_connection(timeout=20.0):
            logger.error("终端未能附着到小区网络。")
            results["status"] = "Fail: No Connection"
            return results
            
        # 3. 开启信道衰落并测试吞吐量
        logger.info(">>> 3. 开启衰落模型，开始测量吞吐量 <<<")
        vertex.start_emulation()
        
        # 稳态运行 duration
        time.sleep(test_duration_s)
        
        # 模拟抓取 CMW500 的吞吐量 (或者实际抓取)
        if cmw.simulation_mode:
            throughput = 85.5
        else:
            # 真实环境中将调用 cmw.lte.fetch_throughput()
            # 这是一个通用示例，真实命令需查阅 CMW500 LTE 手册
            raw_res = cmw.query("FETCh:LTE:SIGNaling:THRoughput:DL?")
            throughput = float(raw_res.split(',')[1]) if ',' in raw_res else 0.0
            
        results["throughput_mbps"] = throughput
        logger.info(f"平均吞吐量: {throughput} Mbps")
        
        results["status"] = "Success"

    except Exception as e:
        logger.error(f"衰落测试发生异常: {e}")
        results["status"] = f"Error: {e}"
    finally:
        # 清理
        try:
            vertex.stop_emulation()
            smw.set_rf_output(False, channel=1)
        except:
            pass

    return results

if __name__ == "__main__":
    logger.info("启动 UniCon LTE 衰落测试自动化联调 (Simulation Mode)...")
    
    # 实例化仪器并连接
    tester = CMW500(resource_name="TCPIP::192.168.1.100::INSTR", simulation_mode=True)
    interferer = SMW200A(resource_name="TCPIP::192.168.1.101::INSTR", simulation_mode=True)
    channel_em = Vertex(resource_name="TCPIP::192.168.1.102::INSTR", simulation_mode=True)
    
    tester.connect()
    interferer.connect()
    channel_em.connect()
    
    try:
        report = run_fading_throughput_test(tester, interferer, channel_em, snr_db=15.0, test_duration_s=2)
        logger.info(f"最终状态: {report['status']}, 吞吐量: {report['throughput_mbps']} Mbps")
    finally:
        tester.disconnect()
        interferer.disconnect()
        channel_em.disconnect()
