from drivers.base_instrument import BaseInstrument


class GenericSA(BaseInstrument):
    """
    通用频谱分析仪驱动 (Generic SCPI Spectrum Analyzer).
    """

    def __init__(self, resource_name: str, name: str = "Generic_SA", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def set_center_frequency(self, frequency_hz: float):
        """[标准接口] 设置中心频率"""
        self.write(f"FREQ:CENT {frequency_hz}")
        self.logger.info(f"设置中心频率: {frequency_hz} Hz")

    def set_span(self, span_hz: float):
        """[标准接口] 设置频率跨度"""
        self.write(f"FREQ:SPAN {span_hz}")
        self.logger.info(f"设置跨度: {span_hz} Hz")

    def set_reference_level(self, level_dbm: float):
        """[标准接口] 设置参考电平"""
        self.write(f"DISP:WIND:TRAC:Y:RLEV {level_dbm}")
        self.logger.info(f"设置参考电平: {level_dbm} dBm")

    def set_resolution_bandwidth(self, rbw_hz: float):
        """[标准接口] 设置分辨率带宽"""
        self.write(f"BAND {rbw_hz}")
        self.logger.info(f"设置 RBW: {rbw_hz} Hz")

    def get_peak_amplitude(self) -> float:
        """[标准接口] 执行峰值搜索并返回幅度"""
        self.write("CALC:MARK1:MAX")
        val = self.query("CALC:MARK1:Y?")
        try:
            return float(val)
        except ValueError:
            self.logger.error(f"无法解析峰值: {val}")
            return -999.0

    def get_trace_data(self) -> list:
        """[标准接口] 获取 Trace 1 数据"""
        self.logger.warning("通用驱动不支持读取 Trace 数据，请使用专用驱动。")
        return []
