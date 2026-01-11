from drivers.base_instrument import BaseInstrument

class GenericVSG(BaseInstrument):
    """
    通用矢量信号发生器驱动 (Generic SCPI VSG Driver).
    实现大多数信号源遵循的标准 SCPI 指令。
    """

    def __init__(self, resource_name: str, name: str = "Generic_VSG", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def set_frequency(self, frequency_hz: float):
        """
        设置射频频率 (Standard SCPI: FREQ).
        """
        self.write(f"FREQ {frequency_hz}")
        self.logger.info(f"设置频率: {frequency_hz} Hz")

    def set_power(self, power_dbm: float):
        """
        设置射频功率 (Standard SCPI: POW).
        """
        self.write(f"POW {power_dbm}")
        self.logger.info(f"设置功率: {power_dbm} dBm")

    def enable_output(self, enable: bool):
        """
        开关射频输出 (Standard SCPI: OUTP).
        """
        state = "ON" if enable else "OFF"
        self.write(f"OUTP {state}")
        self.logger.info(f"射频输出: {state}")

    def load_waveform(self, waveform_name: str):
        """
        加载波形文件。
        由于各厂商路径格式差异极大，通用驱动仅提供最基础的实现或抛出警告。
        """
        # 尝试使用 Keysight 风格的通用加载指令，但不保证成功
        self.logger.warning("正在使用通用 SCPI 指令加载波形，可能不适用于所有设备。建议使用专用驱动。")
        self.write(f"SOUR:RAD:ARB:LOAD '{waveform_name}'")
