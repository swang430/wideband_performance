from drivers.base_instrument import BaseInstrument


class EMPower_Driver(BaseInstrument):
    """
    EMCenter EMPower 功率计驱动 (7002-00x系列)。
    
    支持实时功率测量、峰值检测、数据采集等功能。
    
    Ref: EMCenter_SCPI_Cmds_and_Errs_RevA_1801188.pdf p.15-28
    """

    def __init__(self, resource_name: str, name: str = "EMPower", simulation_mode: bool = False, 
                 slot: int = 2, port: str = "A"):
        super().__init__(resource_name, name, simulation_mode, reset_on_connect=False)
        self.slot = slot  # 默认插槽2
        self.port = port  # 默认端口A (支持A或B)
        self.logger.info(f"EMPower 功率计驱动已加载，插槽: {self.slot}, 端口: {self.port}")

    def read_power(self) -> float:
        """
        读取实时功率值。
        
        Returns:
            功率值（dBm）
        
        Ref: EMCenter SCPI Manual p.18
        - POWER?: 返回测量功率（dBm）
        """
        if self.simulation_mode:
            import random
            power = -50.0 + random.uniform(-5, 5)
            self.logger.info(f"[模拟] EMPower 读取功率: {power:.2f} dBm")
            return power
        
        command = f"{self.slot}{self.port}:POWER?"
        response = self.query(command)
        
        try:
            # 响应格式: "-63.84 dBm"
            power = float(response.split()[0])
            self.logger.info(f"功率: {power:.2f} dBm")
            return power
        except (ValueError, IndexError) as e:
            self.logger.error(f"功率读取解析失败: {response}, 错误: {e}")
            return -999.0

    def read_power_burst(self, count: int) -> list:
        """
        连续读取多次功率值。
        
        Args:
            count: 测量次数 (1-100)
        
        Returns:
            功率值列表（dBm）
        
        Ref: EMCenter SCPI Manual p.16
        - BURST? <n>: 连续测量n次
        """
        if self.simulation_mode:
            import random
            powers = [-50.0 + random.uniform(-3, 3) for _ in range(count)]
            self.logger.info(f"[模拟] EMPower 突发测量 {count} 次")
            return powers
        
        command = f"{self.slot}{self.port}:BURST? {count}"
        response = self.query(command)
        
        try:
            # 响应格式: "-63.92 -63.85 -63.85 -64.03 -63.99 dBm"
            values = response.replace("dBm", "").strip().split()
            powers = [float(v) for v in values]
            self.logger.info(f"突发测量 {len(powers)} 次")
            return powers
        except (ValueError, IndexError) as e:
            self.logger.error(f"突发测量解析失败: {response}, 错误: {e}")
            return []

    def set_frequency(self, freq_hz: float) -> None:
        """
        设置功率计工作频率。
        
        Args:
            freq_hz: 频率（Hz）
        
        Ref: EMCenter SCPI Manual p.17
        - FREQUENCY <freq>: 设置频率
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMPower 设置频率: {freq_hz/1e6:.1f} MHz")
            return
        
        command = f"{self.slot}{self.port}:FREQUENCY {freq_hz}"
        self.write(command)
        self.logger.info(f"设置频率: {freq_hz/1e6:.1f} MHz")

    def set_power_offset(self, offset_db: float) -> None:
        """
        设置功率偏移（校准用）。
        
        Args:
            offset_db: 功率偏移（dB），范围 -100.0 到 100.0
        
        Ref: EMCenter SCPI Manual p.19
        - POWER_OFFSET <dB>: 设置功率偏移
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMPower 设置功率偏移: {offset_db} dB")
            return
        
        if not (-100.0 <= offset_db <= 100.0):
            raise ValueError(f"功率偏移超出范围 (-100~100 dB): {offset_db}")
        
        command = f"{self.slot}{self.port}:POWER_OFFSET {offset_db}"
        self.write(command)
        self.logger.info(f"设置功率偏移: {offset_db} dB")

    def get_power_offset(self) -> float:
        """
        查询当前功率偏移。
        
        Returns:
            功率偏移（dB）
        
        Ref: EMCenter SCPI Manual p.19
        - POWER_OFFSET?: 查询功率偏移
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMPower 查询功率偏移")
            return 0.0
        
        command = f"{self.slot}{self.port}:POWER_OFFSET?"
        response = self.query(command)
        
        try:
            # 响应格式: "30.00 dB"
            offset = float(response.split()[0])
            self.logger.info(f"功率偏移: {offset} dB")
            return offset
        except (ValueError, IndexError) as e:
            self.logger.error(f"功率偏移查询失败: {response}, 错误: {e}")
            return 0.0

    def set_filter_mode(self, mode: int) -> None:
        """
        设置RMS滤波器模式。
        
        Args:
            mode: 滤波器模式
                1 = 10 samples
                2 = 30 samples
                3 = 100 samples
                4 = 300 samples
                5 = 1000 samples
                6 = 3000 samples
                7 = 5000 samples
        
        Ref: EMCenter SCPI Manual p.16
        - FILTER <mode>: 设置滤波器
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMPower 设置滤波器模式: {mode}")
            return
        
        if not (1 <= mode <= 7):
            raise ValueError(f"滤波器模式无效 (1-7): {mode}")
        
        command = f"{self.slot}{self.port}:FILTER {mode}"
        self.write(command)
        self.logger.info(f"设置滤波器模式: {mode}")

    def set_acquisition_speed(self, ks_per_sec: int) -> None:
        """
        设置采样速度。
        
        Args:
            ks_per_sec: 采样速度（KS/sec），范围 1-5000
        
        Ref: EMCenter SCPI Manual p.15
        - ACQ_SPEED <KS>: 设置采样速度
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMPower 设置采样速度: {ks_per_sec} KS/s")
            return
        
        command = f"{self.slot}{self.port}:ACQ_SPEED {ks_per_sec}"
        self.write(command)
        self.logger.info(f"设置采样速度: {ks_per_sec} KS/s")

    def set_mode(self, mode: int) -> None:
        """
        设置工作模式。
        
        Args:
            mode: 工作模式
                0 = 连续测量
                1 = 单次测量
                2 = 自动存储
                3 = 突发模式
        
        Ref: EMCenter SCPI Manual p.18
        - MODE <mode>: 设置模式
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMPower 设置工作模式: {mode}")
            return
        
        if not (0 <= mode <= 3):
            raise ValueError(f"工作模式无效 (0-3): {mode}")
        
        command = f"{self.slot}{self.port}:MODE {mode}"
        self.write(command)
        
        mode_names = {0: "连续", 1: "单次", 2: "自动存储", 3: "突发"}
        self.logger.info(f"设置工作模式: {mode_names.get(mode, str(mode))}")

    def get_temperature(self) -> float:
        """
        查询功率计温度。
        
        Returns:
            温度（摄氏度）
        
        Ref: EMCenter SCPI Manual p.20
        - TEMPERATURE?: 查询温度
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMPower 查询温度")
            return 25.0
        
        command = f"{self.slot}:TEMPERATURE?"
        response = self.query(command)
        
        try:
            temp = float(response.strip())
            self.logger.info(f"温度: {temp}°C")
            return temp
        except ValueError as e:
            self.logger.error(f"温度查询失败: {response}, 错误: {e}")
            return -273.15

    def set_slot_port(self, slot: int, port: str) -> None:
        """
        设置插槽和端口。
        
        Args:
            slot: 插槽编号 (1-8)
            port: 端口 ("A" 或 "B")
        """
        if not (1 <= slot <= 8):
            raise ValueError(f"插槽编号必须在1-8范围内: {slot}")
        
        if port not in ["A", "B"]:
            raise ValueError(f"端口必须为A或B: {port}")
        
        self.slot = slot
        self.port = port
        self.logger.info(f"插槽端口设置为: {slot}{port}")
