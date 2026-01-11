from drivers.common.generic_ce import GenericChannelEmulator

class PROPSIM_Driver(GenericChannelEmulator):
    """
    Keysight (Anite) PROPSIM F64 信道模拟器驱动。
    已根据 Propsim User Reference (ATE 章节) 验证。
    """
    
    def __init__(self, resource_name: str, name: str = "Keysight_PROPSIM", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def load_channel_model(self, model_name: str):
        """
        加载仿真模型。
        """
        self.logger.info(f"PROPSIM 加载模型: {model_name}")
        # 根据 PROPSIM ATE 语法，参数间空格，字符串通常不带引号
        self.write(f"CALCulate:FILTer:FILE {model_name}")
        
        # 检查错误
        err = self.query("SYSTem:ERRor?")
        if "0," not in err:
            self.logger.error(f"PROPSIM 加载模型报错: {err}")

    def rf_on(self):
        """
        开始仿真并开启发射。
        """
        self.write("SIMulation:STARt")
        self.logger.info("PROPSIM: 仿真已启动")

    def rf_off(self):
        """
        停止所有发射。
        """
        self.write("SYSTem:TRANSmitter:OFF")
        self.logger.info("PROPSIM: 所有射频输出已关闭")