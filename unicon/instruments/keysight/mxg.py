"""
Keysight MXG / EXG X-Series Vector Signal Generator Driver.

Ref: X-Series Signal Generators SCPI Command Reference_9018-04210.pdf
"""

from typing import Optional

from unicon.instruments.base_instrument import BaseInstrument


class KeysightMXG(BaseInstrument):
    """
    Keysight MXG (N5182B) 等 X 系列信号发生器驱动。
    """

    def __init__(self, resource_name: str, name: str = "MXG", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)

    def set_frequency(self, freq_hz: float):
        """
        设置中心频率 (Hz)。
        Ref: SCPI Command Reference - [SOURce:]FREQuency[:CW]
        """
        self.logger.info(f"设置频率: {freq_hz} Hz")
        self.write(f":FREQuency {freq_hz}")

    def set_power(self, power_dbm: float):
        """
        设置射频输出功率 (dBm)。
        Ref: SCPI Command Reference - [SOURce:]POWer[:LEVel][:IMMediate][:AMPLitude]
        """
        self.logger.info(f"设置功率: {power_dbm} dBm")
        self.write(f":POWer {power_dbm}")

    def set_rf_output(self, state: bool):
        """
        开启或关闭射频输出。
        Ref: SCPI Command Reference - :OUTPut[:STATe]
        """
        state_str = "ON" if state else "OFF"
        self.logger.info(f"设置射频输出: {state_str}")
        self.write(f":OUTPut {state_str}")

    def set_modulation_state(self, state: bool):
        """
        开启或关闭所有调制。
        Ref: SCPI Command Reference - :OUTPut:MODulation[:STATe]
        """
        state_str = "ON" if state else "OFF"
        self.logger.info(f"设置调制状态: {state_str}")
        self.write(f":OUTPut:MODulation {state_str}")

    def load_arb_waveform(self, waveform_name: str):
        """
        在双基带发生器中选择并加载 ARB 波形文件。
        Ref: SCPI Command Reference - [SOURce:]RADio:ARB:WAVeform
        """
        # 注意：Keysight 仪器内部通常需要指定文件系统路径，例如 "WFM1:my_wave"
        self.logger.info(f"加载 ARB 波形: {waveform_name}")
        self.write(f":RADio:ARB:WAVeform \"WFM1:{waveform_name}\"")

    def set_arb_state(self, state: bool):
        """
        开启或关闭 ARB 基带发生器。
        Ref: SCPI Command Reference - [SOURce:]RADio:ARB[:STATe]
        """
        state_str = "ON" if state else "OFF"
        self.logger.info(f"设置 ARB 状态: {state_str}")
        self.write(f":RADio:ARB {state_str}")
