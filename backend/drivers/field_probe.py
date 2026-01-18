import logging

from drivers.base_instrument import BaseInstrument


class FieldProbe:
    """
    电场探头 HAL 封装层。
    
    支持EMSense等电场探头，通过工厂自动识别型号。
    """

    def __init__(self, resource_name: str, name: str = "FieldProbe", 
                 simulation_mode: bool = False, slot: int = 1):
        """
        初始化电场探头 HAL。
        
        Args:
            resource_name: VISA 资源地址
            name: 探头名称
            simulation_mode: 是否启用模拟模式
            slot: 插槽编号（EMCenter）
        """
        self.resource_name = resource_name
        self.name = name
        self.simulation_mode = simulation_mode
        self.slot = slot
        self.logger = logging.getLogger(f"HAL.{name}")
        self._driver: BaseInstrument = None

    def connect(self) -> None:
        """
        连接到电场探头并自动识别型号。
        """
        idn_string = "Unknown"

        if not self.simulation_mode:
            try:
                import pyvisa
                temp_rm = pyvisa.ResourceManager()
                temp_inst = temp_rm.open_resource(self.resource_name)
                idn_string = temp_inst.query("*IDN?").strip()
                temp_inst.close()
                self.logger.info(f"检测到电场探头: {idn_string}")
            except Exception as e:
                self.logger.warning(f"无法查询 IDN，使用EMSense驱动: {e}")
                idn_string = "EMSense"
        else:
            idn_string = "Simulated ETS-Lindgren, EMSense 10 7007-200, v1.0"

        # 使用EMSense驱动
        from drivers.emsense import EMSense_Driver
        
        self._driver = EMSense_Driver(
            self.resource_name,
            name=self.name,
            simulation_mode=self.simulation_mode,
            slot=self.slot
        )
        self._driver.connect()
        self.logger.info(f"{self.name} HAL 已就绪")

    def disconnect(self) -> None:
        """
        断开探头连接。
        """
        if self._driver:
            self._driver.disconnect()

    # --- 标准接口方法 ---

    def read_field(self) -> float:
        """
        读取E场强度。
        
        Returns:
            E场强度（V/m）
        """
        if self._driver:
            return self._driver.read_efield()
        else:
            raise ConnectionError("电场探头未连接")

    def set_mode(self, mode: str) -> None:
        """
        设置测量模式。
        
        Args:
            mode: 测量模式 ("normal", "peak", "min")
        """
        if not self._driver:
            raise ConnectionError("电场探头未连接")
        
        mode_map = {
            "normal": 0,
            "peak": 1,
            "min": 2
        }
        
        mode_code = mode_map.get(mode.lower(), 0)
        self._driver.set_mode(mode_code)

    def reset_peak(self) -> None:
        """
        复位峰值保持。
        """
        if self._driver:
            self._driver.reset_peak()
        else:
            raise ConnectionError("电场探头未连接")

    def get_laser_status(self) -> str:
        """
        查询激光状态。
        
        Returns:
            状态字符串
        """
        if self._driver:
            return self._driver.get_laser_status()
        else:
            raise ConnectionError("电场探头未连接")

    # --- 高级方法 ---

    def measure_peak_field(self, duration_sec: float = 5.0) -> float:
        """
        [高级接口] 测量指定时间内的峰值场强。
        
        Args:
            duration_sec: 测量持续时间（秒）
        
        Returns:
            峰值E场强度（V/m）
        """
        import time
        
        self.logger.info(f"测量峰值场强，持续 {duration_sec} 秒...")
        
        # 切换到峰值模式
        self.set_mode("peak")
        
        # 复位峰值
        self.reset_peak()
        
        # 等待测量
        time.sleep(duration_sec)
        
        # 读取峰值
        peak = self.read_field()
        
        # 恢复正常模式
        self.set_mode("normal")
        
        self.logger.info(f"峰值场强: {peak:.2f} V/m")
        return peak

    def measure_average_field(self, count: int = 100, interval_ms: float = 100) -> float:
        """
        [高级接口] 测量平均场强。
        
        Args:
            count: 采样次数
            interval_ms: 采样间隔（毫秒）
        
        Returns:
            平均E场强度（V/m）
        """
        import time
        
        self.logger.info(f"测量平均场强，{count} 次采样...")
        
        # 确保在正常模式
        self.set_mode("normal")
        
        samples = []
        for i in range(count):
            try:
                field = self.read_field()
                samples.append(field)
                if interval_ms > 0:
                    time.sleep(interval_ms / 1000.0)
            except Exception as e:
                self.logger.warning(f"采样 {i+1} 失败: {e}")
        
        if samples:
            avg = sum(samples) / len(samples)
            self.logger.info(f"平均场强: {avg:.2f} V/m ({len(samples)}次有效采样)")
            return avg
        else:
            return 0.0

    def check_compliance(self, limit_vm: float) -> bool:
        """
        [高级接口] 检查场强是否符合限值。
        
        Args:
            limit_vm: 场强限值（V/m）
        
        Returns:
            True=符合, False=超限
        """
        current = self.read_field()
        compliant = current <= limit_vm
        
        if compliant:
            self.logger.info(f"场强符合限值: {current:.2f} V/m ≤ {limit_vm} V/m")
        else:
            self.logger.warning(f"场强超限: {current:.2f} V/m > {limit_vm} V/m")
        
        return compliant
