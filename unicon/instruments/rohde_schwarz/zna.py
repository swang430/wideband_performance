"""
Rohde & Schwarz ZNA Vector Network Analyzer Driver.

Ref: ZNA Vector Network Analyzer User Manual
"""

from typing import List

from unicon.instruments.base_instrument import BaseInstrument


class ZNA(BaseInstrument):
    """
    Rohde & Schwarz ZNA 矢量网络分析仪驱动。
    """

    def __init__(self, resource_name: str, name: str = "RS_ZNA", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)

    def set_sweep_points(self, points: int, channel: int = 1):
        """
        设置扫描点数。
        Ref: ZNA User Manual - [SENSe<Ch>:]SWEep:POINts
        """
        self.logger.info(f"设置通道 {channel} 扫描点数: {points}")
        self.write(f"SENSe{channel}:SWEep:POINts {points}")

    def set_frequency_range(self, start_hz: float, stop_hz: float, channel: int = 1):
        """
        设置起始和终止频率。
        Ref: ZNA User Manual - [SENSe<Ch>:]FREQuency:STARt / STOP
        """
        self.logger.info(f"设置通道 {channel} 频率范围: {start_hz} Hz - {stop_hz} Hz")
        self.write(f"SENSe{channel}:FREQuency:STARt {start_hz}")
        self.write(f"SENSe{channel}:FREQuency:STOP {stop_hz}")

    def measure_s_parameter(self, parameter: str = "S21", channel: int = 1) -> List[float]:
        """
        完整配置 Trace 并测量 S 参数。
        Ref: ZNA User Manual - CALCulate<Ch>:PARameter:DEFine / CALCulate<Ch>:DATA?
        """
        self.logger.info(f"测量通道 {channel} 的 {parameter} 参数...")
        if self.simulation_mode:
            return [-10.5, -11.0, -10.8] * 10

        trace_name = f"Trc_{parameter}"
        # 定义 Trace
        self.write(f"CALCulate{channel}:PARameter:DEFine '{trace_name}', '{parameter}'")
        # 显示 Trace
        self.write(f"DISPlay:WINDow1:TRACe1:FEED '{trace_name}'")

        # 触发并等待完成
        self.write(f"INITiate{channel}:IMMediate; *WAI")

        # 读取格式化数据 (以 dB Magnitude 形式)
        self.write(f"CALCulate{channel}:FORMat MLOGarithmic")
        res = self.query(f"CALCulate{channel}:DATA? FDATa")
        
        try:
            raw_data = [float(x) for x in res.split(",")]
            return raw_data
        except Exception as e:
            self.logger.error(f"解析 ZNA 数据失败: {e} (Raw: {res[:50]}...)")
            return []
