import logging

from drivers.base_instrument import BaseInstrument
from drivers.factory import DriverFactory


class TCU:
    """
    TCU (Test Config Unit) HAL 封装层。
    
    负责控制射频开关、探头、放大器、功分器、双工器等RF器件。
    通过工厂自动识别TCU型号并加载对应驱动。
    """

    def __init__(self, resource_name: str, name: str = "TCU", simulation_mode: bool = False):
        """
        初始化 TCU HAL。
        
        Args:
            resource_name: VISA 资源地址
            name: TCU 名称
            simulation_mode: 是否启用模拟模式
        """
        self.resource_name = resource_name
        self.name = name
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(f"HAL.{name}")
        self._driver: BaseInstrument = None

    def connect(self) -> None:
        """
        连接到 TCU 并自动识别型号。
        """
        # 创建临时连接获取 IDN
        temp_rm = None
        idn_string = "Unknown"

        if not self.simulation_mode:
            try:
                import pyvisa
                temp_rm = pyvisa.ResourceManager()
                temp_inst = temp_rm.open_resource(self.resource_name)
                idn_string = temp_inst.query("*IDN?").strip()
                temp_inst.close()
                self.logger.info(f"检测到 TCU: {idn_string}")
            except Exception as e:
                self.logger.warning(f"无法查询 IDN，使用通用驱动: {e}")
                idn_string = "Generic"
        else:
            idn_string = "Simulated EMCenter,TCU-1000,SN000000,v1.0"

        # 使用工厂创建驱动
        self._driver = DriverFactory.create_tcu_driver(
            self.resource_name,
            idn_string,
            self.simulation_mode
        )
        self._driver.connect()
        self.logger.info(f"{self.name} HAL 已就绪")

    def disconnect(self) -> None:
        """
        断开 TCU 连接。
        """
        if self._driver:
            self._driver.disconnect()

    # --- 标准接口方法（委托到底层驱动） ---

    def switch_rf_path(self, path: str) -> None:
        """
        切换射频通路。
        
        Args:
            path: 通路标识符，如 "ANT1_TO_DUT"
        """
        if self._driver:
            self._driver.switch_rf_path(path)
        else:
            raise ConnectionError("TCU 未连接")

    def set_attenuation(self, port: str, db: float) -> None:
        """
        设置衰减器。
        
        Args:
            port: 端口标识符，如 "ATT1"
            db: 衰减值（dB）
        """
        if self._driver:
            self._driver.set_attenuation(port, db)
        else:
            raise ConnectionError("TCU 未连接")

    def enable_amplifier(self, port: str, enable: bool) -> None:
        """
        开关放大器。
        
        Args:
            port: 放大器端口，如 "AMP1"
            enable: True=开启, False=关闭
        """
        if self._driver:
            self._driver.enable_amplifier(port, enable)
        else:
            raise ConnectionError("TCU 未连接")

    def get_switch_state(self, path: str) -> str:
        """
        查询开关状态。
        
        Args:
            path: 通路标识符
        
        Returns:
            状态字符串
        """
        if self._driver:
            return self._driver.get_switch_state(path)
        else:
            raise ConnectionError("TCU 未连接")

    # --- 高级封装方法 ---

    def configure_test_path(self, source: str, destination: str, attenuation_db: float = 0.0) -> None:
        """
        [高级接口] 配置完整测试通路。
        
        一步完成：切换通路 + 设置衰减。
        
        Args:
            source: 信号源端口，如 "VSG_OUT"
            destination: 目标端口，如 "DUT_IN"
            attenuation_db: 通路衰减（dB），默认0
        """
        path_name = f"{source}_TO_{destination}"
        self.logger.info(f"配置测试通路: {path_name}, 衰减: {attenuation_db} dB")
        
        self.switch_rf_path(path_name)
        
        if attenuation_db > 0:
            # 假设衰减器命名为 ATT_<PATH>，实际需根据硬件配置调整
            att_port = f"ATT_{source}"
            self.set_attenuation(att_port, attenuation_db)

    def reset_all_switches(self) -> None:
        """
        [高级接口] 复位所有开关到初始状态。
        
        具体实现取决于 TCU 硬件，可能需要查询当前状态并逐一断开。
        """
        self.logger.info("复位所有开关到初始状态")
        # TODO: 根据 TCU 能力实现（可能需要手册确认是否有全局复位指令）
        if self._driver and hasattr(self._driver, 'reset'):
            self._driver.reset()
        else:
            self.logger.warning("TCU 驱动不支持 reset() 方法")
