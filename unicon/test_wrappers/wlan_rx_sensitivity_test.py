"""
WLAN RX Sensitivity Automated Test Wrapper.
组合 CMW500 进行下行功率扫描，寻找 PER 达到特定阈值 (例如 10%) 的灵敏度点。
"""

import time
import logging
from typing import Dict, Any

from unicon.instruments.rohde_schwarz.cmw500 import CMW500

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("WlanSensitivityTest")

def run_wlan_rx_sensitivity_sweep(
    cmw: CMW500,
    start_power_dbm: float = -50.0,
    stop_power_dbm: float = -90.0,
    step_db: float = -2.0,
    packets_per_step: int = 1000,
    target_per_threshold: float = 10.0
) -> Dict[str, Any]:
    """
    执行一次完整的 WLAN 接收机灵敏度扫描测试。
    
    业务流程：
    1. 配置 CMW500 网络 (如果尚未配置)。
    2. 等待终端连接。
    3. 从 start_power 逐步递减到 stop_power。
    4. 每一个功率点打流 packets_per_step 个包。
    5. 读取 PER，如果超过 target_per_threshold，记录该点为灵敏度点并提前终止。
    """
    results = {
        "sweep_data": [],
        "sensitivity_dbm": None,
        "status": "Running"
    }

    try:
        # 1. 初始网络状态等待
        if not cmw.wlan.wait_for_connection(timeout=10.0):
            logger.error("在开始测试前，终端未能关联。")
            results["status"] = "Fail: No Connection"
            return results

        # 2. 配置固定发包参数
        cmw.wlan.configure_rx_test(num_packets=packets_per_step, payload_length_bytes=1000)

        # 3. 扫描主循环
        current_power = start_power_dbm
        while current_power >= stop_power_dbm:
            logger.info(f"--- 测试点: 功率 {current_power:.1f} dBm ---")
            
            # 设置 CMW500 发射功率
            cmw.wlan.configure_rf(tx_power_dbm=current_power)
            
            # 留出 0.5s 让硬件链路和 AGC 稳定
            time.sleep(0.5)

            # 启动下行发包
            cmw.wlan.start_rx_test()
            
            # 等待发包完成 (粗略估计时间)
            time.sleep(2.0)

            # 抓取结果
            per_data = cmw.wlan.fetch_per()
            per_val = per_data.get("per_percent", float('nan'))
            
            logger.info(f"测试结果 -> 功率: {current_power:.1f} dBm, PER: {per_val}%")
            
            results["sweep_data"].append({
                "power_dbm": current_power,
                "per_percent": per_val,
                "packets_sent": per_data.get("packets_sent", 0)
            })

            # 判断阈值
            if per_val >= target_per_threshold:
                logger.warning(f"达到或超过目标 PER 阈值 ({target_per_threshold}%)，当前功率为接收机灵敏度边缘。")
                results["sensitivity_dbm"] = current_power
                results["status"] = "Success"
                break
                
            current_power += step_db

        if results["sensitivity_dbm"] is None:
            logger.info("扫描完成，未达到 PER 阈值 (设备灵敏度极佳或线损未补偿)。")
            results["status"] = "Success (No Threshold Hit)"

    except Exception as e:
        logger.error(f"灵敏度测试过程中发生异常: {e}")
        results["status"] = f"Error: {e}"

    return results

if __name__ == "__main__":
    # 本地直接运行用于验证驱动和逻辑
    logger.info("启动 UniCon WLAN 灵敏度测试自动化打点 (Simulation Mode)...")
    
    # 实例化 CMW500，开启模拟模式
    tester = CMW500(resource_name="TCPIP::192.168.1.100::INSTR", simulation_mode=True)
    tester.connect()
    
    try:
        # 执行测试
        report = run_wlan_rx_sensitivity_sweep(tester, start_power_dbm=-60.0, stop_power_dbm=-80.0, step_db=-5.0)
        
        logger.info("\n========== 测试报告 ==========")
        logger.info(f"最终状态: {report['status']}")
        logger.info(f"灵敏度点 (10% PER): {report['sensitivity_dbm']} dBm")
        logger.info("详细数据:")
        for point in report["sweep_data"]:
            logger.info(f"  PWR: {point['power_dbm']} dBm -> PER: {point['per_percent']}%")
            
    finally:
        tester.disconnect()
