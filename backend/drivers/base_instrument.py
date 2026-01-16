import pyvisa
import logging

class BaseInstrument:
    """
    通过 PyVISA 管理的所有仪器的抽象基类。
    """
    def __init__(self, resource_name: str, name: str = "未知仪器", simulation_mode: bool = False, reset_on_connect: bool = True):
        self.resource_name = resource_name
        self.name = name
        self.simulation_mode = simulation_mode
        self.reset_on_connect = reset_on_connect
        self.rm = pyvisa.ResourceManager() if not simulation_mode else None
        self.instrument = None
        self.logger = logging.getLogger(f"仪器.{name}")
        self._connected = False
        self._idn = "Unknown"

    def connect(self):
        """
        连接到仪器并执行标准初始化流程 (IDN -> OPT -> RST -> CLS)。
        """
        if self.simulation_mode:
            self._connected = True
            self.logger.info(f"[模拟] 已连接到 {self.name}，地址: {self.resource_name}")
            self._idn = f"Simulated Vendor, {self.name}, 000000, v1.0"
            self.logger.info(f"身份标识 (IDN): {self._idn}")
            
            if self.reset_on_connect:
                self.logger.info("执行复位 (*RST)...")
                self.logger.info("错误队列已清除 (*CLS)")
            return

        try:
            self.instrument = self.rm.open_resource(self.resource_name)
            self._connected = True
            self.logger.info(f"已连接到 {self.name}，地址: {self.resource_name}")
            
            # 1. 识别 (IDN)
            self._idn = self.query("*IDN?")
            self.logger.info(f"身份标识 (IDN): {self._idn}")
            
            # 2. 选件查询 (OPT)
            try:
                opts = self.query("*OPT?")
                self.logger.info(f"已安装选件 (OPT): {opts}")
            except Exception:
                self.logger.warning("查询选件 (*OPT?) 失败或不支持")

            # 3. 复位与清理 (RST/CLS)
            if self.reset_on_connect:
                self.logger.info("执行复位 (*RST)...")
                self.write("*RST")
                self.query("*OPC?") # 等待复位完成
                
                self.write("*CLS")
                self.logger.info("错误队列已清除 (*CLS)")

        except Exception as e:
            self.logger.error(f"连接 {self.name} 失败: {e}")
            raise

    def get_driver_info(self) -> dict:
        """
        获取驱动元数据信息。
        """
        return {
            "driver_class": self.__class__.__name__,
            "driver_module": self.__class__.__module__,
            "resource_name": self.resource_name,
            "idn": getattr(self, "_idn", "Unknown")
        }

    def disconnect(self):
        """
        断开与仪器的连接。
        """
        if self.instrument:
            try:
                self.instrument.close()
                self._connected = False
                self.logger.info(f"已断开与 {self.name} 的连接")
            except Exception as e:
                self.logger.error(f"断开 {self.name} 连接时出错: {e}")

    def write(self, command: str):
        """
        向仪器写入 SCPI 指令。
        """
        if self.simulation_mode:
            self.logger.debug(f"[模拟] 写入 {self.name}: {command}")
            return

        if not self._connected or not self.instrument:
            raise ConnectionError(f"{self.name} 未连接。")
        try:
            self.instrument.write(command)
            self.logger.debug(f"写入 {self.name}: {command}")
        except Exception as e:
            self.logger.error(f"写入 {self.name} 时出错: {e}")
            raise

    def query(self, command: str) -> str:
        """
        写入指令并读取响应。
        """
        if self.simulation_mode:
            self.logger.debug(f"[模拟] 查询 {self.name}: {command} -> SIM_DATA")
            return "SIM_DATA"

        if not self._connected or not self.instrument:
            raise ConnectionError(f"{self.name} 未连接。")
        try:
            response = self.instrument.query(command)
            self.logger.debug(f"查询 {self.name}: {command} -> {response.strip()}")
            return response.strip()
        except Exception as e:
            self.logger.error(f"查询 {self.name} 时出错: {e}")
            raise

    def reset(self):
        """
        重置仪器到已知状态。
        """
        self.write("*RST")
        self.write("*CLS")
