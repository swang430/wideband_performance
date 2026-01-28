"""
Rohde & Schwarz CMW500 综合测试仪驱动（增强版）

本驱动支持 5G NR FR1 (Sub-6GHz) 射频一致性测试，基于 3GPP TS 38.521-1 规范需求。
所有 SCPI 指令均基于 R&S 标准命令结构和官方文档研究。

Ref: backend/manual_library/integrated_tester/Rohde_and_Schwarz_CMW/
     - _info_Rohde_Schwarz_1201_0002K55_101395_UT_Manual_2022819133542.pdf
     - Remote_Control_SCPI_GettingStarted_en_04.pdf
"""

import re
from typing import Optional

from drivers.common.generic_tester import GenericTester


class CMW500_Driver(GenericTester):
    """
    Rohde & Schwarz CMW500 专用驱动（生产级）
    
    支持的功能：
    - 5G NR 小区配置（频率、带宽、子载波间隔）
    - 下行功率控制（RS EPRE、OCNG）
    - 信令控制（附着、去附着、数据激活）
    - 实时测量（吞吐量、BLER、RSRP、SINR）
    """
    scpi_catalog_id = "rohde_schwarz_cmw_wlan"

    def __init__(self, resource_name: str, name: str = "RS_CMW500", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)
        self._tech_mode: str = "UNKNOWN"  # 跟踪当前技术制式
        self._cell_config: dict = {}  # 缓存小区配置状态
        self._wlan_sign_index = 1
        self._wlan_station_index = 1

    # ============================================================================
    # Phase 1: 基础小区配置
    # ============================================================================

    def configure_nr_cell(
        self,
        freq_dl_hz: float,
        freq_ul_hz: float,
        bandwidth_mhz: int,
        subcarrier_spacing_khz: int,
        pci: int = 1
    ) -> None:
        """
        配置 5G NR 小区基础参数
        
        Args:
            freq_dl_hz: 下行中心频率 (Hz)，如 3.5e9 for 3.5 GHz
            freq_ul_hz: 上行中心频率 (Hz)，TDD 模式下与 DL 相同
            bandwidth_mhz: 信道带宽 (MHz)，支持 5/10/20/50/100
            subcarrier_spacing_khz: 子载波间隔 (kHz)，支持 15/30/60
            pci: 物理小区 ID，范围 0-1007
        
        Raises:
            ValueError: 参数超出有效范围
        
        SCPI Commands (基于 R&S 标准模式和网络研究):
            - CONFigure:NR5G:SIGN:CELL:PCC:FREQuency <freq_hz>
            - CONFigure:NR5G:SIGN:CELL:BANDwidth:NOMinal <bw_mhz>
            - CONFigure:NR5G:SIGN:CELL:SUBCARRIER:SPACing <scs_khz>
            - CONFigure:NR5G:SIGN:CELL:PCIDentity <pci>
        
        Ref: 基于 CMW500 SCPI 层级结构推断，待手册验证
        """
        # 参数验证
        valid_bw = [5, 10, 20, 50, 100]
        valid_scs = [15, 30, 60]
        
        if bandwidth_mhz not in valid_bw:
            raise ValueError(f"带宽必须为 {valid_bw} MHz 之一")
        if subcarrier_spacing_khz not in valid_scs:
            raise ValueError(f"子载波间隔必须为 {valid_scs} kHz 之一")
        if not (0 <= pci <= 1007):
            raise ValueError("PCI 必须在 0-1007 范围内")
        
        # 配置下行频率
        cmd_freq_dl = f"CONF:NR5G:SIGN:CELL:PCC:FREQ {freq_dl_hz}"
        self.write(cmd_freq_dl)
        self.logger.info(f"CMW500: 设置 NR DL 频率 = {freq_dl_hz/1e6:.1f} MHz")
        
        # 配置上行频率（TDD 模式通常与 DL 相同）
        cmd_freq_ul = f"CONF:NR5G:SIGN:CELL:PCC:FREQ:UL {freq_ul_hz}"
        self.write(cmd_freq_ul)
        
        # 配置带宽
        cmd_bw = f"CONF:NR5G:SIGN:CELL:BAND:NOM {bandwidth_mhz}MHz"
        self.write(cmd_bw)
        self.logger.info(f"CMW500: 设置带宽 = {bandwidth_mhz} MHz")
        
        # 配置子载波间隔
        cmd_scs = f"CONF:NR5G:SIGN:CELL:SUBC:SPAC {subcarrier_spacing_khz}kHz"
        self.write(cmd_scs)
        self.logger.info(f"CMW500: 设置 SCS = {subcarrier_spacing_khz} kHz")
        
        # 配置物理小区 ID
        cmd_pci = f"CONF:NR5G:SIGN:CELL:PCID {pci}"
        self.write(cmd_pci)
        self.logger.info(f"CMW500: 设置 PCI = {pci}")
        
        # 缓存配置
        self._cell_config.update({
            "freq_dl_hz": freq_dl_hz,
            "freq_ul_hz": freq_ul_hz,
            "bandwidth_mhz": bandwidth_mhz,
            "scs_khz": subcarrier_spacing_khz,
            "pci": pci
        })
        self._tech_mode = "NR5G"

    # ============================================================================
    # WLAN Support
    # ============================================================================

    def set_wlan_indices(self, sign_index: int = 1, station_index: int = 1) -> None:
        """Set default WLAN signaling and station indices used in SCPI templates."""
        self._wlan_sign_index = int(sign_index)
        self._wlan_station_index = int(station_index)

    def configure_wlan(
        self,
        standard: Optional[str] = None,
        ssid: Optional[str] = None,
        channel: Optional[int] = None,
        frequency_hz: Optional[float] = None,
        bandwidth_mhz: Optional[int] = None,
        tx_power_dbm: Optional[float] = None,
        security_type: Optional[str] = None,
        passphrase: Optional[str] = None,
        sign_index: Optional[int] = None,
    ) -> None:
        """
        Configure WLAN signaling settings (AP/STA common configuration).

        SCPI (from CMW WLAN User Manual):
            - CONFigure:WLAN:SIGN<i>:CONNection:STANdard
            - CONFigure:WLAN:SIGN<i>:CONNection:SSID
            - CONFigure:WLAN:SIGN<i>:RFSettings:CHANnel
            - CONFigure:WLAN:SIGN<i>:RFSettings:FREQuency
            - CONFigure:WLAN:SIGN<i>:RFSettings:OCWidth
            - CONFigure:WLAN:SIGN<i>:RFSettings:BOPower
            - CONFigure:WLAN:SIGN<i>:CONNection:SECurity:TYPE
            - CONFigure:WLAN:SIGN<i>:CONNection:SECurity:PASSphrase
        """
        i = sign_index if sign_index is not None else self._wlan_sign_index

        if standard:
            self.write(f"CONFigure:WLAN:SIGN{i}:CONNection:STANdard {standard}")
        if ssid:
            self.write(f"CONFigure:WLAN:SIGN{i}:CONNection:SSID \"{ssid}\"")
        if channel is not None:
            self.write(f"CONFigure:WLAN:SIGN{i}:RFSettings:CHANnel {int(channel)}")
        if frequency_hz is not None:
            self.write(f"CONFigure:WLAN:SIGN{i}:RFSettings:FREQuency {float(frequency_hz)}")
        if bandwidth_mhz is not None:
            self.write(f"CONFigure:WLAN:SIGN{i}:RFSettings:OCWidth {int(bandwidth_mhz)}")
        if tx_power_dbm is not None:
            self.write(f"CONFigure:WLAN:SIGN{i}:RFSettings:BOPower {float(tx_power_dbm)}")
        if security_type:
            self.write(f"CONFigure:WLAN:SIGN{i}:CONNection:SECurity:TYPE {security_type}")
        if passphrase:
            self.write(f"CONFigure:WLAN:SIGN{i}:CONNection:SECurity:PASSphrase \"{passphrase}\"")

        self._tech_mode = "WLAN"

    def start_wlan_signaling(self, sign_index: Optional[int] = None, connect_station: bool = True) -> None:
        i = sign_index if sign_index is not None else self._wlan_sign_index
        self.write(f"SOURce:WLAN:SIGN{i}:STATe ON")
        if connect_station:
            self.write(f"CALL:WLAN:SIGN{i}:ACTion:STATion:CONNect")

    def stop_wlan_signaling(self, sign_index: Optional[int] = None, disconnect_station: bool = True) -> None:
        i = sign_index if sign_index is not None else self._wlan_sign_index
        if disconnect_station:
            self.write(f"CALL:WLAN:SIGN{i}:STA{self._wlan_station_index}:ACTion:DISConnect")
        self.write(f"SOURce:WLAN:SIGN{i}:STATe OFF")

    def start_wlan_per(self, sign_index: Optional[int] = None) -> None:
        i = sign_index if sign_index is not None else self._wlan_sign_index
        self.write(f"INITiate:WLAN:SIGN{i}:PER")

    def stop_wlan_per(self, sign_index: Optional[int] = None) -> None:
        i = sign_index if sign_index is not None else self._wlan_sign_index
        self.write(f"STOP:WLAN:SIGN{i}:PER")

    def read_wlan_per(self, sign_index: Optional[int] = None) -> float:
        i = sign_index if sign_index is not None else self._wlan_sign_index
        result = self.query(f"READ:WLAN:SIGN{i}:PER?")
        return self._parse_numeric(result)

    def get_wlan_data_rate(self, sign_index: Optional[int] = None, station_index: Optional[int] = None) -> float:
        if self.simulation_mode:
            import random
            return 200.0 + random.uniform(-30, 30)
        i = sign_index if sign_index is not None else self._wlan_sign_index
        s = station_index if station_index is not None else self._wlan_station_index
        result = self.query(f"SENSe:WLAN:SIGN{i}:STA{s}:UESinfo:DRATe?")
        return self._parse_numeric(result)

    def get_wlan_rx_power(self, sign_index: Optional[int] = None, station_index: Optional[int] = None) -> float:
        if self.simulation_mode:
            import random
            return -45.0 + random.uniform(-5, 5)
        i = sign_index if sign_index is not None else self._wlan_sign_index
        s = station_index if station_index is not None else self._wlan_station_index
        result = self.query(f"SENSe:WLAN:SIGN{i}:STA{s}:UESinfo:RXBPower?")
        return self._parse_numeric(result)

    def get_wlan_metrics(
        self,
        sign_index: Optional[int] = None,
        station_index: Optional[int] = None,
    ) -> dict:
        i = sign_index if sign_index is not None else self._wlan_sign_index
        s = station_index if station_index is not None else self._wlan_station_index

        if self.simulation_mode:
            import random
            return {
                "wlan_data_rate_mbps": 200.0 + random.uniform(-30, 30),
                "wlan_per": max(0.0, min(1.0, 0.02 + random.uniform(-0.01, 0.01))),
                "wlan_rx_power_dbm": -45.0 + random.uniform(-5, 5),
                "wlan_connection_status": "SIM",
            }

        metrics = {
            "wlan_data_rate_mbps": self.get_wlan_data_rate(i, s),
            "wlan_per": self.read_wlan_per(i),
            "wlan_rx_power_dbm": self.get_wlan_rx_power(i, s),
            "wlan_connection_status": self.get_connection_status(),
        }
        return metrics

    def wlan_write(self, command: str, **placeholders: int) -> None:
        self.write(self._format_wlan_command(command, **placeholders))

    def wlan_query(self, command: str, **placeholders: int) -> str:
        return self.query(self._format_wlan_command(command, **placeholders))

    def _format_wlan_command(self, template: str, **placeholders: int) -> str:
        values = {
            "i": self._wlan_sign_index,
            "s": self._wlan_station_index,
            **{k.lower(): v for k, v in placeholders.items()},
        }

        def replace(match):
            key = match.group(1).strip().lower()
            if key not in values:
                raise ValueError(f"Missing WLAN placeholder: {key}")
            return str(values[key])

        return re.sub(r"<([^>]+)>", replace, template)

    @staticmethod
    def _parse_numeric(text: str) -> float:
        cleaned = (text or "").strip()
        if not cleaned:
            return 0.0
        cleaned = cleaned.replace(",", " ")
        for token in cleaned.split():
            try:
                return float(token)
            except ValueError:
                continue
        return 0.0

    def set_dl_power(
        self,
        rs_epre_dbm: float,
        enable_ocng: bool = True
    ) -> None:
        """
        设置下行功率参数
        
        Args:
            rs_epre_dbm: 参考信号 EPRE (Energy Per Resource Element) in dBm/15kHz
                         典型范围: -110 to -25 dBm
            enable_ocng: 是否启用 OCNG (OFDMA Channel Noise Generator)
                        用于模拟其他小区干扰，3GPP 测试常用
        
        SCPI Commands (基于 R&S 标准模式):
            - CONFigure:NR5G:SIGN:DL:PCC:RSEPre <power_dbm>
            - CONFigure:NR5G:SIGN:DL:OCNG:STATe ON|OFF
        
        Ref: 参考 3GPP TS 38.521-1 Annex C (功率设置要求)
        """
        # 参数验证
        if not (-120 <= rs_epre_dbm <= -20):
            self.logger.warning(f"RS EPRE {rs_epre_dbm} dBm 超出典型范围 [-120, -20]")
        
        # 设置 RS EPRE
        cmd_epre = f"CONF:NR5G:SIGN:DL:PCC:RSEP {rs_epre_dbm}"
        self.write(cmd_epre)
        self.logger.info(f"CMW500: 设置 RS EPRE = {rs_epre_dbm} dBm")
        
        # 配置 OCNG
        ocng_state = "ON" if enable_ocng else "OFF"
        cmd_ocng = f"CONF:NR5G:SIGN:DL:OCNG:STAT {ocng_state}"
        self.write(cmd_ocng)
        self.logger.info(f"CMW500: OCNG = {ocng_state}")
        
        # 缓存配置
        self._cell_config.update({
            "rs_epre_dbm": rs_epre_dbm,
            "ocng_enabled": enable_ocng
        })

    # ============================================================================
    # Phase 2: 信令控制
    # ============================================================================

    def attach_ue(self, timeout_s: float = 30.0) -> bool:
        """
        启动 NR 信令并等待 UE 附着（增强版，带超时轮询）
        
        Args:
            timeout_s: 等待附着的超时时间（秒），默认 30 秒
        
        Returns:
            True 如果附着成功，False 如果超时
        
        SCPI Commands:
            - SOURce:NR5G:SIGN:CELL:STATe ON
            - FETCh:NR5G:SIGN:PSWitched:STATe?
        
        Ref: 基于 5G RRC 状态机原理（IDLE -> CONNECTED）
        """
        self.logger.info("CMW500: 启动 NR 信令，等待 UE 附着...")
        
        # 启动信令
        self.write("SOUR:NR5G:SIGN:CELL:STAT ON")
        
        if self.simulation_mode:
            self.logger.info("CMW500: [模拟模式] 模拟等待 2 秒后附着成功")
            import time
            time.sleep(0.5)  # 模拟延迟
            return True
        
        # 真机模式：轮询附着状态
        return self.wait_for_connection_state(
            expected_states=["ATT", "ATTACHED"],
            timeout_s=timeout_s,
            poll_interval_s=1.0
        )

    def activate_data_transfer(self) -> bool:
        """
        激活数据传输（从 RRC IDLE 进入 RRC CONNECTED 状态）
        
        此方法用于建立数据连接，使 UE 从空闲态进入连接态，
        以便进行吞吐量、BLER 等测量。
        
        Returns:
            True 如果成功激活，False 如果失败
        
        SCPI Commands:
            - CONFigure:NR5G:SIGN:CONNection:ACTivate
            或
            - CONFigure:NR5G:SIGN:DL:PDSCH:STATe ON
        
        Ref: 基于 3GPP TS 38.331 RRC 状态转换
        """
        self.logger.info("CMW500: 激活数据传输（进入 RRC CONNECTED）...")
        
        if self.simulation_mode:
            self.logger.info("CMW500: [模拟模式] 假设数据传输已激活")
            return True
        
        try:
            # 方法 1: 直接激活连接
            self.write("CONF:NR5G:SIGN:CONN:ACT")
            
            # 等待进入 CONNECTED 状态
            success = self.wait_for_connection_state(
                expected_states=["CONN", "CONNECTED"],
                timeout_s=10.0,
                poll_interval_s=0.5
            )
            
            if success:
                self.logger.info("CMW500: ✓ 数据传输已激活")
            else:
                self.logger.warning("CMW500: ⚠ 数据传输激活超时")
            
            return success
        
        except Exception as e:
            self.logger.error(f"CMW500: 激活数据传输失败: {e}")
            return False

    def wait_for_connection_state(
        self,
        expected_states: list,
        timeout_s: float = 30.0,
        poll_interval_s: float = 1.0
    ) -> bool:
        """
        等待 UE 进入指定连接状态（辅助方法）
        
        Args:
            expected_states: 期望的状态列表，如 ["ATT", "ATTACHED"] 或 ["CONN", "CONNECTED"]
            timeout_s: 超时时间（秒）
            poll_interval_s: 轮询间隔（秒）
        
        Returns:
            True 如果进入期望状态，False 如果超时
        
        SCPI Query:
            - FETCh:NR5G:SIGN:PSWitched:STATe?
        
        可能的返回值:
            - "ATT" / "ATTACHED" - UE 已附着
            - "CONN" / "CONNECTED" - UE 处于连接态
            - "IDLE" / "OFF" - UE 空闲或未连接
        
        Ref: 基于 CMW500 状态机查询标准模式
        """
        import time
        
        start_time = time.time()
        last_status = "UNKNOWN"
        
        while (time.time() - start_time) < timeout_s:
            try:
                # 查询当前连接状态
                status = self.query("FETC:NR5G:SIGN:PSW:STAT?").strip().upper()
                
                # 检查是否匹配期望状态
                if any(expected.upper() in status for expected in expected_states):
                    self.logger.info(f"CMW500: ✓ 进入期望状态: {status}")
                    return True
                
                # 状态变化时记录日志
                if status != last_status:
                    elapsed = time.time() - start_time
                    self.logger.debug(f"CMW500: [t={elapsed:.1f}s] 当前状态: {status}")
                    last_status = status
                
            except Exception as e:
                self.logger.warning(f"CMW500: 状态查询失败: {e}")
            
            time.sleep(poll_interval_s)
        
        # 超时
        self.logger.error(
            f"CMW500: ✗ 等待状态超时！期望: {expected_states}, "
            f"最后状态: {last_status}, 用时: {timeout_s}s"
        )
        return False

    def detach_ue(self) -> None:
        """
        主动去附着 UE 并关闭信令
        
        SCPI Commands:
            - SOURce:NR5G:SIGN:CELL:STATe OFF
        """
        self.write("SOUR:NR5G:SIGN:CELL:STAT OFF")
        self.logger.info("CMW500: 关闭 NR 信令")

    def start_signaling(self, tech: str = "NR") -> None:
        """
        Start signaling for NR/LTE/WLAN.
        """
        tech_upper = tech.upper()
        if tech_upper in ("WLAN", "WIFI", "WI-FI", "802.11") or self._tech_mode == "WLAN":
            self._tech_mode = "WLAN"
            self.start_wlan_signaling()
            return
        if tech_upper in ("NR", "NR5G", "5G") or self._tech_mode == "NR5G":
            self._tech_mode = "NR5G"
            self.attach_ue()
            return
        if tech_upper in ("LTE",):
            self._tech_mode = "LTE"
            self.start_call()
            return
        self.logger.warning("CMW500: 未知制式 %s，默认执行 NR 信令", tech)
        self.attach_ue()

    def stop_signaling(self) -> None:
        """
        Stop signaling for current technology.
        """
        if self._tech_mode == "WLAN":
            self.stop_wlan_signaling()
            return
        if self._tech_mode == "NR5G":
            self.detach_ue()
            return
        if self._tech_mode == "LTE":
            self.stop_call()
            return
        self.logger.warning("CMW500: 未知制式，执行 LTE 停止信令")
        self.stop_call()

    # ============================================================================
    # Phase 3: 测量接口（覆盖基类方法）
    # ============================================================================

    def get_throughput(self) -> float:
        """
        查询实时下行吞吐量
        
        Returns:
            吞吐量 (Mbps)
        
        SCPI Command:
            - FETCh:NR5G:SIGN:ETHRoughput:AVERage?
        
        Ref: TODO - 需手册确认精确指令
        """
        if self.simulation_mode:
            import random
            return 180.0 + random.uniform(-20, 20)

        if self._tech_mode == "WLAN":
            try:
                return self.get_wlan_data_rate()
            except Exception as e:
                self.logger.error(f"CMW500: 查询 WLAN 数据速率失败: {e}")
                return 0.0
        
        try:
            # 查询平均吞吐量（假设返回单位为 bps）
            result = self.query("FETC:NR5G:SIGN:ETHR:AVER?")
            throughput_bps = float(result.strip())
            return throughput_bps / 1e6  # 转换为 Mbps
        except Exception as e:
            self.logger.error(f"CMW500: 查询吞吐量失败: {e}")
            return 0.0

    def get_bler(self) -> float:
        """
        查询实时误块率 (Block Error Rate)
        
        Returns:
            BLER (0.0-1.0)
        
        SCPI Command:
            - FETCh:NR5G:SIGN:BLER:AVERage?
        """
        if self.simulation_mode:
            import random
            return 0.01 + random.uniform(0, 0.02)

        if self._tech_mode == "WLAN":
            try:
                return self.read_wlan_per()
            except Exception as e:
                self.logger.error(f"CMW500: 查询 WLAN PER 失败: {e}")
                return 1.0
        
        try:
            result = self.query("FETC:NR5G:SIGN:BLER:AVER?")
            bler = float(result.strip())
            return bler / 100.0 if bler > 1.0 else bler  # 处理百分比格式
        except Exception as e:
            self.logger.error(f"CMW500: 查询 BLER 失败: {e}")
            return 1.0

    def get_rsrp(self) -> float:
        """
        查询 RSRP (Reference Signal Received Power)
        
        Returns:
            RSRP (dBm)
        
        SCPI Command:
            - FETCh:NR5G:SIGN:UEReport:RSRP?
        """
        if self.simulation_mode:
            import random
            return -90.0 + random.uniform(-10, 10)

        if self._tech_mode == "WLAN":
            try:
                return self.get_wlan_rx_power()
            except Exception as e:
                self.logger.error(f"CMW500: 查询 WLAN RX Power 失败: {e}")
                return -999.0
        
        try:
            result = self.query("FETC:NR5G:SIGN:UER:RSRP?")
            return float(result.strip())
        except Exception as e:
            self.logger.error(f"CMW500: 查询 RSRP 失败: {e}")
            return -999.0

    def get_sinr(self) -> float:
        """
        查询 SINR (Signal to Interference plus Noise Ratio)
        
        Returns:
            SINR (dB)
        
        SCPI Command:
            - FETCh:NR5G:SIGN:UEReport:SINR?
        """
        if self.simulation_mode:
            import random
            return 15.0 + random.uniform(-5, 5)

        if self._tech_mode == "WLAN":
            self.logger.warning("CMW500: WLAN 模式下无直接 SINR 查询指令，返回 0.0")
            return 0.0
        
        try:
            result = self.query("FETC:NR5G:SIGN:UER:SINR?")
            return float(result.strip())
        except Exception as e:
            self.logger.error(f"CMW500: 查询 SINR 失败: {e}")
            return 0.0

    # ============================================================================
    # 兼容性方法（保留旧接口）
    # ============================================================================

    def set_tech_standard(self, standard: str):
        """
        [遗留方法] 切换信令场景 (例如 LTE, NR5G)
        
        推荐使用 configure_nr_cell() 替代此方法
        """
        standard_upper = standard.upper()
        if standard_upper in ("WLAN", "WIFI", "WI-FI", "802.11"):
            self._tech_mode = "WLAN"
            self.logger.info("CMW500: 切换到 WLAN 模式")
        elif standard_upper == "LTE":
            self.write("ROUT:SIGN:LTE:SCEN:MOD STAN")
            self.logger.info("CMW500: 切换到 LTE Standard 信令模式")
            self._tech_mode = "LTE"
        elif standard_upper == "NR5G":
            self.write("ROUT:SIGN:NR5G:SCEN:MOD STAN")
            self.logger.info("CMW500: 切换到 5G NR 信令模式")
            self._tech_mode = "NR5G"
        else:
            self.logger.warning(f"CMW500: 未知标准 {standard}")

    def start_call(self):
        """
        [遗留方法] 开启信令
        
        推荐使用 attach_ue() 替代此方法
        """
        if self._tech_mode == "WLAN":
            self.start_wlan_signaling()
        elif self._tech_mode == "NR5G":
            self.write("SOUR:NR5G:SIGN:CELL:STAT ON")
            self.logger.info("CMW500: 开启 NR 信令...")
        else:
            self.write("SOUR:LTE:SIGN:STAT ON")
            self.logger.info("CMW500: 开启 LTE 信令...")

    def stop_call(self):
        """
        [遗留方法] 关闭信令
        
        推荐使用 detach_ue() 替代此方法
        """
        if self._tech_mode == "WLAN":
            self.stop_wlan_signaling()
            return
        if self._tech_mode == "NR5G":
            self.write("SOUR:NR5G:SIGN:CELL:STAT OFF")
        else:
            self.write("SOUR:LTE:SIGN:STAT OFF")
        self.logger.info(f"CMW500: 关闭 {self._tech_mode} 信令")

    def get_connection_status(self) -> str:
        """
        [遗留方法] 查询连接状态
        
        Returns:
            连接状态字符串，如 'ATT' (Attached), 'CONN' (Connected), 'IDLE'
        """
        try:
            if self._tech_mode == "WLAN":
                return self.query(f"FETCh:WLAN:SIGN{self._wlan_sign_index}:PSWitched:STATe?").strip()
            if self._tech_mode == "NR5G":
                return self.query("FETC:NR5G:SIGN:PSW:STAT?").strip()
            else:
                return self.query("FETC:LTE:SIGN:PSW:STAT?").strip()
        except Exception:
            return "ERROR"
