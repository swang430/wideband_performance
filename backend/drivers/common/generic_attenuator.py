from drivers.base_instrument import BaseInstrument


class GenericAttenuator(BaseInstrument):
    """
    通用可编程衰减器驱动基类。
    
    定义标准接口方法，具体厂商驱动需要继承此类并实现SCPI指令。
    """

    def __init__(self, resource_name: str, name: str = "Generic_Attenuator", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def set_attenuation(self, db: float) -> None:
        """
        [标准接口] 设置衰减值。
        
        Args:
            db: 衰减值（dB），范围取决于硬件（通常0-90 dB）
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] 设置衰减: {db} dB")
            return
        
        # 占位符实现，需在子类中覆盖
        self.logger.warning(f"set_attenuation() 未实现，dB={db}")

    def get_attenuation(self) -> float:
        """
        [标准接口] 查询当前衰减值。
        
        Returns:
            衰减值（dB）
        """
        if self.simulation_mode:
            self.logger.info("[模拟] 查询衰减")
            return 10.0
        
        # 占位符实现
        self.logger.warning("get_attenuation() 未实现")
        return 0.0

    def increment_attenuation(self, step_db: float) -> None:
        """
        [标准接口] 增量调整衰减值。
        
        Args:
            step_db: 增量（dB），正值增加衰减，负值减少衰减
        """
        current = self.get_attenuation()
        new_value = current + step_db
        self.set_attenuation(new_value)
        self.logger.info(f"衰减调整: {current} dB -> {new_value} dB")

    def get_attenuation_range(self) -> tuple:
        """
        [标准接口] 查询衰减器范围。
        
        Returns:
            (最小值, 最大值) 元组（dB）
        """
        # 默认值，子类应覆盖
        return (0.0, 90.0)

    def get_step_size(self) -> float:
        """
        [标准接口] 查询衰减器步进。
        
        Returns:
            步进值（dB）
        """
        # 默认值，子类应覆盖
        return 0.25  # 常见的0.25 dB步进
