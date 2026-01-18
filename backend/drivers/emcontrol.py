from drivers.base_instrument import BaseInstrument


class EMControl_Driver(BaseInstrument):
    """
    EMCenter EMControl 定位器/转台控制驱动 (7006-001)。
    
    支持转台、塔架、混响室搅拌器等定位设备的控制。
    
    Ref: EMCenter_SCPI_Cmds_and_Errs_RevA_1801188.pdf p.53-75
    """

    def __init__(self, resource_name: str, name: str = "EMControl", simulation_mode: bool = False, slot: int = 5):
        super().__init__(resource_name, name, simulation_mode, reset_on_connect=False)
        self.slot = slot  # 默认插槽5
        self.logger.info(f"EMControl 定位器控制驱动已加载，插槽: {self.slot}")

    def seek_position(self, position: float) -> None:
        """
        移动到目标位置（最短路径）。
        
        Args:
            position: 目标位置（度数/厘米）
        
        Ref: EMCenter SCPI Manual p.64
        - SK <pos>: 移动到目标位置
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMControl 移动到: {position}")
            return
        
        command = f"{self.slot}:SK {position}"
        self.write(command)
        self.logger.info(f"移动到位置: {position}")

    def seek_negative(self, position: float) -> None:
        """
        逆时针/向下移动到目标位置。
        
        Args:
            position: 目标位置（度数/厘米）
        
        Ref: EMCenter SCPI Manual p.64
        - SKN <pos>: 逆时针移动到目标
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMControl 逆时针移动到: {position}")
            return
        
        command = f"{self.slot}:SKN {position}"
        self.write(command)
        self.logger.info(f"逆时针移动到: {position}")

    def seek_positive(self, position: float) -> None:
        """
        顺时针/向上移动到目标位置。
        
        Args:
            position: 目标位置（度数/厘米）
        
        Ref: EMCenter SCPI Manual p.65
        - SKP <pos>: 顺时针移动到目标
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMControl 顺时针移动到: {position}")
            return
        
        command = f"{self.slot}:SKP {position}"
        self.write(command)
        self.logger.info(f"顺时针移动到: {position}")

    def seek_relative(self, offset: float) -> None:
        """
        相对当前位置移动。
        
        Args:
            offset: 相对偏移量（正=顺时针/向上，负=逆时针/向下）
        
        Ref: EMCenter SCPI Manual p.65
        - SKR <offset>: 相对移动
        """
        if self.simulation_mode:
            direction = "顺时针" if offset > 0 else "逆时针"
            self.logger.info(f"[模拟] EMControl {direction}移动: {abs(offset)}")
            return
        
        command = f"{self.slot}:SKR {offset}"
        self.write(command)
        self.logger.info(f"相对移动: {offset}")

    def get_current_position(self) -> float:
        """
        查询当前位置。
        
        Returns:
            当前位置（度数或厘米）
        
        Ref: EMCenter SCPI Manual p.57
        - CP?: 查询当前位置
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMControl 查询位置")
            return 0.0
        
        command = f"{self.slot}:CP?"
        response = self.query(command)
        
        try:
            # 响应格式: "100.2 CM" 或 "200.5 DEGREES"
            position = float(response.split()[0])
            unit = response.split()[1] if len(response.split()) > 1 else ""
            self.logger.info(f"当前位置: {position} {unit}")
            return position
        except (ValueError, IndexError) as e:
            self.logger.error(f"位置查询失败: {response}, 错误: {e}")
            return 0.0

    def set_current_position(self, position: float) -> None:
        """
        设置当前位置值（不移动，仅重新定义坐标）。
        
        Args:
            position: 新的位置值
        
        Ref: EMCenter SCPI Manual p.57
        - CP <pos>: 改变当前位置值
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMControl 重定义位置为: {position}")
            return
        
        command = f"{self.slot}:CP {position}"
        self.write(command)
        self.logger.info(f"位置重定义为: {position}")

    def set_speed(self, speed: float) -> None:
        """
        设置运动速度。
        
        Args:
            speed: 速度（厘米/秒或度/秒）
        
        Ref: EMCenter SCPI Manual p.63
        - S <speed>: 设置速度
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMControl 设置速度: {speed}")
            return
        
        command = f"{self.slot}:S {speed}"
        self.write(command)
        self.logger.info(f"设置速度: {speed}")

    def get_speed(self) -> float:
        """
        查询当前速度。
        
        Returns:
            速度（厘米/秒或度/秒）
        
        Ref: EMCenter SCPI Manual p.63
        - S?: 查询速度
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMControl 查询速度")
            return 10.0
        
        command = f"{self.slot}:S?"
        response = self.query(command)
        
        try:
            speed = float(response.strip())
            self.logger.info(f"当前速度: {speed}")
            return speed
        except ValueError as e:
            self.logger.error(f"速度查询失败: {response}, 错误: {e}")
            return 0.0

    def set_acceleration(self, accel: float) -> None:
        """
        设置加速度。
        
        Args:
            accel: 加速度值
        
        Ref: EMCenter SCPI Manual p.56
        - A <accel>: 设置加速度
        """
        if self.simulation_mode:
            self.logger.info(f"[模拟] EMControl 设置加速度: {accel}")
            return
        
        command = f"{self.slot}:A {accel}"
        self.write(command)
        self.logger.info(f"设置加速度: {accel}")

    def get_acceleration(self) -> float:
        """
        查询加速度。
        
        Returns:
            加速度值
        
        Ref: EMCenter SCPI Manual p.56
        - A?: 查询加速度
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMControl 查询加速度")
            return 1.0
        
        command = f"{self.slot}:A?"
        response = self.query(command)
        
        try:
            accel = float(response.strip())
            self.logger.info(f"当前加速度: {accel}")
            return accel
        except ValueError as e:
            self.logger.error(f"加速度查询失败: {response}, 错误: {e}")
            return 0.0

    def get_direction(self) -> int:
        """
        查询运动方向。
        
        Returns:
            运动方向
                0 = 静止
                1 = 顺时针/向上
                -1 = 逆时针/向下
        
        Ref: EMCenter SCPI Manual p.59
        - DIR?: 查询方向
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMControl 查询方向")
            return 0
        
        command = f"{self.slot}:DIR?"
        response = self.query(command)
        
        try:
            direction = int(response.strip())
            dir_names = {0: "静止", 1: "顺时针/向上", -1: "逆时针/向下"}
            self.logger.info(f"运动方向: {dir_names.get(direction, str(direction))}")
            return direction
        except ValueError as e:
            self.logger.error(f"方向查询失败: {response}, 错误: {e}")
            return 0

    def get_motor_status(self) -> int:
        """
        查询马达状态。
        
        Returns:
            状态码
                0 = 正常
                1 = 位置限位错误
                2 = 马达不动（卡住）
                3 = 马达不停
                等等（参见手册p.60）
        
        Ref: EMCenter SCPI Manual p.60
        - M?: 查询马达状态
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMControl 查询马达状态")
            return 0
        
        command = f"{self.slot}:M?"
        response = self.query(command)
        
        try:
            status = int(response.strip())
            if status == 0:
                self.logger.info("马达状态: 正常")
            else:
                self.logger.warning(f"马达状态: 异常 (代码 {status})")
            return status
        except ValueError as e:
            self.logger.error(f"马达状态查询失败: {response}, 错误: {e}")
            return -1

    def stop_motion(self) -> None:
        """
        立即停止运动。
        
        Ref: EMCenter SCPI Manual p.66+
        - STOP: 停止运动
        """
        if self.simulation_mode:
            self.logger.info("[模拟] EMControl 停止运动")
            return
        
        command = f"{self.slot}:STOP"
        self.write(command)
        self.logger.info("运动已停止")

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
