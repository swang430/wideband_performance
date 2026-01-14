import logging
from .base_instrument import BaseInstrument
from .factory import DriverFactory
from .common.generic_tester import GenericTester

class IntegratedTester:
    """
    综测仪代理类 (Proxy)。
    """
    def __init__(self, resource_name: str, name: str = "Tester_Proxy", simulation_mode: bool = False):
        self.resource_name = resource_name
        self.name = name
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(f"Proxy.{name}")
        self._driver: GenericTester = None

    def connect(self):
        if self.simulation_mode:
            fake_idn = "Rohde&Schwarz,CMW,Simulated,1.0"
            self.logger.info(f"[模拟] 识别到 IDN: {fake_idn}")
            self._driver = DriverFactory.create_tester_driver(self.resource_name, fake_idn, True)
            self._driver.connect()
            return

        try:
            temp_inst = BaseInstrument(self.resource_name, "Temp_Probe")
            temp_inst.connect()
            idn = temp_inst.query("*IDN?")
            temp_inst.disconnect()
            
            self.logger.info(f"设备 IDN: {idn}")
            self._driver = DriverFactory.create_tester_driver(self.resource_name, idn, self.simulation_mode)
            self._driver.connect()
        except Exception as e:
            self.logger.error(f"初始化驱动失败: {e}")
            raise

    def disconnect(self):
        if self._driver: self._driver.disconnect()

    def set_tech_standard(self, standard: str):
        self._check(); self._driver.set_tech_standard(standard)

    def start_call(self):
        self._check(); self._driver.start_call()

    def stop_call(self):
        self._check(); self._driver.stop_call()

    def get_connection_status(self) -> str:
        self._check(); return self._driver.get_connection_status()

    def get_driver_info(self) -> dict:
        if self._driver: return self._driver.get_driver_info()
        return {"status": "Not Connected", "proxy": "Tester_Proxy"}

    # === 场景测试扩展方法 ===

    def start_signaling(self, tech: str = "NR"):
        """启动信令连接"""
        self._check(); self._driver.start_signaling(tech)

    def stop_signaling(self):
        """停止信令连接"""
        self._check(); self._driver.stop_signaling()

    def get_throughput(self) -> float:
        """获取当前吞吐量 (Mbps)"""
        self._check(); return self._driver.get_throughput()

    def get_bler(self) -> float:
        """获取当前 BLER"""
        self._check(); return self._driver.get_bler()

    def get_rsrp(self) -> float:
        """获取 RSRP (dBm)"""
        self._check(); return self._driver.get_rsrp()

    def get_sinr(self) -> float:
        """获取 SINR (dB)"""
        self._check(); return self._driver.get_sinr()

    def configure_cell(self, freq_hz: float, bandwidth_mhz: float, power_dbm: float):
        """配置小区参数"""
        self._check(); self._driver.configure_cell(freq_hz, bandwidth_mhz, power_dbm)

    def trigger_handover(self, target_config: dict):
        """触发小区切换"""
        self._check(); self._driver.trigger_handover(target_config)

    def _check(self):
        if not self._driver: raise ConnectionError("Tester 尚未连接")