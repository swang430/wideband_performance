"""
Rohde & Schwarz FSW Signal and Spectrum Analyzer Driver.

Ref: FSW_UserManual.htm
"""

from typing import List, Tuple

from unicon.instruments.base_instrument import BaseInstrument


class FSW(BaseInstrument):
    """
    R&S FSW 信号与频谱分析仪驱动。
    侧重于通用频谱扫描 (Spectrum) 以及 IQ 数据抓取。
    """

    def __init__(self, resource_name: str, name: str = "FSW", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)

    def set_frequency_center(self, freq_hz: float):
        """
        设置频谱仪的中心频率 (Hz)。
        Ref: FSW User Manual - [SENSe:]FREQuency:CENTer
        """
        self.logger.info(f"设置中心频率: {freq_hz} Hz")
        self.write(f"SENSe:FREQuency:CENTer {freq_hz}")

    def set_span(self, span_hz: float):
        """
        设置频谱仪的扫频宽度 (Hz)。
        Ref: FSW User Manual - [SENSe:]FREQuency:SPAN
        """
        self.logger.info(f"设置 Span: {span_hz} Hz")
        self.write(f"SENSe:FREQuency:SPAN {span_hz}")

    def set_reference_level(self, level_dbm: float):
        """
        设置参考电平 (Reference Level)。
        Ref: FSW User Manual - DISPlay[:WINDow<n>][:SUBWindow<w>]:TRACe<t>:Y[:SCALe]:RLEVel
        """
        self.logger.info(f"设置参考电平: {level_dbm} dBm")
        self.write(f"DISPlay:WINDow:TRACe:Y:SCALe:RLEVel {level_dbm}")

    def run_single_sweep(self):
        """
        执行单次扫描并等待完成 (阻塞式)。
        Ref: FSW User Manual - INITiate:IMMediate
        """
        self.logger.info("执行单次扫描...")
        # 取消连续扫描
        self.write("INITiate:CONTinuous OFF")
        # 触发单次扫描并发送 *WAI 等待完成
        self.write("INITiate:IMMediate; *WAI")
        self.logger.info("单次扫描完成。")

    def perform_peak_search(self) -> Tuple[float, float]:
        """
        执行 Peak Search (最大峰值搜索) 并读取 Marker 1 的 X(Hz) 和 Y(dBm)。
        Ref: FSW User Manual - CALCulate<n>:MARKer<m>:MAXimum[:PEAK]
        
        :return: (频率 Hz, 功率 dBm)
        """
        self.logger.info("执行 Peak Search (Marker 1)...")
        if self.simulation_mode:
            return (2.4e9, -15.2)

        # 移动 Marker1 到峰值
        self.write("CALCulate:MARKer1:MAXimum:PEAK")
        
        # 读取 X (频率)
        x_val = float(self.query("CALCulate:MARKer1:X?"))
        # 读取 Y (幅度)
        y_val = float(self.query("CALCulate:MARKer1:Y?"))
        
        self.logger.info(f"Peak 结果 -> Freq: {x_val} Hz, Power: {y_val} dBm")
        return (x_val, y_val)

    def fetch_trace_data_binary(self, trace: int = 1) -> bytes:
        """
        以 IEEE 488.2 明确定义的二进制块 (REAL,32) 格式获取 Trace 数据，速度比 ASCII 快。
        Ref: FSW User Manual - FORMat[:DATA] REAL,32
        """
        self.logger.info(f"读取 Trace {trace} 二进制数据...")
        if self.simulation_mode:
            return b'#41600' + b'\x00'*1600  # 模拟二进制块头部和数据
            
        # 设置传输格式为 REAL,32 (32-bit 浮点数)
        self.write("FORMat:DATA REAL,32")
        # 针对特定的 Trace 抓取数据
        self.write(f"TRACe:DATA? TRACE{trace}")
        
        if not self.instrument:
            raise ConnectionError("FSW 未连接")
            
        # 因为是二进制数据，这里必须绕过 query，使用底层的 read_raw
        try:
            raw_data = self.instrument.read_raw()
            return raw_data
        except Exception as e:
            self.logger.error(f"读取二进制 Trace 失败: {e}")
            raise
        finally:
            # 读取完毕后恢复为 ASCII 以免影响其他常用指令
            self.write("FORMat:DATA ASCii")
