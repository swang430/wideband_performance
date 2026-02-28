"""
Keysight PNA Series Microwave Network Analyzer Driver.

Ref: PNA Series Network Analyzer Help (PDF)
"""

from typing import List

from unicon.instruments.base_instrument import BaseInstrument


class PNA(BaseInstrument):
    """
    Keysight PNA (N5224A/N5245B 等) 微波网络分析仪驱动。
    """

    def __init__(self, resource_name: str, name: str = "PNA", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)

    def set_sweep_points(self, points: int, channel: int = 1):
        """
        设置扫描点数。
        Ref: PNA Programmer's Guide - SENS:SWE:POIN
        """
        self.logger.info(f"设置通道 {channel} 扫描点数: {points}")
        self.write(f"SENSe{channel}:SWEep:POINts {points}")

    def set_frequency_range(self, start_hz: float, stop_hz: float, channel: int = 1):
        """
        设置起始和终止频率。
        Ref: PNA Programmer's Guide - SENS:FREQ:STAR / STOP
        """
        self.logger.info(f"设置通道 {channel} 频率范围: {start_hz} Hz - {stop_hz} Hz")
        self.write(f"SENSe{channel}:FREQuency:STARt {start_hz}")
        self.write(f"SENSe{channel}:FREQuency:STOP {stop_hz}")

    def set_s_parameter(self, measurement_name: str = "CH1_S21_1", parameter: str = "S21", channel: int = 1):
        """
        定义 Trace 测量的 S 参数类型。
        Ref: PNA Programmer's Guide - CALC:PAR:DEF:EXT
        """
        self.logger.info(f"在通道 {channel} 定义测量 {measurement_name} 为 {parameter}")
        self.write(f"CALCulate{channel}:PARameter:DEFine:EXT '{measurement_name}', {parameter}")
        # 显示在 Window 1
        self.write(f"DISPlay:WINDow1:TRACe1:FEED '{measurement_name}'")

    def run_single_sweep(self, channel: int = 1):
        """
        执行单次扫描并等待。
        Ref: PNA Programmer's Guide - INIT:IMM
        """
        self.logger.info(f"通道 {channel} 执行单次扫描...")
        self.write(f"INITiate{channel}:CONTinuous OFF")
        self.write(f"INITiate{channel}:IMMediate; *OPC?")
        self.query("*OPC?") # 确保执行完毕

    def fetch_formatted_data(self, measurement_name: str = "CH1_S21_1", channel: int = 1) -> List[float]:
        """
        获取指定测量的格式化数据数组 (FDATa)。
        Ref: PNA Programmer's Guide - CALC:DATA? FDATA
        """
        self.logger.info(f"读取测量 {measurement_name} 的格式化数据...")
        if self.simulation_mode:
            return [-10.0, -10.5, -11.0, -10.8] * 10

        self.write(f"CALCulate{channel}:PARameter:SELect '{measurement_name}'")
        res = self.query(f"CALCulate{channel}:DATA? FDATA")
        try:
            raw_data = [float(x) for x in res.split(",")]
            return raw_data
        except Exception as e:
            self.logger.error(f"解析 PNA 数据失败: {e} (Raw: {res[:50]}...)")
            return []
