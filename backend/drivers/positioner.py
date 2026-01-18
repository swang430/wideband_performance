import logging

from drivers.base_instrument import BaseInstrument


class Positioner:
    """
    定位器/转台 HAL 封装层。
    
    支持EMControl等定位器，用于天线方向图测试等应用。
    """

    def __init__(self, resource_name: str, name: str = "Positioner", 
                 simulation_mode: bool = False, slot: int = 5):
        """
        初始化定位器 HAL。
        
        Args:
            resource_name: VISA 资源地址
            name: 定位器名称
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
        连接到定位器并自动识别型号。
        """
        idn_string = "Unknown"

        if not self.simulation_mode:
            try:
                import pyvisa
                temp_rm = pyvisa.ResourceManager()
                temp_inst = temp_rm.open_resource(self.resource_name)
                idn_string = temp_inst.query("*IDN?").strip()
                temp_inst.close()
                self.logger.info(f"检测到定位器: {idn_string}")
            except Exception as e:
                self.logger.warning(f"无法查询 IDN，使用EMControl驱动: {e}")
                idn_string = "EMControl"
        else:
            idn_string = "Simulated ETS-Lindgren, EMControl 7006-001, v1.0"

        # 使用EMControl驱动
        from drivers.emcontrol import EMControl_Driver
        
        self._driver = EMControl_Driver(
            self.resource_name,
            name=self.name,
            simulation_mode=self.simulation_mode,
            slot=self.slot
        )
        self._driver.connect()
        self.logger.info(f"{self.name} HAL 已就绪")

    def disconnect(self) -> None:
        """
        断开定位器连接。
        """
        if self._driver:
            self._driver.disconnect()

    # --- 基本位置控制 ---

    def move_to(self, position: float, wait: bool = True) -> None:
        """
        移动到目标位置（最短路径）。
        
        Args:
            position: 目标位置（度数或厘米）
            wait: 是否等待移动完成
        """
        if not self._driver:
            raise ConnectionError("定位器未连接")
        
        self._driver.seek_position(position)
        
        if wait and not self.simulation_mode:
            self._wait_for_motion_complete()

    def move_relative(self, offset: float, wait: bool = True) -> None:
        """
        相对当前位置移动。
        
        Args:
            offset: 相对偏移量（正=顺时针/向上，负=逆时针/向下）
            wait: 是否等待移动完成
        """
        if not self._driver:
            raise ConnectionError("定位器未连接")
        
        self._driver.seek_relative(offset)
        
        if wait and not self.simulation_mode:
            self._wait_for_motion_complete()

    def get_position(self) -> float:
        """
        查询当前位置。
        
        Returns:
            当前位置（度数或厘米）
        """
        if self._driver:
            return self._driver.get_current_position()
        else:
            raise ConnectionError("定位器未连接")

    def stop(self) -> None:
        """
        立即停止运动。
        """
        if self._driver:
            self._driver.stop_motion()
        else:
            raise ConnectionError("定位器未连接")

    # --- 运动参数配置 ---

    def set_speed(self, speed: float) -> None:
        """
        设置运动速度。
        
        Args:
            speed: 速度（度/秒或厘米/秒）
        """
        if self._driver:
            self._driver.set_speed(speed)
        else:
            raise ConnectionError("定位器未连接")

    def get_speed(self) -> float:
        """
        查询当前速度。
        
        Returns:
            速度（度/秒或厘米/秒）
        """
        if self._driver:
            return self._driver.get_speed()
        else:
            raise ConnectionError("定位器未连接")

    def set_acceleration(self, accel: float) -> None:
        """
        设置加速度。
        
        Args:
            accel: 加速度值
        """
        if self._driver:
            self._driver.set_acceleration(accel)
        else:
            raise ConnectionError("定位器未连接")

    # --- 状态查询 ---

    def is_moving(self) -> bool:
        """
        查询是否正在运动。
        
        Returns:
            True=运动中, False=静止
        """
        if self._driver:
            direction = self._driver.get_direction()
            return direction != 0
        else:
            raise ConnectionError("定位器未连接")

    def get_motor_status(self) -> int:
        """
        查询马达状态。
        
        Returns:
            状态码（0=正常，其他=异常）
        """
        if self._driver:
            return self._driver.get_motor_status()
        else:
            raise ConnectionError("定位器未连接")

    # --- 高级方法 ---

    def configure_motion(self, speed: float = 10.0, accel: float = 5.0) -> None:
        """
        [高级接口] 配置运动参数。
        
        Args:
            speed: 速度（度/秒或厘米/秒）
            accel: 加速度
        """
        self.logger.info(f"配置运动参数: 速度={speed}, 加速度={accel}")
        self.set_speed(speed)
        self.set_acceleration(accel)

    def scan_range(self, start: float, end: float, step: float, 
                   callback=None, wait_at_each: float = 0.5) -> list:
        """
        [高级接口] 扫描指定范围。
        
        Args:
            start: 起始位置（度）
            end: 结束位置（度）
            step: 步进（度）
            callback: 每个位置执行的回调函数（接收位置参数）
            wait_at_each: 每个位置的等待时间（秒）
        
        Returns:
            所有位置的列表
        """
        import time
        
        self.logger.info(f"扫描范围: {start}° -> {end}°, 步进={step}°")
        
        positions = []
        current = start
        
        while (step > 0 and current <= end) or (step < 0 and current >= end):
            # 移动到位置
            self.move_to(current, wait=True)
            positions.append(current)
            
            # 等待稳定
            if wait_at_each > 0:
                time.sleep(wait_at_each)
            
            # 执行回调
            if callback:
                try:
                    callback(current)
                except Exception as e:
                    self.logger.error(f"回调执行失败（位置={current}°）: {e}")
            
            current += step
        
        self.logger.info(f"扫描完成，共 {len(positions)} 个位置")
        return positions

    def scan_antenna_pattern(self, start_deg: float = 0.0, end_deg: float = 360.0,
                            step_deg: float = 10.0, measure_callback=None) -> dict:
        """
        [高级接口] 天线方向图扫描。
        
        Args:
            start_deg: 起始角度（度）
            end_deg: 结束角度（度）
            step_deg: 角度步进（度）
            measure_callback: 测量回调函数（接收角度，返回测量值）
        
        Returns:
            {angle: measurement} 字典
        """
        self.logger.info(f"开始天线方向图扫描: {start_deg}° - {end_deg}°, 步进={step_deg}°")
        
        results = {}
        
        def scan_callback(angle):
            if measure_callback:
                try:
                    value = measure_callback(angle)
                    results[angle] = value
                    self.logger.info(f"  角度 {angle}°: {value}")
                except Exception as e:
                    self.logger.error(f"测量失败（角度={angle}°）: {e}")
        
        self.scan_range(start_deg, end_deg, step_deg, callback=scan_callback)
        
        self.logger.info(f"方向图扫描完成，共 {len(results)} 个数据点")
        return results

    def home(self, home_position: float = 0.0) -> None:
        """
        [高级接口] 回归初始位置。
        
        Args:
            home_position: 初始位置（度数或厘米），默认0
        """
        self.logger.info(f"回归初始位置: {home_position}")
        self.move_to(home_position, wait=True)

    # --- 内部辅助方法 ---

    def _wait_for_motion_complete(self, timeout_sec: float = 60.0) -> None:
        """
        等待运动完成。
        
        Args:
            timeout_sec: 超时时间（秒）
        """
        import time
        
        start_time = time.time()
        
        while self.is_moving():
            if time.time() - start_time > timeout_sec:
                self.logger.error("运动超时，强制停止")
                self.stop()
                raise TimeoutError("定位器运动超时")
            
            time.sleep(0.1)  # 100ms轮询间隔
        
        # 再等待一小段时间确保稳定
        time.sleep(0.2)
