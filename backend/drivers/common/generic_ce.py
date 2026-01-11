from drivers.base_instrument import BaseInstrument

class GenericChannelEmulator(BaseInstrument):
    """
    通用信道模拟器驱动 (Generic SCPI Channel Emulator).
    """

    def __init__(self, resource_name: str, name: str = "Generic_CE", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def load_channel_model(self, model_name: str):
        """
        加载信道模型文件。
        """
        self.logger.warning("通用驱动使用标准 MEM:LOAD 指令，可能不适用。")
        self.write(f"MEM:LOAD:MODEL '{model_name}'")

    def set_input_power(self, power_dbm: float):
        """
        设置输入端口的期望功率电平。
        """
        self.write(f"INP:POW {power_dbm}")
        self.logger.info(f"设置输入功率: {power_dbm} dBm")

    def set_output_power(self, power_dbm: float):
        """
        设置输出端口功率（或增益）。
        """
        self.write(f"OUTP:POW {power_dbm}")
        self.logger.info(f"设置输出功率: {power_dbm} dBm")

    def rf_on(self):
        self.write("OUTP:STAT ON")
        self.logger.info("RF 开启")

    def rf_off(self):
        self.write("OUTP:STAT OFF")
        self.logger.info("RF 关闭")
