import logging

from drivers.base_instrument import BaseInstrument


class PowerMeter:
    """
    功率计 HAL 封装层。
    
    支持EMPower等功率计，通过工厂自动识别型号。
    """

    def __init__(self, resource_name: str, name: str = "PowerMeter", 
                 simulation_mode: bool = False, slot: int = 2, port: str = "A"):
        """
        初始化功率计 HAL。
        
        Args:
            resource_name: VISA 资源地址
            name: 功率计名称
            simulation_mode: 是否启用模拟模式
            slot: 插槽编号（EMCenter）
            port: 端口（"A" 或 "B"）
        """
        self.resource_name = resource_name
        self.name = name
        self.simulation_mode = simulation_mode
        self.slot = slot
        self.port = port
        self.logger = logging.getLogger(f"HAL.{name}")
        self._driver: BaseInstrument = None

    def connect(self) -> None:
        """
        连接到功率计并自动识别型号。
        """
        # 创建临时连接获取 IDN
        idn_string = "Unknown"

        if not self.simulation_mode:
            try:
                import pyvisa
                temp_rm = pyvisa.ResourceManager()
                temp_inst = temp_rm.open_resource(self.resource_name)
                idn_string = temp_inst.query("*IDN?").strip()
                temp_inst.close()
                self.logger.info(f"检测到功率计: {idn_string}")
            except Exception as e:
                self.logger.warning(f"无法查询 IDN，使用EMPower驱动: {e}")
                idn_string = "EMPower"
        else:
            idn_string = "Simulated ETS-Lindgren, EMPower 7002-001, v1.0"

        # 自动识别或默认使用EMPower驱动
        from drivers.empower import EMPower_Driver
        
        self._driver = EMPower_Driver(
            self.resource_name,
            name=self.name,
            simulation_mode=self.simulation_mode,
            slot=self.slot,
            port=self.port
        )
        self._driver.connect()
        self.logger.info(f"{self.name} HAL 已就绪")

    def disconnect(self) -> None:
        """
        断开功率计连接。
        """
        if self._driver:
            self._driver.disconnect()

    # --- 标准接口方法（委托到底层驱动） ---

    def read_power(self) -> float:
        """
        读取当前功率。
        
        Returns:
            功率值（dBm）
        """
        if self._driver:
            return self._driver.read_power()
        else:
            raise ConnectionError("功率计未连接")

    def read_power_burst(self, count: int) -> list:
        """
        连续读取多次功率。
        
        Args:
            count: 测量次数
        
        Returns:
            功率值列表（dBm）
        """
        if self._driver:
            return self._driver.read_power_burst(count)
        else:
            raise ConnectionError("功率计未连接")

    def set_frequency(self, freq_hz: float) -> None:
        """
        设置工作频率。
        
        Args:
            freq_hz: 频率（Hz）
        """
        if self._driver:
            self._driver.set_frequency(freq_hz)
        else:
            raise ConnectionError("功率计未连接")

    def calibrate(self, offset_db: float) -> None:
        """
        校准功率计（设置功率偏移）。
        
        Args:
            offset_db: 功率偏移（dB）
        """
        if self._driver:
            self._driver.set_power_offset(offset_db)
        else:
            raise ConnectionError("功率计未连接")

    def get_calibration(self) -> float:
        """
        查询校准偏移值。
        
        Returns:
            功率偏移（dB）
        """
        if self._driver:
            return self._driver.get_power_offset()
        else:
            raise ConnectionError("功率计未连接")

    def configure(self, freq_hz: float = None, offset_db: float = 0.0, 
                  filter_mode: int = 3) -> None:
        """
        [高级接口] 一键配置功率计。
        
        Args:
            freq_hz: 工作频率（Hz），None表示不改变
            offset_db: 校准偏移（dB）
            filter_mode: 滤波器模式（1-7）
        """
        self.logger.info(f"配置功率计: 频率={freq_hz/1e6 if freq_hz else 'N/A'} MHz, "
                        f"偏移={offset_db} dB, 滤波器={filter_mode}")
        
        if freq_hz is not None:
            self.set_frequency(freq_hz)
        
        if offset_db != 0.0:
            self.calibrate(offset_db)
        
        if self._driver:
            self._driver.set_filter_mode(filter_mode)

    def measure_average(self, count: int = 10) -> float:
        """
        [高级接口] 测量平均功率。
        
        Args:
            count: 采样次数
        
        Returns:
            平均功率（dBm）
        """
        powers = self.read_power_burst(count)
        if powers:
            avg = sum(powers) / len(powers)
            self.logger.info(f"平均功率: {avg:.2f} dBm ({count}次采样)")
            return avg
        else:
            return -999.0

    def get_temperature(self) -> float:
        """
        查询功率计温度。
        
        Returns:
            温度（摄氏度）
        """
        if self._driver:
            return self._driver.get_temperature()
        else:
            raise ConnectionError("功率计未连接")
