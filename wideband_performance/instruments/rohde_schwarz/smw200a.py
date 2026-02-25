from drivers.common.generic_vsg import GenericVSG


class SMW200A_Driver(GenericVSG):
    """
    Rohde & Schwarz SMW200A 专用驱动。
    继承自 GenericVSG，重写了部分差异化指令。
    """

    def __init__(self, resource_name: str, name: str = "RS_SMW200A", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def load_waveform(self, waveform_name: str):
        """
        [重写] 加载波形文件，适配 R&S 文件系统路径。
        """
        # R&S SMW200A 需要先选择波形文件到 ARB 生成器
        # 假设文件位于默认的用户目录 /var/user/
        base_path = "/var/user/"
        if not waveform_name.startswith("/"):
             full_path = f"{base_path}{waveform_name}"
        else:
             full_path = waveform_name

        if not full_path.endswith(".wv"):
            full_path += ".wv"

        self.logger.info(f"SMW200A 加载波形: {full_path}")
        # 指令: SOURce:BB:ARBitrary:WAVeform:SELect <Path>
        self.write(f"SOUR:BB:ARB:WAV:SEL '{full_path}'")

        # 加载后通常需要自动打开 ARB 状态
        self.write("SOUR:BB:ARB:STAT ON")

    def set_rf_frequency(self, freq: float):
        """
        [扩展] R&S 习惯用语别名，底层仍调用父类标准指令。
        """
        self.set_frequency(freq)

    def get_errors(self):
        """
        [扩展] 读取系统错误队列。
        """
        return self.query("SYST:ERR?")
