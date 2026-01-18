from drivers.base_instrument import BaseInstrument


class GenericAmplifier(BaseInstrument):
    """
    通用可编程放大器驱动基类。
    
    定义标准接口方法，具体厂商驱动需要继承此类并实现SCPI指令。
    """

    def __init__(self, resource_name: str, name: str = "Generic_Amplifier", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def set_gain(self, db: float) -> None:
        """
        [标准接口] 设置增益。
        
        Args:
            db: 增益值（dB），范围取决于硬件（如0-50 dB）
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] 设置增益: {db} dB")
            return
        
        # 占位符实现，需在子类中覆盖
        self.logger.warning(f"set_gain() 未实现，dB={db}")

    def get_gain(self) -> float:
        """
        [标准接口] 查询当前增益。
        
        Returns:
            增益值（dB）
        """
        if self.simulation_mode:
            self.logger.info("[模拟] 查询增益")
            return 20.0
        
        # 占位符实现
        self.logger.warning("get_gain() 未实现")
        return 0.0

    def enable_output(self, enable: bool) -> None:
        """
        [标准接口] 开关放大器输出。
        
        Args:
            enable: True=开启, False=关闭
        """
        state = "ON" if enable else "OFF"
        
        if self.simulation_mode:
            self.logger.info(f"[模拟] 放大器输出: {state}")
            return
        
        # 占位符实现
        self.logger.warning(f"enable_output() 未实现，enable={enable}")

    def get_output_state(self) -> bool:
        """
        [标准接口] 查询输出状态。
        
        Returns:
            True=开启, False=关闭
        """
        if self.simulation_mode:
            self.logger.info("[模拟] 查询输出状态")
            return False
        
        # 占位符实现
        self.logger.warning("get_output_state() 未实现")
        return False

    def get_gain_range(self) -> tuple:
        """
        [标准接口] 查询增益范围。
        
        Returns:
            (最小值, 最大值) 元组（dB）
        """
        # 默认值，子类应覆盖
        return (0.0, 50.0)

    def set_bias_voltage(self, voltage: float) -> None:
        """
        [扩展接口] 设置偏置电压（如果支持）。
        
        Args:
            voltage: 偏置电压（V）
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] 设置偏置电压: {voltage} V")
            return
        
        self.logger.warning(f"set_bias_voltage() 未实现，voltage={voltage}")

    def get_temperature(self) -> float:
        """
        [扩展接口] 查询放大器温度（如果支持）。
        
        Returns:
            温度（摄氏度）
        """
        if self.simulation_mode:
            self.logger.info("[模拟] 查询温度")
            return 25.0
        
        self.logger.warning("get_temperature() 未实现")
        return -273.15
