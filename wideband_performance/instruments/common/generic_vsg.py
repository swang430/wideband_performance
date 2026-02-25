from drivers.base_instrument import BaseInstrument


class GenericVSG(BaseInstrument):
    """
    通用矢量信号发生器驱动 (Generic SCPI VSG Driver).
    实现大多数信号源遵循的标准 SCPI 指令。
    """

    def __init__(self, resource_name: str, name: str = "Generic_VSG", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def set_frequency(self, hz: float):
        """
        [标准接口] 设置射频频率 (Standard SCPI: FREQ).
        """
        self.write(f"FREQ {hz}")
        self.logger.info(f"设置频率: {hz} Hz")

    def set_power(self, dbm: float):
        """
        [标准接口] 设置射频功率 (Standard SCPI: POW).
        """
        self.write(f"POW {dbm}")
        self.logger.info(f"设置功率: {dbm} dBm")

    def enable_output(self, enable: bool):
        """
        [标准接口] 开关射频输出 (Standard SCPI: OUTP).
        """
        state = "ON" if enable else "OFF"
        self.write(f"OUTP {state}")
        self.logger.info(f"射频输出: {state}")

    def load_waveform(self, waveform_name: str):
        """
        [标准接口] 加载波形文件。
        """
        self.logger.warning("通用驱动使用 Keysight 风格 ARB 指令，可能不适用。")
        self.write(f"SOUR:RAD:ARB:LOAD '{waveform_name}'")
