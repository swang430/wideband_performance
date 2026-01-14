from drivers.base_instrument import BaseInstrument

class GenericChannelEmulator(BaseInstrument):
    """
    通用信道模拟器驱动 (Generic SCPI Channel Emulator).
    """

    def __init__(self, resource_name: str, name: str = "Generic_CE", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def set_velocity(self, velocity_kmh: float):
        """
        [标准接口] 设置移动速度 (km/h) 以模拟多普勒频移。
        """
        self.logger.warning("通用驱动未实现 set_velocity")

    def load_channel_model(self, model_name: str):
        """
        [标准接口] 加载信道模型文件。
        """
        self.logger.warning("通用驱动使用标准 MEM:LOAD 指令，可能不适用。")
        self.write(f"MEM:LOAD:MODEL '{model_name}'")

    def set_input_power(self, power_dbm: float):
        """
        [标准接口] 设置输入端口期望功率电平。
        """
        self.write(f"INP:POW {power_dbm}")
        self.logger.info(f"设置输入功率: {power_dbm} dBm")

    def set_output_power(self, power_dbm: float):
        """
        [标准接口] 设置输出端口功率（或增益）。
        """
        self.write(f"OUTP:POW {power_dbm}")
        self.logger.info(f"设置输出功率: {power_dbm} dBm")

    def rf_on(self):
        """
        [标准接口] 全局开启射频仿真。
        """
        self.write("OUTP:STAT ON")
        self.logger.info("RF 开启")

    def rf_off(self):
        """
        [标准接口] 全局关闭射频仿真。
        """
        self.write("OUTP:STAT OFF")
        self.logger.info("RF 关闭")
