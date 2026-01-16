import logging

from .base_instrument import BaseInstrument
from .common.generic_sa import GenericSA
from .factory import DriverFactory


class SpectrumAnalyzer:
    """
    频谱仪代理类 (Proxy)。
    """
    def __init__(self, resource_name: str, name: str = "SA_Proxy", simulation_mode: bool = False):
        self.resource_name = resource_name
        self.name = name
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(f"Proxy.{name}")
        self._driver: GenericSA = None

    def connect(self):
        if self.simulation_mode:
            # 模拟 FSW
            fake_idn = "Rohde&Schwarz,FSW,Simulated,1.0"
            self.logger.info(f"[模拟] 识别到 IDN: {fake_idn}")
            self._driver = DriverFactory.create_sa_driver(self.resource_name, fake_idn, True)
            self._driver.connect()
            return

        try:
            temp_inst = BaseInstrument(self.resource_name, "Temp_Probe")
            temp_inst.connect()
            idn = temp_inst.query("*IDN?")
            temp_inst.disconnect()

            self.logger.info(f"设备 IDN: {idn}")
            self._driver = DriverFactory.create_sa_driver(self.resource_name, idn, self.simulation_mode)
            self._driver.connect()
        except Exception as e:
            self.logger.error(f"初始化驱动失败: {e}")
            raise

    def disconnect(self):
        if self._driver: self._driver.disconnect()

    def set_center_frequency(self, frequency_hz: float):
        self._check(); self._driver.set_center_frequency(frequency_hz)

    def set_span(self, span_hz: float):
        self._check(); self._driver.set_span(span_hz)

    def set_reference_level(self, level_dbm: float):
        self._check(); self._driver.set_reference_level(level_dbm)

    def set_resolution_bandwidth(self, rbw_hz: float):
        self._check(); self._driver.set_resolution_bandwidth(rbw_hz)

    def get_peak_amplitude(self) -> float:
        self._check(); return self._driver.get_peak_amplitude()

    def get_trace_data(self) -> list:
        self._check(); return self._driver.get_trace_data()

    def get_driver_info(self) -> dict:
        if self._driver: return self._driver.get_driver_info()
        return {"status": "Not Connected", "proxy": "SA_Proxy"}

    def _check(self):
        if not self._driver: raise ConnectionError("SA 尚未连接")
