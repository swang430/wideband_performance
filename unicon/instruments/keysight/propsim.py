"""
Keysight PROPSIM F64 Channel Emulator Driver.

Ref: Propsim User Reference.pdf / Propsim ATE environment and practices AN.pdf
"""

from typing import List

from unicon.instruments.base_instrument import BaseInstrument


class Propsim(BaseInstrument):
    """
    Keysight PROPSIM 信道仿真器驱动。
    侧重于 ATE 模式下的场景加载和基础仿真控制。
    """

    def __init__(self, resource_name: str, name: str = "PROPSIM", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)

    def load_scenario(self, scenario_path: str):
        """
        加载预先在 Channel Studio 生成的 GCM 场景文件。
        Ref: Propsim User Reference - :SYSTem:CONFigure:LOAD
        """
        self.logger.info(f"加载 PROPSIM 场景文件: {scenario_path}")
        self.write(f':SYSTem:CONFigure:LOAD "{scenario_path}"')
        self.query("*OPC?")

    def start_emulation(self):
        """
        启动信道仿真引擎。
        Ref: Propsim User Reference - :SYSTem:SIMulation:RUN
        """
        self.logger.info("启动 PROPSIM 信道仿真...")
        self.write(":SYSTem:SIMulation:RUN")

    def stop_emulation(self):
        """
        停止信道仿真引擎。
        Ref: Propsim User Reference - :SYSTem:SIMulation:STOP
        """
        self.logger.info("停止 PROPSIM 信道仿真...")
        self.write(":SYSTem:SIMulation:STOP")

    def set_awgn_snr(self, link_index: int, snr_db: float):
        """
        为特定链路设置 AWGN 的信噪比 (SNR)。
        Ref: Propsim User Reference - :CONFigure:LINK<n>:AWGN:SNR
        """
        self.logger.info(f"配置链路 {link_index} 的 AWGN SNR: {snr_db} dB")
        self.write(f":CONFigure:LINK{link_index}:AWGN:SNR {snr_db}")
        self.write(f":CONFigure:LINK{link_index}:AWGN:STATe ON")
