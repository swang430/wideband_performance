"""
Anritsu MT8000A Radio Communication Test Station Driver.

Ref: MT8000A Operation Manual
"""

import time
from typing import Dict, Any

from unicon.instruments.base_instrument import BaseInstrument


class MT8000A(BaseInstrument):
    """
    Anritsu MT8000A 5G 通信综合测试仪驱动。
    """

    def __init__(self, resource_name: str, name: str = "MT8000A", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)

    def set_rf_frequency(self, freq_hz: float, band: str = "n78"):
        """
        设置 5G NR 射频中心频率。
        Ref: MT8000A SCPI Reference - [SOURce:]FREQuency:CENTer
        """
        self.logger.info(f"设置 5G NR 频率: {freq_hz} Hz, 频段: {band}")
        # Anritsu 指令通常针对特定的系统模块 (例如 SYSTem:NR5G)
        self.write(f"CONFigure:NR5G:BAND {band}")
        self.write(f"CONFigure:NR5G:FREQuency:CENTer {freq_hz}")

    def set_output_power(self, power_dbm: float):
        """
        设置下行发射功率。
        Ref: MT8000A SCPI Reference - CONFigure:NR5G:DL:POWer
        """
        self.logger.info(f"设置 5G NR 下行功率: {power_dbm} dBm")
        self.write(f"CONFigure:NR5G:DL:POWer {power_dbm}")

    def start_call(self) -> bool:
        """
        启动信令连接 (Start Call)。
        Ref: MT8000A SCPI Reference - CALL:NR5G:SIGNaling:STARt
        """
        self.logger.info("启动 MT8000A 5G 信令连接...")
        self.write("CALL:NR5G:SIGNaling:STARt")
        
        timeout = 20
        start_time = time.time()
        while time.time() - start_time < timeout:
            state = self.query("CALL:NR5G:SIGNaling:STATe?")
            if "CONN" in state.upper() or "IDLE" not in state.upper():
                self.logger.info("5G 信令状态就绪。")
                return True
            time.sleep(1.0)
            
        self.logger.error("启动信令超时！")
        return False

    def fetch_throughput(self) -> Dict[str, float]:
        """
        获取当前 IP 层的吞吐量统计。
        Ref: MT8000A SCPI Reference - FETCh:NR5G:THRoughput:IP?
        """
        self.logger.info("读取 5G NR 吞吐量统计...")
        if self.simulation_mode:
            return {"dl_mbps": 850.5, "ul_mbps": 120.2}

        res = self.query("FETCh:NR5G:THRoughput:IP?")
        try:
            parts = res.split(",")
            return {
                "dl_mbps": float(parts[0]) / 1e6 if len(parts) > 0 else 0.0,
                "ul_mbps": float(parts[1]) / 1e6 if len(parts) > 1 else 0.0
            }
        except Exception as e:
            self.logger.error(f"解析 MT8000A 吞吐量数据失败: {e} (Raw: {res})")
            return {}
