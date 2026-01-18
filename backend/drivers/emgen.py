from drivers.base_instrument import BaseInstrument


class EMGen_Driver(BaseInstrument):
    """
    EMCenter EMGen 信号发生器驱动 (7003-003)。
    
    支持频率/功率控制、AM/FM/Pulse调制等功能。
    
    Ref: EMCenter_SCPI_Cmds_and_Errs_RevA_1801188.pdf p.30-52
    """

    def __init__(self, resource_name: str, name: str = "EMGen", simulation_mode: bool = False, slot: int = 3):
        super().__init__(resource_name, name, simulation_mode, reset_on_connect=False)
        self.slot = slot  # 默认插槽3
        self.logger.info(f"EMGen 信号发生器驱动已加载，插槽: {self.slot}")

    def set_frequency(self, freq_hz: float) -> None:
        """
        设置载波频率。
        
        Args:
            freq_hz: 频率（Hz），范围取决于型号（通常100 kHz - 6 GHz）
        
        Ref: EMCenter SCPI Manual p.42
        - FREQ <Hz>: 设置载波频率
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen 设置频率: {freq_hz/1e6:.3f} MHz")
            return
        
        command = f"{self.slot}:FREQ {freq_hz}"
        self.write(command)
        self.logger.info(f"设置频率: {freq_hz/1e6:.3f} MHz")

    def get_frequency(self) -> float:
        """
        查询当前载波频率。
        
        Returns:
            频率（Hz）
        
        Ref: EMCenter SCPI Manual p.42
        - FREQ?: 查询载波频率
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMGen 查询频率")
            return 1000e6  # 模拟1 GHz
        
        command = f"{self.slot}:FREQ?"
        response = self.query(command)
        
        try:
            freq = float(response.strip())
            self.logger.info(f"当前频率: {freq/1e6:.3f} MHz")
            return freq
        except ValueError as e:
            self.logger.error(f"频率查询失败: {response}, 错误: {e}")
            return 0.0

    def set_power(self, power_dbm: float) -> None:
        """
        设置输出功率。
        
        Args:
            power_dbm: 功率（dBm），范围通常 -50 到 +10 dBm
        
        Ref: EMCenter SCPI Manual p.48
        - POWER <dBm>: 设置输出功率
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen 设置功率: {power_dbm} dBm")
            return
        
        command = f"{self.slot}:POWER {power_dbm}"
        self.write(command)
        self.logger.info(f"设置功率: {power_dbm} dBm")

    def get_power(self) -> float:
        """
        查询当前输出功率。
        
        Returns:
            功率（dBm）
        
        Ref: EMCenter SCPI Manual p.48
        - POWER?: 查询输出功率
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMGen 查询功率")
            return 0.0
        
        command = f"{self.slot}:POWER?"
        response = self.query(command)
        
        try:
            power = float(response.strip())
            self.logger.info(f"当前功率: {power} dBm")
            return power
        except ValueError as e:
            self.logger.error(f"功率查询失败: {response}, 错误: {e}")
            return -999.0

    def enable_output(self, enable: bool) -> None:
        """
        开关RF输出。
        
        Args:
            enable: True=开启, False=关闭
        
        Ref: EMCenter SCPI Manual p.44
        - OUTPUT ON/OFF: 控制RF输出
        """
        state = "ON" if enable else "OFF"
        
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen RF输出: {state}")
            return
        
        command = f"{self.slot}:OUTPUT {state}"
        self.write(command)
        self.logger.info(f"RF输出: {state}")

    def get_output_state(self) -> bool:
        """
        查询RF输出状态。
        
        Returns:
            True=开启, False=关闭
        
        Ref: EMCenter SCPI Manual p.44
        - OUTPUT?: 查询输出状态
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMGen 查询输出状态")
            return False
        
        command = f"{self.slot}:OUTPUT?"
        response = self.query(command)
        
        is_on = response.strip().upper() in ["ON", "1"]
        self.logger.info(f"输出状态: {'ON' if is_on else 'OFF'}")
        return is_on

    # === 幅度调制 (AM) ===

    def enable_am(self, enable: bool) -> None:
        """
        开关幅度调制。
        
        Args:
            enable: True=开启, False=关闭
        
        Ref: EMCenter SCPI Manual p.36
        - AM:STATE ON/OFF: 控制AM调制
        """
        state = "ON" if enable else "OFF"
        
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen AM调制: {state}")
            return
        
        command = f"{self.slot}:AM:STATE {state}"
        self.write(command)
        self.logger.info(f"AM调制: {state}")

    def set_am_depth(self, depth_percent: float) -> None:
        """
        设置AM调制深度。
        
        Args:
            depth_percent: 调制深度（%），范围 0-100
        
        Ref: EMCenter SCPI Manual p.36
        - AM:DEPTH <percent>: 设置调制深度
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen AM调制深度: {depth_percent}%")
            return
        
        if not (0 <= depth_percent <= 100):
            raise ValueError(f"AM调制深度超出范围 (0-100%): {depth_percent}")
        
        command = f"{self.slot}:AM:DEPTH {depth_percent}"
        self.write(command)
        self.logger.info(f"AM调制深度: {depth_percent}%")

    def set_am_frequency(self, freq_hz: float) -> None:
        """
        设置AM调制频率（内部调制源）。
        
        Args:
            freq_hz: 调制频率（Hz）
        
        Ref: EMCenter SCPI Manual p.36
        - AM:INT:FREQ <Hz>: 设置内部调制频率
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen AM调制频率: {freq_hz} Hz")
            return
        
        command = f"{self.slot}:AM:INT:FREQ {freq_hz}"
        self.write(command)
        self.logger.info(f"AM调制频率: {freq_hz} Hz")

    # === 频率调制 (FM) ===

    def enable_fm(self, enable: bool) -> None:
        """
        开关频率调制。
        
        Args:
            enable: True=开启, False=关闭
        
        Ref: EMCenter SCPI Manual p.39
        - FM:STATE ON/OFF: 控制FM调制
        """
        state = "ON" if enable else "OFF"
        
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen FM调制: {state}")
            return
        
        command = f"{self.slot}:FM:STATE {state}"
        self.write(command)
        self.logger.info(f"FM调制: {state}")

    def set_fm_deviation(self, deviation_hz: float) -> None:
        """
        设置FM频偏。
        
        Args:
            deviation_hz: 频偏（Hz）
        
        Ref: EMCenter SCPI Manual p.39
        - FM:DEV <Hz>: 设置频偏
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen FM频偏: {deviation_hz} Hz")
            return
        
        command = f"{self.slot}:FM:DEV {deviation_hz}"
        self.write(command)
        self.logger.info(f"FM频偏: {deviation_hz} Hz")

    def set_fm_frequency(self, freq_hz: float) -> None:
        """
        设置FM调制频率（内部调制源）。
        
        Args:
            freq_hz: 调制频率（Hz）
        
        Ref: EMCenter SCPI Manual p.39
        - FM:INT:FREQ <Hz>: 设置内部调制频率
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen FM调制频率: {freq_hz} Hz")
            return
        
        command = f"{self.slot}:FM:INT:FREQ {freq_hz}"
        self.write(command)
        self.logger.info(f"FM调制频率: {freq_hz} Hz")

    # === 脉冲调制 (Pulse) ===

    def enable_pulse(self, enable: bool) -> None:
        """
        开关脉冲调制。
        
        Args:
            enable: True=开启, False=关闭
        
        Ref: EMCenter SCPI Manual p.50
        - PULSE:STATE ON/OFF: 控制脉冲调制
        """
        state = "ON" if enable else "OFF"
        
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen 脉冲调制: {state}")
            return
        
        command = f"{self.slot}:PULSE:STATE {state}"
        self.write(command)
        self.logger.info(f"脉冲调制: {state}")

    def set_pulse_width(self, width_sec: float) -> None:
        """
        设置脉冲宽度。
        
        Args:
            width_sec: 脉宽（秒）
        
        Ref: EMCenter SCPI Manual p.50
        - PULSE:WIDTH <sec>: 设置脉宽
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMGen 脉宽: {width_sec*1e6:.1f} μs")
            return
        
        command = f"{self.slot}:PULSE:WIDTH {width_sec}"
        self.write(command)
        self.logger.info(f"脉宽: {width_sec*1e6:.1f} μs")

    def set_pulse_period(self, period_sec: float) -> None:
        """
        设置脉冲周期（PRF = 1/period）。
        
        Args:
            period_sec: 周期（秒）
        
        Ref: EMCenter SCPI Manual p.50
        - PULSE:PER <sec>: 设置脉冲周期
        """
        if self.simulation_mode:
            prf = 1.0 / period_sec if period_sec > 0 else 0
            self.logger.info(f"[模拟] EMGen 脉冲周期: {period_sec*1e3:.3f} ms (PRF: {prf:.1f} Hz)")
            return
        
        command = f"{self.slot}:PULSE:PER {period_sec}"
        self.write(command)
        
        prf = 1.0 / period_sec if period_sec > 0 else 0
        self.logger.info(f"脉冲周期: {period_sec*1e3:.3f} ms (PRF: {prf:.1f} Hz)")

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
