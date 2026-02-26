import logging
import time
from typing import Optional

import pyvisa


class BaseInstrument:
    """
    通过 PyVISA 管理的所有仪器的抽象基类。
    提供重试机制、超时控制和模拟模式。
    """
    def __init__(self, resource_name: str, name: str = "未知仪器", simulation_mode: bool = False, 
                 reset_on_connect: bool = True, timeout_ms: int = 10000, max_retries: int = 3):
        self.resource_name = resource_name
        self.name = name
        self.simulation_mode = simulation_mode
        self.reset_on_connect = reset_on_connect
        self.timeout_ms = timeout_ms
        self.max_retries = max_retries
        
        self.rm = pyvisa.ResourceManager() if not simulation_mode else None
        self.instrument: Optional[pyvisa.resources.Resource] = None
        self.logger = logging.getLogger(f"仪器.{name}")
        self._connected = False
        self._idn = "Unknown"

    def connect(self):
        """
        连接到仪器并执行标准初始化流程 (IDN -> OPT -> RST -> CLS)。
        支持带指数退避的重试机制。
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

        for attempt in range(1, self.max_retries + 1):
            try:
                self.instrument = self.rm.open_resource(self.resource_name)
                self.instrument.timeout = self.timeout_ms
                self._connected = True
                self.logger.info(f"已连接到 {self.name}，地址: {self.resource_name} (尝试 {attempt}/{self.max_retries})")

                # 1. 识别 (IDN)
                self._idn = self.query("*IDN?", retry=False)
                self.logger.info(f"身份标识 (IDN): {self._idn}")

                # 2. 选件查询 (OPT)
                try:
                    opts = self.query("*OPT?", retry=False)
                    self.logger.info(f"已安装选件 (OPT): {opts}")
                except Exception:
                    self.logger.debug("查询选件 (*OPT?) 失败或不支持")

                # 3. 复位与清理 (RST/CLS)
                if self.reset_on_connect:
                    self.logger.info("执行复位 (*RST)...")
                    self.write("*RST", retry=False)
                    self.query("*OPC?", retry=False) # 等待复位完成
                    self.write("*CLS", retry=False)
                    self.logger.info("错误队列已清除 (*CLS)")
                return  # 成功连接并初始化，退出循环

            except pyvisa.VisaIOError as e:
                self.logger.warning(f"连接 {self.name} 失败 (VisaIOError): {e} (尝试 {attempt}/{self.max_retries})")
                if attempt == self.max_retries:
                    self.logger.error(f"连接 {self.name} 最终失败，已达到最大重试次数。")
                    raise
                time.sleep(2 ** attempt)  # 指数退避: 2s, 4s, 8s...
            except Exception as e:
                self.logger.error(f"连接 {self.name} 时发生未知错误: {e}")
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
        if self.simulation_mode:
            self._connected = False
            self.logger.info(f"[模拟] 已断开与 {self.name} 的连接")
            return
            
        if self.instrument:
            try:
                self.instrument.close()
                self._connected = False
                self.logger.info(f"已断开与 {self.name} 的连接")
            except Exception as e:
                self.logger.error(f"断开 {self.name} 连接时出错: {e}")

    def write(self, command: str, retry: bool = True):
        """
        向仪器写入 SCPI 指令，支持重试。
        """
        if self.simulation_mode:
            if hasattr(self.logger, "trace"):
                self.logger.trace(f"[模拟] 写入 {self.name}: {command}")
            else:
                self.logger.debug(f"[模拟] 写入 {self.name}: {command}")
            return

        if not self._connected or not self.instrument:
            raise ConnectionError(f"{self.name} 未连接。")
            
        retries = self.max_retries if retry else 1
        for attempt in range(1, retries + 1):
            try:
                self.instrument.write(command)
                if hasattr(self.logger, "trace"):
                    self.logger.trace(f"写入 {self.name}: {command}")
                else:
                    self.logger.debug(f"写入 {self.name}: {command}")
                return
            except pyvisa.VisaIOError as e:
                self.logger.warning(f"写入 {self.name} 超时或失败: {command} (尝试 {attempt}/{retries}) - {e}")
                if attempt == retries:
                    self.logger.error(f"写入 {self.name} 最终失败: {command}")
                    raise
                time.sleep(0.5 * attempt)
            except Exception as e:
                self.logger.error(f"写入 {self.name} 时发生未知错误: {e}")
                raise

    def query(self, command: str, retry: bool = True) -> str:
        """
        写入指令并读取响应，支持重试。
        """
        if self.simulation_mode:
            if "STATe?" in command:
                response = "ON"
            elif "CSState?" in command:
                response = "ASSOCIATED"
            elif "PSWitched:STATe?" in command:
                response = "ATT"
            elif "*IDN?" in command:
                response = "Simulated Instrument"
            elif "RDY" in command or "STATe?" in command:
                response = "RDY"
            else:
                response = "SIM_DATA"
            if hasattr(self.logger, "trace"):
                self.logger.trace(f"[模拟] 查询 {self.name}: {command} -> {response}")
            else:
                self.logger.debug(f"[模拟] 查询 {self.name}: {command} -> {response}")
            return response

        if not self._connected or not self.instrument:
            raise ConnectionError(f"{self.name} 未连接。")
            
        retries = self.max_retries if retry else 1
        for attempt in range(1, retries + 1):
            try:
                response = self.instrument.query(command)
                response = response.strip()
                if hasattr(self.logger, "trace"):
                    self.logger.trace(f"查询 {self.name}: {command} -> {response}")
                else:
                    self.logger.debug(f"查询 {self.name}: {command} -> {response}")
                return response
            except pyvisa.VisaIOError as e:
                self.logger.warning(f"查询 {self.name} 超时或失败: {command} (尝试 {attempt}/{retries}) - {e}")
                if attempt == retries:
                    self.logger.error(f"查询 {self.name} 最终失败: {command}")
                    raise
                time.sleep(0.5 * attempt)
            except Exception as e:
                self.logger.error(f"查询 {self.name} 时发生未知错误: {e}")
                raise

    def reset(self):
        """
        重置仪器到已知状态。
        """
        self.write("*RST")
        self.write("*CLS")

    def check_system_errors(self) -> list[str]:
        """
        抽干并返回仪器内部的系统错误队列 (System Error Queue)。
        """
        errors = []
        if self.simulation_mode:
            return errors
            
        while True:
            # 标准的 SCPI 错误查询命令
            err = self.query("SYSTem:ERRor?", retry=False)
            if not err or '0,"No error"' in err or '0,"NO ERROR"' in err or '+0,"No error"' in err:
                break
            errors.append(err)
            
        if errors:
            self.logger.error(f"检测到系统错误: {errors}")
        return errors

