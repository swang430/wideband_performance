"""
Keysight X-Series Signal Analyzer Driver (e.g., N9020B, N9030B).

Ref: X-Series Signal Analyzer User and Programmer Reference IQ Analyzer Mode_9018-04533.pdf
"""

from typing import Tuple

from unicon.instruments.base_instrument import BaseInstrument


class KeysightVSA(BaseInstrument):
    """
    Keysight X-Series 频谱分析仪/信号分析仪驱动。
    """

    def __init__(self, resource_name: str, name: str = "Keysight_VSA", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)

    def set_frequency_center(self, freq_hz: float):
        """
        设置中心频率 (Hz)。
        Ref: X-Series Programmer Reference - [:SENSe]:FREQuency:CENTer
        """
        self.logger.info(f"设置中心频率: {freq_hz} Hz")
        self.write(f":FREQuency:CENTer {freq_hz}")

    def set_span(self, span_hz: float):
        """
        设置扫频宽度 (Hz)。
        Ref: X-Series Programmer Reference - [:SENSe]:FREQuency:SPAN
        """
        self.logger.info(f"设置 Span: {span_hz} Hz")
        self.write(f":FREQuency:SPAN {span_hz}")

    def set_reference_level(self, level_dbm: float):
        """
        设置参考电平 (Reference Level)。
        Ref: X-Series Programmer Reference - :DISPlay:WINDow[1]:TRACe:Y[:SCALe]:RLEVel
        """
        self.logger.info(f"设置参考电平: {level_dbm} dBm")
        self.write(f":DISPlay:WINDow1:TRACe:Y:RLEVel {level_dbm}")

    def set_resolution_bandwidth(self, rbw_hz: float, auto: bool = False):
        """
        设置分辨带宽 (RBW)。
        Ref: X-Series Programmer Reference - [:SENSe]:BWIDth[:RESolution]
        """
        if auto:
            self.logger.info("设置 RBW 为 Auto")
            self.write(":BWIDth:RESolution:AUTO ON")
        else:
            self.logger.info(f"设置 RBW: {rbw_hz} Hz")
            self.write(f":BWIDth:RESolution {rbw_hz}")

    def run_single_sweep(self):
        """
        执行单次扫描并等待。
        Ref: X-Series Programmer Reference - :INITiate:IMMediate
        """
        self.logger.info("执行单次扫描...")
        self.write(":INITiate:CONTinuous OFF")
        self.write(":INITiate:IMMediate; *WAI")

    def perform_peak_search(self, marker: int = 1) -> Tuple[float, float]:
        """
        执行 Peak Search 并读取频率和幅度。
        Ref: X-Series Programmer Reference - :CALCulate:MARKer[1]:MAXimum
        """
        if self.simulation_mode:
            return (2.4e9, -15.2)

        self.logger.info(f"执行 Peak Search (Marker {marker})...")
        self.write(f":CALCulate:MARKer{marker}:MAXimum")
        
        x_val = float(self.query(f":CALCulate:MARKer{marker}:X?"))
        y_val = float(self.query(f":CALCulate:MARKer{marker}:Y?"))
        
        return (x_val, y_val)
