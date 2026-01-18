import logging

from drivers.base_instrument import BaseInstrument


class SignalGenerator:
    """
    信号发生器 HAL 封装层。
    
    支持EMGen等信号源，通过工厂自动识别型号。
    注意：与VSG不同，这是专门用于EMCenter EMGen模块的HAL。
    """

    def __init__(self, resource_name: str, name: str = "SignalGenerator", 
                 simulation_mode: bool = False, slot: int = 3):
        """
        初始化信号发生器 HAL。
        
        Args:
            resource_name: VISA 资源地址
            name: 信号源名称
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
        连接到信号源并自动识别型号。
        """
        idn_string = "Unknown"

        if not self.simulation_mode:
            try:
                import pyvisa
                temp_rm = pyvisa.ResourceManager()
                temp_inst = temp_rm.open_resource(self.resource_name)
                idn_string = temp_inst.query("*IDN?").strip()
                temp_inst.close()
                self.logger.info(f"检测到信号源: {idn_string}")
            except Exception as e:
                self.logger.warning(f"无法查询 IDN，使用EMGen驱动: {e}")
                idn_string = "EMGen"
        else:
            idn_string = "Simulated ETS-Lindgren, EMGen 7003-003, v1.0"

        # 使用EMGen驱动
        from drivers.emgen import EMGen_Driver
        
        self._driver = EMGen_Driver(
            self.resource_name,
            name=self.name,
            simulation_mode=self.simulation_mode,
            slot=self.slot
        )
        self._driver.connect()
        self.logger.info(f"{self.name} HAL 已就绪")

    def disconnect(self) -> None:
        """
        断开信号源连接。
        """
        if self._driver:
            self._driver.disconnect()

    # --- 基本载波控制 ---

    def set_frequency(self, freq_hz: float) -> None:
        """
        设置载波频率。
        
        Args:
            freq_hz: 频率（Hz）
        """
        if self._driver:
            self._driver.set_frequency(freq_hz)
        else:
            raise ConnectionError("信号源未连接")

    def get_frequency(self) -> float:
        """
        查询当前频率。
        
        Returns:
            频率（Hz）
        """
        if self._driver:
            return self._driver.get_frequency()
        else:
            raise ConnectionError("信号源未连接")

    def set_power(self, power_dbm: float) -> None:
        """
        设置输出功率。
        
        Args:
            power_dbm: 功率（dBm）
        """
        if self._driver:
            self._driver.set_power(power_dbm)
        else:
            raise ConnectionError("信号源未连接")

    def get_power(self) -> float:
        """
        查询当前功率。
        
        Returns:
            功率（dBm）
        """
        if self._driver:
            return self._driver.get_power()
        else:
            raise ConnectionError("信号源未连接")

    def enable_output(self, enable: bool) -> None:
        """
        开关RF输出。
        
        Args:
            enable: True=开启, False=关闭
        """
        if self._driver:
            self._driver.enable_output(enable)
        else:
            raise ConnectionError("信号源未连接")

    def get_output_state(self) -> bool:
        """
        查询输出状态。
        
        Returns:
            True=开启, False=关闭
        """
        if self._driver:
            return self._driver.get_output_state()
        else:
            raise ConnectionError("信号源未连接")

    # --- 调制功能 ---

    def configure_am(self, enable: bool, depth_percent: float = 50.0, 
                     freq_hz: float = 1000.0) -> None:
        """
        [高级接口] 配置幅度调制。
        
        Args:
            enable: True=开启AM, False=关闭AM
            depth_percent: 调制深度（%）
            freq_hz: 调制频率（Hz）
        """
        if not self._driver:
            raise ConnectionError("信号源未连接")
        
        self._driver.enable_am(enable)
        if enable:
            self._driver.set_am_depth(depth_percent)
            self._driver.set_am_frequency(freq_hz)
            self.logger.info(f"AM调制已开启: 深度={depth_percent}%, 频率={freq_hz} Hz")
        else:
            self.logger.info("AM调制已关闭")

    def configure_fm(self, enable: bool, deviation_hz: float = 10000.0, 
                     freq_hz: float = 1000.0) -> None:
        """
        [高级接口] 配置频率调制。
        
        Args:
            enable: True=开启FM, False=关闭FM
            deviation_hz: 频偏（Hz）
            freq_hz: 调制频率（Hz）
        """
        if not self._driver:
            raise ConnectionError("信号源未连接")
        
        self._driver.enable_fm(enable)
        if enable:
            self._driver.set_fm_deviation(deviation_hz)
            self._driver.set_fm_frequency(freq_hz)
            self.logger.info(f"FM调制已开启: 频偏={deviation_hz} Hz, 频率={freq_hz} Hz")
        else:
            self.logger.info("FM调制已关闭")

    def configure_pulse(self, enable: bool, width_us: float = 10.0, 
                       prf_hz: float = 1000.0) -> None:
        """
        [高级接口] 配置脉冲调制。
        
        Args:
            enable: True=开启脉冲, False=关闭脉冲
            width_us: 脉宽（微秒）
            prf_hz: 脉冲重复频率（Hz）
        """
        if not self._driver:
            raise ConnectionError("信号源未连接")
        
        self._driver.enable_pulse(enable)
        if enable:
            self._driver.set_pulse_width(width_us * 1e-6)  # 转换为秒
            self._driver.set_pulse_period(1.0 / prf_hz)  # 周期 = 1/PRF
            self.logger.info(f"脉冲调制已开启: 脉宽={width_us} μs, PRF={prf_hz} Hz")
        else:
            self.logger.info("脉冲调制已关闭")

    # --- 高级方法 ---

    def configure_cw(self, freq_hz: float, power_dbm: float, output_on: bool = True) -> None:
        """
        [高级接口] 配置连续波(CW)输出。
        
        Args:
            freq_hz: 频率（Hz）
            power_dbm: 功率（dBm）
            output_on: 是否立即开启输出
        """
        self.logger.info(f"配置CW: {freq_hz/1e6:.3f} MHz, {power_dbm} dBm")
        
        # 关闭所有调制
        self.configure_am(False)
        self.configure_fm(False)
        self.configure_pulse(False)
        
        # 设置频率和功率
        self.set_frequency(freq_hz)
        self.set_power(power_dbm)
        
        # 开启输出
        if output_on:
            self.enable_output(True)

    def configure_modulated_carrier(self, freq_hz: float, power_dbm: float,
                                    mod_type: str = "AM", mod_params: dict = None) -> None:
        """
        [高级接口] 配置调制载波。
        
        Args:
            freq_hz: 载波频率（Hz）
            power_dbm: 载波功率（dBm）
            mod_type: 调制类型 ("AM", "FM", "Pulse")
            mod_params: 调制参数字典
        """
        self.logger.info(f"配置{mod_type}调制载波: {freq_hz/1e6:.3f} MHz, {power_dbm} dBm")
        
        # 设置载波
        self.set_frequency(freq_hz)
        self.set_power(power_dbm)
        
        # 配置调制
        mod_params = mod_params or {}
        
        if mod_type.upper() == "AM":
            self.configure_am(
                True,
                depth_percent=mod_params.get('depth', 50.0),
                freq_hz=mod_params.get('freq', 1000.0)
            )
        elif mod_type.upper() == "FM":
            self.configure_fm(
                True,
                deviation_hz=mod_params.get('deviation', 10000.0),
                freq_hz=mod_params.get('freq', 1000.0)
            )
        elif mod_type.upper() == "PULSE":
            self.configure_pulse(
                True,
                width_us=mod_params.get('width', 10.0),
                prf_hz=mod_params.get('prf', 1000.0)
            )
        
        # 开启输出
        self.enable_output(True)
