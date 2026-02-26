"""
Rohde & Schwarz CMW500 Wideband Radio Communication Tester Driver
WLAN Signaling & Measurement Implementation.

Ref: CMW_WLAN_UserManual_V4-0-20_en.pdf
"""

from typing import Optional, Dict
import time

from unicon.instruments.base_instrument import BaseInstrument


class CMW500(BaseInstrument):
    """
    R&S CMW500 综测仪驱动程序。
    目前侧重于 WLAN (Wi-Fi) 信令与测量模式的控制。
    """
    
    def __init__(self, resource_name: str, name: str = "CMW500", simulation_mode: bool = False, reset_on_connect: bool = True):
        super().__init__(resource_name, name=name, simulation_mode=simulation_mode, reset_on_connect=reset_on_connect)
        self.wlan = self.WlanSubsystem(self)
        self.lte = self.LteSubsystem(self)

    class LteSubsystem:
        """LTE Signaling Subsystem"""
        def __init__(self, parent: 'CMW500'):
            self.parent = parent
            self.logger = parent.logger

        def set_routing(self, scenario: str = "STANdard", rf_in: str = "RF1C", rf_out: str = "RF1C"):
            """
            配置 LTE 信令的射频路由和场景模式。
            Ref: CMW LTE UE User Manual - ROUTe:LTE:SIGNaling...
            """
            self.logger.info(f"配置 LTE 路由: 场景={scenario}, RF_IN={rf_in}, RF_OUT={rf_out}")
            self.parent.write(f"ROUTe:LTE:SIGNaling:SCENario:MODe {scenario}")
            self.parent.write(f"ROUTe:LTE:SIGNaling:TX {rf_out}")
            self.parent.write(f"ROUTe:LTE:SIGNaling:RX {rf_in}")

        def configure_rf(self, band: str = "OB1", dl_channel: int = 300, tx_power_dbm: float = -40.0, ext_att_in: float = 0.0, ext_att_out: float = 0.0):
            """
            配置 LTE 射频参数。
            Ref: CMW LTE UE User Manual - CONFigure:LTE:SIGNaling:BAND...
            """
            self.logger.info(f"配置 LTE 射频: 频段={band}, DL_CH={dl_channel}, 功率={tx_power_dbm} dBm")
            self.parent.write(f"CONFigure:LTE:SIGNaling:BAND {band}")
            self.parent.write(f"CONFigure:LTE:SIGNaling:RFSettings:CHANnel:DL {dl_channel}")
            
            self.parent.write(f"CONFigure:LTE:SIGNaling:RFSettings:EATTenuation:INPut {ext_att_in}")
            self.parent.write(f"CONFigure:LTE:SIGNaling:RFSettings:EATTenuation:OUTPut {ext_att_out}")
            self.parent.write(f"CONFigure:LTE:SIGNaling:RFSettings:LEVel:RSEPre {tx_power_dbm}")

        def configure_network(self, bandwidth: str = "B050", cell_id: int = 1):
            """
            配置 LTE 小区网络参数。
            Ref: CMW LTE UE User Manual - CONFigure:LTE:SIGNaling:CELL...
            
            :param bandwidth: 信道带宽 (B014=1.4MHz, B030=3MHz, B050=5MHz, B100=10MHz, B150=15MHz, B200=20MHz)
            """
            self.logger.info(f"配置 LTE 网络: Bandwidth={bandwidth}, Cell ID={cell_id}")
            self.parent.write(f"CONFigure:LTE:SIGNaling:CELL:BANDwidth:DL {bandwidth}")
            self.parent.write(f"CONFigure:LTE:SIGNaling:CELL:PCID {cell_id}")

        def start_signaling(self) -> bool:
            """
            开启 LTE 信令小区 (Cell ON)。
            Ref: CMW LTE UE User Manual - SOURce:LTE:SIGNaling:CELL:STATe
            """
            self.logger.info("开启 LTE 小区 (Cell ON)...")
            self.parent.write("SOURce:LTE:SIGNaling:CELL:STATe ON")
            
            timeout = 10
            start_time = time.time()
            while time.time() - start_time < timeout:
                state = self.parent.query("SOURce:LTE:SIGNaling:CELL:STATe?")
                if "ON" in state.upper():
                    self.logger.info("LTE 小区已成功开启。")
                    return True
                time.sleep(0.5)
            
            self.logger.error("开启 LTE 小区超时！")
            return False

        def get_connection_state(self) -> str:
            """
            查询当前 DUT 的分组交换连接状态。
            Ref: CMW LTE UE User Manual - FETCh:LTE:SIGNaling:PSWitched:STATe?
            """
            state = self.parent.query("FETCh:LTE:SIGNaling:PSWitched:STATe?")
            self.logger.debug(f"当前 LTE PS 连接状态: {state}")
            return state

        def wait_for_connection(self, timeout: float = 30.0) -> bool:
            """
            等待终端成功附着 (ATTACHED) 到 LTE 小区。
            """
            self.logger.info(f"等待终端附着到 LTE 网络，最大超时时间: {timeout} 秒...")
            start_time = time.time()
            while time.time() - start_time < timeout:
                state = self.get_connection_state()
                if "ATT" in state.upper():
                    self.logger.info("终端已成功附着 (ATTACHED)！")
                    return True
                time.sleep(1.0)
            
            self.logger.warning("等待终端附着超时。")
            return False

    class WlanSubsystem:
        """WLAN Signaling & Measurement Subsystem"""
        def __init__(self, parent: 'CMW500'):
            self.parent = parent
            self.logger = parent.logger

        def set_routing(self, scenario: str = "STANdard", rf_in: str = "RF1C", rf_out: str = "RF1C"):
            """
            配置 WLAN 信令的射频路由和场景模式。
            Ref: CMW WLAN User Manual - ROUTe:WLAN:SIGNaling...
            """
            self.logger.info(f"配置 WLAN 路由: 场景={scenario}, RF_IN={rf_in}, RF_OUT={rf_out}")
            # 设置基本信令场景
            self.parent.write(f"ROUTe:WLAN:SIGNaling:SCENario:MODe {scenario}")
            # 配置 TX/RX 端口
            self.parent.write(f"ROUTe:WLAN:SIGNaling:TX {rf_out}")
            self.parent.write(f"ROUTe:WLAN:SIGNaling:RX {rf_in}")

        def configure_rf(self, band: str = "OB24", channel: int = 6, tx_power_dbm: float = -10.0, ext_att_in: float = 0.0, ext_att_out: float = 0.0):
            """
            配置 WLAN 的射频参数（频段、信道、发射功率、外部衰减）。
            Ref: CMW WLAN User Manual - CONFigure:WLAN:SIGNaling:RFSettings...
            
            :param band: 频段 (OB24 -> 2.4 GHz, OB50 -> 5 GHz, OB60 -> 6 GHz)
            :param channel: 信道号
            :param tx_power_dbm: CMW500 TX 输出功率 (dBm)
            :param ext_att_in: RF 输入路径的外部线损 (dB)
            :param ext_att_out: RF 输出路径的外部线损 (dB)
            """
            self.logger.info(f"配置 WLAN 射频: 频段={band}, 信道={channel}, 功率={tx_power_dbm} dBm")
            # 设置频段和信道
            self.parent.write(f"CONFigure:WLAN:SIGNaling:BAND {band}")
            self.parent.write(f"CONFigure:WLAN:SIGNaling:RFSettings:CHANnel {channel}")
            
            # 设置外部衰减 (External Attenuation)
            self.parent.write(f"CONFigure:WLAN:SIGNaling:RFSettings:EATTenuation:INPut {ext_att_in}")
            self.parent.write(f"CONFigure:WLAN:SIGNaling:RFSettings:EATTenuation:OUTPut {ext_att_out}")
            
            # 设置下行 TX 功率
            self.parent.write(f"CONFigure:WLAN:SIGNaling:RFSettings:LEVel {tx_power_dbm}")

        def configure_network(self, ssid: str, standard: str = "N", bandwidth: str = "BW20"):
            """
            配置 WLAN 接入点 (AP) 的网络参数。
            Ref: CMW WLAN User Manual - CONFigure:WLAN:SIGNaling:CONNection...
            
            :param ssid: AP 的 SSID 名称
            :param standard: WLAN 标准 (A, B, G, N, AC, AX, BE)
            :param bandwidth: 信道带宽 (BW20, BW40, BW80, BW160)
            """
            self.logger.info(f"配置 WLAN 网络: SSID={ssid}, Standard=802.11{standard}, 带宽={bandwidth}")
            # 设置网络标准 (例如 11n, 11ac)
            self.parent.write(f"CONFigure:WLAN:SIGNaling:CONNection:STANdard {standard}")
            # 设置信道带宽
            self.parent.write(f"CONFigure:WLAN:SIGNaling:CONNection:Bwidth {bandwidth}")
            # 设置 SSID
            self.parent.write(f"CONFigure:WLAN:SIGNaling:CONNection:SSID '{ssid}'")

        def start_signaling(self) -> bool:
            """
            开启 WLAN 信令源 (Turn on the AP)。
            Ref: CMW WLAN User Manual - SOURce:WLAN:SIGNaling:STATe
            """
            self.logger.info("开启 WLAN 信令源 (AP 启动)...")
            self.parent.write("SOURce:WLAN:SIGNaling:STATe ON")
            
            # 等待直到状态变为 ON
            timeout = 10
            start_time = time.time()
            while time.time() - start_time < timeout:
                state = self.parent.query("SOURce:WLAN:SIGNaling:STATe?")
                if "ON" in state.upper():
                    self.logger.info("WLAN 信令源已成功开启。")
                    return True
                time.sleep(0.5)
            
            self.logger.error("开启 WLAN 信令源超时！")
            return False

        def stop_signaling(self):
            """
            关闭 WLAN 信令源。
            Ref: CMW WLAN User Manual - SOURce:WLAN:SIGNaling:STATe
            """
            self.logger.info("关闭 WLAN 信令源 (AP 停止)...")
            self.parent.write("SOURce:WLAN:SIGNaling:STATe OFF")

        def get_connection_state(self) -> str:
            """
            查询当前 DUT 的连接状态。
            Ref: CMW WLAN User Manual - FETCh:WLAN:SIGNaling:CSState?
            
            返回示例: "OFF", "ON", "ASSOCIATED"
            """
            state = self.parent.query("FETCh:WLAN:SIGNaling:CSState?")
            self.logger.debug(f"当前 WLAN 连接状态: {state}")
            return state

        def wait_for_connection(self, timeout: float = 30.0) -> bool:
            """
            等待终端 (DUT) 成功关联 (ASSOCIATED) 到 CMW500。
            """
            self.logger.info(f"等待终端连接，最大超时时间: {timeout} 秒...")
            start_time = time.time()
            while time.time() - start_time < timeout:
                state = self.get_connection_state()
                if "ASS" in state.upper():
                    self.logger.info("终端已成功连接 (ASSOCIATED)！")
                    return True
                time.sleep(1.0)
            
            self.logger.warning("等待终端连接超时。")
            return False

        # --- Measurements (EVM, Power) ---

        def start_measurement(self) -> bool:
            """
            启动 WLAN 多项评估测量 (Multi Evaluation Measurement)。
            Ref: CMW WLAN User Manual - INITiate:WLAN:MEAS:MEValuation
            """
            self.logger.info("启动 WLAN 测量 (Multi Evaluation)...")
            self.parent.write("INITiate:WLAN:MEAS:MEValuation")
            
            # 等待测量 Ready
            timeout = 10
            start_time = time.time()
            while time.time() - start_time < timeout:
                state = self.parent.query("FETCh:WLAN:MEAS:MEValuation:STATe?")
                if "RDY" in state.upper():
                    self.logger.info("WLAN 测量已就绪 (READY)。")
                    return True
                time.sleep(0.5)
                
            self.logger.error("WLAN 测量就绪超时！")
            return False

        def stop_measurement(self):
            """
            停止 WLAN 测量。
            Ref: CMW WLAN User Manual - STOP:WLAN:MEAS:MEValuation
            """
            self.logger.info("停止 WLAN 测量...")
            self.parent.write("STOP:WLAN:MEAS:MEValuation")

        def fetch_evm(self) -> Dict[str, float]:
            """
            获取 WLAN EVM 测量结果。
            Ref: CMW WLAN User Manual - FETCh:WLAN:MEAS:MEValuation:EVM:ALL?
            
            :return: 包含 EVM 均值、最大值等参数的字典
            """
            self.logger.info("读取 WLAN EVM 测量结果...")
            res = self.parent.query("FETCh:WLAN:MEAS:MEValuation:EVM:ALL?")
            
            if self.parent.simulation_mode:
                return {"evm_avg_db": -35.2, "evm_max_db": -31.4}
                
            # 解析返回的逗号分隔字符串
            # 示例响应: Reliability, EVM_Current, EVM_Min, EVM_Max, EVM_Avg ...
            try:
                parts = [float(x) for x in res.split(",")]
                reliability = parts[0]
                if reliability != 0:
                    self.logger.warning(f"测量可能无效，Reliability Indicator: {reliability}")
                
                # 根据 CMW500 返回格式，一般情况下 4 是 Avg, 3 是 Max
                return {
                    "reliability": reliability,
                    "evm_avg_db": parts[4] if len(parts) > 4 else float('nan'),
                    "evm_max_db": parts[3] if len(parts) > 3 else float('nan')
                }
            except Exception as e:
                self.logger.error(f"解析 EVM 结果失败: {e} (Raw: {res})")
                return {}

        def fetch_tx_power(self) -> Dict[str, float]:
            """
            获取 WLAN 发射功率 (TX Power) 测量结果。
            Ref: CMW WLAN User Manual - FETCh:WLAN:MEAS:MEValuation:POWer:ALL?
            """
            self.logger.info("读取 WLAN TX Power 测量结果...")
            res = self.parent.query("FETCh:WLAN:MEAS:MEValuation:POWer:ALL?")
            
            if self.parent.simulation_mode:
                return {"power_avg_dbm": 15.4, "power_max_dbm": 16.1}
                
            try:
                parts = [float(x) for x in res.split(",")]
                reliability = parts[0]
                if reliability != 0:
                    self.logger.warning(f"测量可能无效，Reliability Indicator: {reliability}")
                
                return {
                    "reliability": reliability,
                    "power_avg_dbm": parts[4] if len(parts) > 4 else float('nan'),
                    "power_max_dbm": parts[3] if len(parts) > 3 else float('nan')
                }
            except Exception as e:
                self.logger.error(f"解析 TX Power 结果失败: {e} (Raw: {res})")
                return {}

        # --- RX / Throughput / PER Tests ---

        def configure_rx_test(self, num_packets: int = 1000, payload_length_bytes: int = 1000):
            """
            配置 WLAN RX 测试 (例如 PER 测试) 的发包参数。
            Ref: CMW WLAN User Manual - CONFigure:WLAN:SIGNaling:TX:MAC:PAYLoad...
            """
            self.logger.info(f"配置 RX 测试: 包数={num_packets}, Payload大小={payload_length_bytes} Bytes")
            # 设置下行 MAC Payload 的包数 (Number of packets to send)
            self.parent.write(f"CONFigure:WLAN:SIGNaling:TX:MAC:PACKets {num_packets}")
            # 设置每个 Payload 的长度
            self.parent.write(f"CONFigure:WLAN:SIGNaling:TX:MAC:PAYLoad:LENGth {payload_length_bytes}")

        def start_rx_test(self):
            """
            开始向终端发送下行数据包 (Start Downlink Packet Transmission)。
            Ref: CMW WLAN User Manual - INITiate:WLAN:SIGNaling:TX:MAC:PACKets
            """
            self.logger.info("启动 RX 数据包发送...")
            self.parent.write("INITiate:WLAN:SIGNaling:TX:MAC:PACKets")

        def fetch_per(self) -> Dict[str, float]:
            """
            获取由 CMW500 统计的 WLAN PER (Packet Error Rate) / 吞吐量。
            注意：部分高级统计可能需要特殊的信令配置或外部 iPerf。
            Ref: CMW WLAN User Manual - FETCh:WLAN:SIGNaling:RX:MAC:PER?
            """
            self.logger.info("获取 RX PER 结果...")
            res = self.parent.query("FETCh:WLAN:SIGNaling:RX:MAC:PER?")
            
            if self.parent.simulation_mode:
                return {"per_percent": 0.5, "packets_sent": 1000, "packets_acked": 995}

            try:
                parts = [float(x) for x in res.split(",")]
                reliability = parts[0]
                if reliability != 0:
                    self.logger.warning(f"测量可能无效，Reliability Indicator: {reliability}")
                
                # CMW500 PER 返回通常包含: Reliability, PER, Sent, Acked 等
                return {
                    "reliability": reliability,
                    "per_percent": parts[1] if len(parts) > 1 else float('nan'),
                    "packets_sent": parts[2] if len(parts) > 2 else float('nan'),
                    "packets_acked": parts[3] if len(parts) > 3 else float('nan')
                }
            except Exception as e:
                self.logger.error(f"解析 PER 结果失败: {e} (Raw: {res})")
                return {}
