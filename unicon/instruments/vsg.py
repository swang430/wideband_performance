import logging

from .base_instrument import BaseInstrument
from .common.generic_vsg import GenericVSG
from .factory import DriverFactory


class VSG:
    """
    VSG 代理类 (Proxy)。
    对上层隐藏具体的驱动实现细节。
    根据设备 IDN 自动加载 GenericVSG 或 RS_SMW200A 等专用驱动。
    """

    def __init__(self, resource_name: str, name: str = "VSG_Proxy", simulation_mode: bool = False):
        self.resource_name = resource_name
        self.name = name
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(f"Proxy.{name}")
        self._driver: GenericVSG = None # 实际的驱动实例

    def connect(self):
        """
        连接设备，识别型号，并初始化对应的驱动。
        """
        if self.simulation_mode:
            # 模拟模式下，为了测试 R&S 逻辑，我们可以伪造一个 IDN
            # 或者默认使用通用驱动
            fake_idn = "Rohde&Schwarz,SMW200A,Simulated,1.0"
            self.logger.info(f"[模拟] 识别到 IDN: {fake_idn}")
            self._driver = DriverFactory.create_vsg_driver(self.resource_name, fake_idn, True)
            self._driver.connect()
            return

        try:
            # 1. 使用基础类建立临时连接以查询 IDN
            temp_inst = BaseInstrument(self.resource_name, "Temp_Probe")
            temp_inst.connect()
            idn = temp_inst.query("*IDN?")
            temp_inst.disconnect() # 释放连接，交给专用驱动去连

            self.logger.info(f"设备 IDN: {idn}")

            # 2. 使用工厂创建真正的驱动
            self._driver = DriverFactory.create_vsg_driver(self.resource_name, idn, self.simulation_mode)

            # 3. 连接真正的驱动
            self._driver.connect()

        except Exception as e:
            self.logger.error(f"初始化驱动失败: {e}")
            raise

    def disconnect(self):
        if self._driver:
            self._driver.disconnect()

    # --- 代理方法 (Delegation) ---

    def set_frequency(self, hz: float):
        self._check_driver()
        self._driver.set_frequency(hz)

    def set_power(self, dbm: float):
        self._check_driver()
        self._driver.set_power(dbm)

    def enable_output(self, enable: bool):
        self._check_driver()
        self._driver.enable_output(enable)

    def load_waveform(self, waveform_name: str):
        self._check_driver()
        self._driver.load_waveform(waveform_name)

    def get_driver_info(self) -> dict:
        if self._driver:
            return self._driver.get_driver_info()
        return {"status": "Not Connected", "proxy": "VSG_Proxy"}

    def _check_driver(self):
        if not self._driver:
            raise ConnectionError("VSG 尚未连接或驱动初始化失败")
