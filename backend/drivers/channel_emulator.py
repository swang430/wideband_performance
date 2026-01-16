import logging

from .base_instrument import BaseInstrument
from .common.generic_ce import GenericChannelEmulator
from .factory import DriverFactory


class ChannelEmulator:
    """
    信道模拟器代理类 (Proxy)。
    """
    def __init__(self, resource_name: str, name: str = "ChanEm_Proxy", simulation_mode: bool = False):
        self.resource_name = resource_name
        self.name = name
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger(f"Proxy.{name}")
        self._driver: GenericChannelEmulator = None

    def connect(self):
        if self.simulation_mode:
            # 模拟 Keysight PROPSIM F64
            fake_idn = "Keysight,PROPSIM F64,Simulated,v10.2"
            self.logger.info(f"[模拟] 识别到 IDN: {fake_idn}")
            self._driver = DriverFactory.create_chan_em_driver(self.resource_name, fake_idn, True)
            self._driver.connect()
            return

        try:
            temp_inst = BaseInstrument(self.resource_name, "Temp_Probe")
            temp_inst.connect()
            idn = temp_inst.query("*IDN?")
            temp_inst.disconnect()

            self.logger.info(f"设备 IDN: {idn}")
            self._driver = DriverFactory.create_chan_em_driver(self.resource_name, idn, self.simulation_mode)
            self._driver.connect()
        except Exception as e:
            self.logger.error(f"初始化驱动失败: {e}")
            raise

    def disconnect(self):
        if self._driver: self._driver.disconnect()

    def get_driver_info(self) -> dict:
        if self._driver: return self._driver.get_driver_info()
        return {"status": "Not Connected", "proxy": "ChanEm_Proxy"}

    def load_channel_model(self, model: str):
        self._check(); self._driver.load_channel_model(model)

    def set_input_power(self, power_dbm: float):
        self._check(); self._driver.set_input_power(power_dbm)

    def set_output_power(self, power_dbm: float):
        self._check(); self._driver.set_output_power(power_dbm)

    def set_velocity(self, kmh: float):
        self._check(); self._driver.set_velocity(kmh)

    def rf_on(self):
        self._check(); self._driver.rf_on()

    def rf_off(self):
        self._check(); self._driver.rf_off()

    # === 场景测试扩展方法 ===

    def set_path_loss(self, db: float):
        """设置路径损耗 (dB)"""
        self._check(); self._driver.set_path_loss(db)

    def set_distance(self, km: float):
        """设置模拟距离 (km)"""
        self._check(); self._driver.set_distance(km)

    def set_fading_profile(self, profile: str, duration_ms: int = 0):
        """设置衰落配置 (用于深衰落事件模拟)"""
        self._check(); self._driver.set_fading_profile(profile, duration_ms)

    def trigger_handover(self, target_cell: int):
        """触发小区切换"""
        self._check(); self._driver.trigger_handover(target_cell)

    def _check(self):
        if not self._driver: raise ConnectionError("Channel Emulator 尚未连接")
