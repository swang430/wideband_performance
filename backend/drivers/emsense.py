from drivers.base_instrument import BaseInstrument


class EMSense_Driver(BaseInstrument):
    """
    EMCenter EMSense 电场探头驱动 (7007-200系列)。
    
    支持E场强度测量、峰值保持等功能。
    
    Ref: EMCenter_SCPI_Cmds_and_Errs_RevA_1801188.pdf p.76-82
    """

    def __init__(self, resource_name: str, name: str = "EMSense", simulation_mode: bool = False, slot: int = 1):
        super().__init__(resource_name, name, simulation_mode, reset_on_connect=False)
        self.slot = slot  # 默认插槽1
        self.logger.info(f"EMSense 电场探头驱动已加载，插槽: {self.slot}")

    def read_efield(self) -> float:
        """
        读取E场强度。
        
        Returns:
            E场强度（V/m）
        
        Ref: EMCenter SCPI Manual p.76+
        - EFIELD?: 读取E场强度
        """
        if self.simulation_mode:
            import random
            efield = 10.0 + random.uniform(-2, 2)
            self.logger.info(f"[模拟] EMSense E场: {efield:.2f} V/m")
            return efield
        
        command = f"{self.slot}:EFIELD?"
        response = self.query(command)
        
        try:
            efield = float(response.strip().split()[0])
            self.logger.info(f"E场强度: {efield:.2f} V/m")
            return efield
        except (ValueError, IndexError) as e:
            self.logger.error(f"E场读取失败: {response}, 错误: {e}")
            return 0.0

    def set_mode(self, mode: int) -> None:
        """
        设置测量模式。
        
        Args:
            mode: 测量模式
                0 = 正常模式
                1 = 峰值保持
                2 = 最小值
        
        Ref: EMCenter SCPI Manual p.76+
        - MODE <mode>: 设置模式
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMSense 设置模式: {mode}")
            return
        
        command = f"{self.slot}:MODE {mode}"
        self.write(command)
        
        mode_names = {0: "正常", 1: "峰值保持", 2: "最小值"}
        self.logger.info(f"设置测量模式: {mode_names.get(mode, str(mode))}")

    def reset_peak(self) -> None:
        """
        复位峰值保持。
        
        Ref: EMCenter SCPI Manual p.76+
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMSense 复位峰值")
            return
        
        command = f"{self.slot}:PEAK:RESET"
        self.write(command)
        self.logger.info("峰值已复位")

    def get_laser_status(self) -> str:
        """
        查询激光状态（EMSense特有）。
        
        Returns:
            状态字符串 ("ON", "STANDBY", 等)
        
        Ref: EMCenter SCPI Manual p.7
        - LASER_STATUS?: 查询激光状态
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMSense 查询激光状态")
            return "ON"
        
        command = f"{self.slot}:LASER_STATUS?"
        response = self.query(command)
        
        status = response.strip()
        self.logger.info(f"激光状态: {status}")
        return status

    def set_slot(self, slot: int) -> None:
        """
        设置插槽编号。
        
        Args:
            slot: 插槽编号 (1-8)
        """
        if not (1 <= slot <= 8):
            raise ValueError(f"插槽编号必须在1-8范围内: {slot}")
        
        self.slot = slot
        self.logger.info(f"插槽编号设置为: {slot}")
