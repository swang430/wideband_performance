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
        if self.simulation_mode:
            return
        # ⚠️ 真实 SCPI 命令需要以 MT8000A 的官方 SCPI/Remote Control 手册为准。
        # 目前手册库仅包含概览手册，避免凭空猜测指令。
        raise NotImplementedError("MT8000A SCPI reference manual not available in manual library yet. Please provide SCPI/remote control guide.")

    def set_output_power(self, power_dbm: float):
        """
        设置下行发射功率。
        Ref: MT8000A SCPI Reference - CONFigure:NR5G:DL:POWer
        """
        self.logger.info(f"设置 5G NR 下行功率: {power_dbm} dBm")
        if self.simulation_mode:
            return
        raise NotImplementedError("MT8000A SCPI reference manual not available in manual library yet. Please provide SCPI/remote control guide.")

    def start_call(self) -> bool:
        """
        启动信令连接 (Start Call)。
        Ref: MT8000A SCPI Reference - CALL:NR5G:SIGNaling:STARt
        """
        self.logger.info("启动 MT8000A 5G 信令连接...")
        if self.simulation_mode:
            return True
        raise NotImplementedError("MT8000A SCPI reference manual not available in manual library yet. Please provide SCPI/remote control guide.")

    def fetch_throughput(self) -> Dict[str, float]:
        """
        获取当前 IP 层的吞吐量统计。
        Ref: MT8000A SCPI Reference - FETCh:NR5G:THRoughput:IP?
        """
        self.logger.info("读取 5G NR 吞吐量统计...")
        if self.simulation_mode:
            return {"dl_mbps": 850.5, "ul_mbps": 120.2}

        raise NotImplementedError("MT8000A SCPI reference manual not available in manual library yet. Please provide SCPI/remote control guide.")
