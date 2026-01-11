from drivers.base_instrument import BaseInstrument

class GenericSA(BaseInstrument):
    """
    通用频谱分析仪驱动 (Generic SCPI Spectrum Analyzer).
    """

    def __init__(self, resource_name: str, name: str = "Generic_SA", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def set_center_frequency(self, frequency_hz: float):
        self.write(f"FREQ:CENT {frequency_hz}")
        self.logger.info(f"设置中心频率: {frequency_hz} Hz")

    def set_span(self, span_hz: float):
        self.write(f"FREQ:SPAN {span_hz}")
        self.logger.info(f"设置跨度: {span_hz} Hz")

    def set_reference_level(self, level_dbm: float):
        self.write(f"DISP:WIND:TRAC:Y:RLEV {level_dbm}")
        self.logger.info(f"设置参考电平: {level_dbm} dBm")

    def set_resolution_bandwidth(self, rbw_hz: float):
        self.write(f"BAND {rbw_hz}")
        self.logger.info(f"设置 RBW: {rbw_hz} Hz")

    def get_peak_amplitude(self) -> float:
        """
        执行峰值搜索并返回幅度 (Standard SCPI).
        """
        self.write("CALC:MARK1:MAX") 
        val = self.query("CALC:MARK1:Y?")
        try:
            return float(val)
        except ValueError:
            self.logger.error(f"无法解析峰值: {val}")
            return -999.0

    def get_trace_data(self) -> list:
        """
        获取迹线数据 (默认返回空，需子类实现).
        """
        self.logger.warning("通用驱动不支持读取 Trace 数据。")
        return []
