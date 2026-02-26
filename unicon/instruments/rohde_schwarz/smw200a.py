"""
Rohde & Schwarz SMW200A Vector Signal Generator Driver.

Ref: SMW200A Vector Signal Generator User Manual
"""

from typing import Optional

from unicon.instruments.base_instrument import BaseInstrument


class SMW200A(BaseInstrument):
    """
    R&S SMW200A 矢量信号发生器驱动程序。
    支持双通道 (Path A / Path B) 控制和 AWGN 噪声注入。
    """

    def __init__(self, resource_name: str, name: str = "SMW200A", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)

    def set_frequency(self, freq_hz: float, channel: int = 1):
        """
        设置特定通道的射频频率。
        Ref: SMW User Manual - [SOURce<hw>:]FREQuency:CW
        
        :param channel: 1 对应 Path A, 2 对应 Path B
        """
        self.logger.info(f"设置通道 {channel} 频率: {freq_hz} Hz")
        self.write(f"SOURce{channel}:FREQuency:CW {freq_hz}")

    def set_power(self, power_dbm: float, channel: int = 1):
        """
        设置特定通道的输出功率。
        Ref: SMW User Manual - [SOURce<hw>:]POWer:POWer
        """
        self.logger.info(f"设置通道 {channel} 功率: {power_dbm} dBm")
        self.write(f"SOURce{channel}:POWer:POWer {power_dbm}")

    def set_rf_output(self, state: bool, channel: int = 1):
        """
        开启或关闭特定通道的射频输出。
        Ref: SMW User Manual - OUTPut<hw>:STATe
        """
        state_str = "ON" if state else "OFF"
        self.logger.info(f"设置通道 {channel} 射频输出: {state_str}")
        self.write(f"OUTPut{channel}:STATe {state_str}")

    def load_arb_waveform(self, waveform_path: str, channel: int = 1):
        """
        在特定通道的 ARB 基带中加载波形文件。
        Ref: SMW User Manual - [SOURce<hw>:]BB:ARBitrary:WAVeform:SELect
        """
        # 如果不是绝对路径，默认指向 /var/user/
        if not waveform_path.startswith("/"):
            waveform_path = f"/var/user/{waveform_path}"
        if not waveform_path.endswith(".wv"):
            waveform_path += ".wv"
            
        self.logger.info(f"通道 {channel} 加载 ARB 波形: {waveform_path}")
        self.write(f"SOURce{channel}:BB:ARBitrary:WAVeform:SELect '{waveform_path}'")

    def set_arb_state(self, state: bool, channel: int = 1):
        """
        开启或关闭特定通道的 ARB。
        Ref: SMW User Manual - [SOURce<hw>:]BB:ARBitrary:STATe
        """
        state_str = "ON" if state else "OFF"
        self.logger.info(f"设置通道 {channel} ARB 状态: {state_str}")
        self.write(f"SOURce{channel}:BB:ARBitrary:STATe {state_str}")

    def set_awgn_state(self, state: bool, channel: int = 1):
        """
        开启或关闭 AWGN 噪声发生器。
        Ref: SMW User Manual - [SOURce<hw>:]AWGN:STATe
        """
        state_str = "ON" if state else "OFF"
        self.logger.info(f"设置通道 {channel} AWGN 状态: {state_str}")
        self.write(f"SOURce{channel}:AWGN:STATe {state_str}")

    def set_awgn_snr(self, snr_db: float, channel: int = 1):
        """
        配置 AWGN 发生器的信噪比 (SNR)。
        Ref: SMW User Manual - [SOURce<hw>:]AWGN:SNR
        """
        self.logger.info(f"设置通道 {channel} AWGN SNR: {snr_db} dB")
        # 必须先将模式设为 ADD (即信号 + 噪声)
        self.write(f"SOURce{channel}:AWGN:MODE ADD")
        self.write(f"SOURce{channel}:AWGN:SNR {snr_db}")
