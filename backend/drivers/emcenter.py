from drivers.common.generic_tcu import GenericTCU


class EMCenter_Driver(GenericTCU):
    """
    EMCenter TCU 专用驱动。
    
    基于 EMCenter SCPI Cmds and Errs RevA 1801188 手册实现。
    
    EMCenter 使用插槽编号 + 命令格式控制继电器开关。
    命令格式: <slot>:<command>
    例如: "4:INT_RELAY_A_1" 表示插槽4的内部继电器A切换到位置1
    
    Ref: EMCenter_SCPI_Cmds_and_Errs_RevA_1801188.pdf
    """

    def __init__(self, resource_name: str, name: str = "EMCenter", simulation_mode: bool = False, slot: int = 4):
        super().__init__(resource_name, name, simulation_mode)
        self.slot = slot  # 默认插槽编号为4，可在配置中指定
        self.logger.info(f"EMCenter TCU 驱动已加载，插槽编号: {self.slot}")

    def switch_rf_path(self, path: str) -> None:
        """
        切换射频通路（EMCenter 特定实现）。
        
        EMCenter 通过内部或外部继电器控制通路。
        path 格式: "RELAY_A_1", "RELAY_B_3", "EXT_RELAY_A_2" 等
        
        Ref: EMCenter SCPI Manual p.8-12
        - INT_RELAY_<R>_<N>: 设置内部继电器A或B到位置0-6
        - EXT_RELAY_<R>_<N>: 设置外部继电器A或B到位置0-6
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMCenter 切换RF通路: {path}")
            return
        
        # 解析path，构建SCPI命令
        # 支持格式: "INT_RELAY_A_1", "EXT_RELAY_B_3" 等
        if path.startswith("INT_") or path.startswith("EXT_"):
            command = f"{self.slot}:{path}"
        else:
            # 如果没有前缀，默认为内部继电器
            command = f"{self.slot}:INT_{path}"
        
        self.write(command)
        self.logger.info(f"切换RF通路: {command}")

    def set_relay_position(self, relay_type: str, relay_id: str, position: int) -> None:
        """
        设置继电器位置（EMCenter 专用方法）。
        
        Args:
            relay_type: "INT_RELAY" 或 "EXT_RELAY"
            relay_id: "A" 或 "B"
            position: 0-6 (0表示全部断开，1-6表示连接到对应端口)
        
        Ref: EMCenter SCPI Manual p.9, p.11-12
        - INT_RELAY_<R>_<N>: 内部继电器 (p.9)
        - EXT_RELAY_<R>_<N>: 外部继电器 (p.11)
        - SP6T卡继电器 (p.12)
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMCenter 设置 {relay_type}_{relay_id} 到位置 {position}")
            return
        
        if relay_type not in ["INT_RELAY", "EXT_RELAY"]:
            raise ValueError(f"不支持的继电器类型: {relay_type}")
        
        if relay_id not in ["A", "B"]:
            raise ValueError(f"继电器ID必须为A或B: {relay_id}")
        
        if not (0 <= position <= 6):
            raise ValueError(f"继电器位置必须在0-6范围内: {position}")
        
        command = f"{self.slot}:{relay_type}_{relay_id}_{position}"
        self.write(command)
        self.logger.info(f"设置继电器: {command}")

    def get_relay_position(self, relay_type: str, relay_id: str) -> int:
        """
        查询继电器位置（EMCenter 专用方法）。
        
        Args:
            relay_type: "INT_RELAY" 或 "EXT_RELAY"
            relay_id: "A" 或 "B"
        
        Returns:
            当前继电器位置 (0-6)
        
        Ref: EMCenter SCPI Manual p.8, p.10
        - INT_RELAY_<R>?: 查询内部继电器状态 (p.8)
        - EXT_RELAY_<R>?: 查询外部继电器状态 (p.10)
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMCenter 查询 {relay_type}_{relay_id} 位置")
            return 1  # 模拟返回位置1
        
        if relay_type not in ["INT_RELAY", "EXT_RELAY"]:
            raise ValueError(f"不支持的继电器类型: {relay_type}")
        
        if relay_id not in ["A", "B"]:
            raise ValueError(f"继电器ID必须为A或B: {relay_id}")
        
        command = f"{self.slot}:{relay_type}_{relay_id}?"
        response = self.query(command)
        
        try:
            position = int(response.strip())
            self.logger.info(f"查询继电器: {command} -> {position}")
            return position
        except ValueError:
            self.logger.error(f"继电器查询返回无效数据: {response}")
            return -1

    def set_attenuation(self, port: str, db: float) -> None:
        """
        设置衰减值（EMCenter 特定实现）。
        
        注意: EMCenter SCPI手册中未找到直接的衰减器控制指令。
        如果EMCenter系统使用外部衰减器，需要通过继电器间接控制。
        
        对于程控衰减器，通常需要外部设备或模块支持。
        
        Ref: EMCenter SCPI Manual - 未找到ATT/ATTEN命令
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMCenter 设置衰减器 {port}: {db} dB")
            return
        
        # EMCenter可能不直接支持衰减控制，使用父类占位实现
        self.logger.warning(f"EMCenter SCPI手册中未找到衰减器指令，端口: {port}, dB: {db}")
        self.logger.warning("如需控制衰减器，请确认系统配置是否包含程控衰减模块")
        super().set_attenuation(port, db)

    def enable_amplifier(self, port: str, enable: bool) -> None:
        """
        开关放大器（EMCenter 特定实现）。
        
        注意: EMCenter SCPI手册中未找到直接的放大器控制指令。
        放大器通常通过继电器控制电源或信号通路实现开关。
        
        建议使用 set_relay_position() 方法控制关联的继电器。
        
        Ref: EMCenter SCPI Manual - 未找到AMP/AMPLIFIER命令
        """
        if self.simulation_mode:
            state = "ON" if enable else "OFF"
            self.logger.info(f"[模拟] EMCenter 放大器 {port}: {state}")
            return
        
        # EMCenter可能不直接支持放大器控制
        self.logger.warning(f"EMCenter SCPI手册中未找到放大器控制指令，端口: {port}")
        self.logger.warning("如需控制放大器，请使用set_relay_position()方法控制关联继电器")
        super().enable_amplifier(port, enable)

    def get_switch_state(self, path: str) -> str:
        """
        查询开关状态（EMCenter 特定实现）。
        
        返回继电器当前位置，格式为字符串。
        
        Ref: EMCenter SCPI Manual p.8, p.10
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMCenter 查询开关状态: {path}")
            return "CONNECTED"
        
        # 解析path，提取继电器类型和ID
        # 假设path格式: "INT_RELAY_A" 或 "EXT_RELAY_B"
        try:
            parts = path.split("_")
            if len(parts) >= 3:
                relay_type = f"{parts[0]}_RELAY"
                relay_id = parts[2]
                position = self.get_relay_position(relay_type, relay_id)
                return f"Position_{position}"
            else:
                self.logger.warning(f"无法解析path格式: {path}")
                return "UNKNOWN"
        except Exception as e:
            self.logger.error(f"查询开关状态失败: {e}")
            return "ERROR"

    def calibrate_path(self, path: str) -> None:
        """
        校准指定通路。
        
        注意: EMCenter SCPI手册中未找到校准相关指令。
        EMSwitch主要用于开关控制，不包含校准功能。
        
        Ref: EMCenter SCPI Manual - 未找到calibrate命令
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMCenter 校准通路: {path}")
            return
        
        self.logger.warning("EMCenter不支持通路校准功能，此方法为占位符")

    # EMCenter 特有的辅助方法
    
    def set_slot(self, slot: int) -> None:
        """
        设置插槽编号。
        
        Args:
            slot: EMSwitch卡在EMCenter机箱中的插槽编号 (通常为1-8)
        """
        if not (1 <= slot <= 8):
            raise ValueError(f"插槽编号必须在1-8范围内: {slot}")
        
        self.slot = slot
        self.logger.info(f"插槽编号设置为: {slot}")

    def get_relay_temperature(self, relay_id: str) -> float:
        """
        获取内部继电器温度（EMSwitch特有功能）。
        
        Args:
            relay_id: "A" 或 "B"
        
        Returns:
            温度值（摄氏度）
        
        Ref: EMCenter SCPI Manual p.9
        - INT_TEMPERATURE_<R>?: 查询内部继电器温度
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] 查询继电器{relay_id}温度")
            return 25.0  # 模拟室温
        
        if relay_id not in ["A", "B"]:
            raise ValueError(f"继电器ID必须为A或B: {relay_id}")
        
        command = f"{self.slot}:INT_TEMPERATURE_{relay_id}?"
        response = self.query(command)
        
        try:
            temp = float(response.strip())
            self.logger.info(f"继电器{relay_id}温度: {temp}°C")
            return temp
        except ValueError:
            self.logger.error(f"温度查询返回无效数据: {response}")
            return -273.15  # 返回绝对零度表示错误
