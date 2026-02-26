"""
Keysight ENA Vector Network Analyzer Driver.

Ref: E5071C ENA Network Analyzer Programmers Guide_9018-01309.pdf
"""

from typing import List

from unicon.instruments.base_instrument import BaseInstrument


class ENA(BaseInstrument):
    """
    Keysight E5071C 等 ENA 系列网络分析仪驱动。
    """

    def __init__(self, resource_name: str, name: str = "ENA", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)

    def set_sweep_points(self, points: int):
        """
        设置信道 1 的扫描点数。
        Ref: ENA Programmer's Guide - :SENSe{[1]-36}:SWEep:POINts <numeric>
        """
        self.logger.info(f"设置扫描点数: {points}")
        self.write(f":SENSe1:SWEep:POINts {points}")

    def set_frequency_range(self, start_hz: float, stop_hz: float):
        """
        设置信道 1 的起始和终止频率 (Hz)。
        Ref: ENA Programmer's Guide - :SENSe{[1]-36}:FREQuency:STARt, :STOP
        """
        self.logger.info(f"设置频率范围: {start_hz} Hz - {stop_hz} Hz")
        self.write(f":SENSe1:FREQuency:STARt {start_hz}")
        self.write(f":SENSe1:FREQuency:STOP {stop_hz}")

    def set_s_parameter(self, trace: int = 1, parameter: str = "S21"):
        """
        定义 Trace 测量的 S 参数类型。
        Ref: ENA Programmer's Guide - :CALCulate{[1]-36}:PARameter{[1]-36}:DEFine <string>
        """
        self.logger.info(f"设置 Trace {trace} 测量参数: {parameter}")
        self.write(f":CALCulate1:PARameter{trace}:DEFine {parameter}")

    def run_single_sweep(self):
        """
        执行单次扫描并等待。
        Ref: ENA Programmer's Guide - :INITiate{[1]-36}:IMMediate
        """
        self.logger.info("执行单次网络扫描...")
        # 开启触发源为总线 (Bus) 或手动，避免自由连续运行
        self.write(":TRIGger:SOURce BUS")
        self.write(":INITiate1:CONTinuous OFF")
        # 发送触发并阻塞直到完成 (OPC)
        self.query(":TRIGger:SINGle; *OPC?")
        self.logger.info("单次扫描完成。")

    def fetch_formatted_data(self, trace: int = 1) -> List[float]:
        """
        获取 Trace 的格式化数据数组 (FDATa)。
        Ref: ENA Programmer's Guide - :CALCulate{[1]-36}:SELected:DATA:FDATa
        """
        self.logger.info(f"读取 Trace {trace} 的格式化数据...")
        if self.simulation_mode:
            return [-10.0, -10.5, -11.0, -10.8] * 10 # 伪造 40 个点

        # 确保选中了对应的 trace
        self.write(f":CALCulate1:PARameter{trace}:SELect")
        # 默认返回的是 ASCII 逗号分隔的数组 (包含实部和虚部交替，如果是 FDATa 则视显示格式而定)
        res = self.query(":CALCulate1:SELected:DATA:FDATa?")
        try:
            # 数据通常为 val1, 0, val2, 0 ... 的格式
            raw_data = [float(x) for x in res.split(",")]
            # 取出有效数据点 (奇数位)
            return raw_data[::2]
        except Exception as e:
            self.logger.error(f"解析网络分析仪数据失败: {e} (Raw: {res[:50]}...)")
            return []

    def set_calibration_state(self, state: bool, channel: int = 1):
        """
        开启或关闭错误校正 (Calibration Correction)。
        Ref: ENA Programmer's Guide - :SENSe{[1]-36}:CORRection:STATe
        """
        state_str = "ON" if state else "OFF"
        self.logger.info(f"设置通道 {channel} 校正状态: {state_str}")
        self.write(f":SENSe{channel}:CORRection:STATe {state_str}")

    def load_state_file(self, file_path: str):
        """
        加载包含校准数据和测试设置的状态文件 (.sta 或 .csa)。
        Ref: ENA Programmer's Guide - :MMEMory:LOAD:STATe
        """
        self.logger.info(f"加载 ENA 状态文件: {file_path}")
        self.write(f':MMEMory:LOAD:STATe "{file_path}"')
        self.query("*OPC?")
