from drivers.base_instrument import BaseInstrument


class GenericVNA(BaseInstrument):
    """
    通用矢量网络分析仪驱动。
    """

    def __init__(self, resource_name: str, name: str = "Generic_VNA", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def set_frequency_sweep(self, start_freq: float, stop_freq: float, points: int):
        """[标准接口] 配置频率扫描"""
        self.write(f"SENSE:FREQ:START {start_freq}")
        self.write(f"SENSE:FREQ:STOP {stop_freq}")
        self.write(f"SENSE:SWEEP:POINTS {points}")
        self.logger.info(f"设置扫描: {start_freq}-{stop_freq} Hz, {points} pts")

    def set_power(self, power_dbm: float):
        """[标准接口] 设置源功率"""
        self.write(f"SOUR:POW {power_dbm}")
        self.logger.info(f"设置功率: {power_dbm} dBm")

    def preset(self):
        """[标准接口] 复位仪器状态"""
        self.write("SYST:PRESET")

    def measure_s_parameter(self, parameter: str = "S21") -> str:
        """[标准接口] 测量 S 参数并返回数据"""
        self.logger.warning("通用驱动仅触发扫描，不保证数据格式正确。")
        self.write("INIT:IMM; *WAI")
        return self.query("CALC:DATA? FDATA")
