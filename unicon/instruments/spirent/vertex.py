"""
Spirent Vertex Channel Emulator Driver.

Ref: RPI_CommandRef.pdf (Remote Programming Interface)
"""

from typing import List, Dict

from unicon.instruments.base_instrument import BaseInstrument


class Vertex(BaseInstrument):
    """
    Spirent Vertex 信道仿真器驱动。
    """

    def __init__(self, resource_name: str, name: str = "Vertex", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)

    def load_scenario(self, scenario_name: str):
        """
        加载预定义或保存的 Workspace/Scenario 拓扑。
        Ref: Vertex RPI Command Reference - :SYSTem:CONFigure:LOAD
        """
        self.logger.info(f"加载 Vertex 仿真场景拓扑: {scenario_name}")
        self.write(f':SYSTem:CONFigure:LOAD "{scenario_name}"')
        # 加载可能需要时间，等待指令结束
        self.query("*OPC?")

    def start_emulation(self):
        """
        启动信道衰落仿真 (Play)。
        Ref: Vertex RPI Command Reference - :SYSTem:PLAY
        """
        self.logger.info("启动信道衰落仿真 (Play)...")
        self.write(":SYSTem:PLAY")
        self.query("*OPC?")

    def stop_emulation(self):
        """
        停止信道衰落仿真 (Stop)。
        Ref: Vertex RPI Command Reference - :SYSTem:STOP
        """
        self.logger.info("停止信道衰落仿真 (Stop)...")
        self.write(":SYSTem:STOP")

    def set_channel_fading_model(self, link_id: str, model_name: str):
        """
        为特定的 Link 分配衰落模型 (Fading Model)。
        Ref: Vertex RPI Command Reference - :CONFigure:LINK<link_id>:FADing:MODel
        """
        self.logger.info(f"设置 Link {link_id} 的衰落模型为: {model_name}")
        self.write(f":CONFigure:LINK{link_id}:FADing:MODel {model_name}")

    def set_awgn_snr(self, port_id: int, snr_db: float):
        """
        在特定的输出端口注入 AWGN 并设置 SNR (信噪比)。
        Ref: Vertex RPI Command Reference - :CONFigure:PORT<port_id>:OUTPut:AWGN:SNR
        """
        self.logger.info(f"设置端口 {port_id} AWGN 注入 SNR = {snr_db} dB")
        # 开启 AWGN
        self.write(f":CONFigure:PORT{port_id}:OUTPut:AWGN:STATe ON")
        # 设置 SNR
        self.write(f":CONFigure:PORT{port_id}:OUTPut:AWGN:SNR {snr_db}")

    def set_port_input_power(self, port_id: int, power_dbm: float):
        """
        设置射频输入端口的期望输入功率级 (Expected Input Power)。
        这用于 Vertex 内部的自动增益控制 (AGC)。
        Ref: Vertex RPI Command Reference - :CONFigure:PORT<port_id>:INPut:EIP
        """
        self.logger.info(f"设置输入端口 {port_id} 期望功率 = {power_dbm} dBm")
        self.write(f":CONFigure:PORT{port_id}:INPut:EIP {power_dbm}")
