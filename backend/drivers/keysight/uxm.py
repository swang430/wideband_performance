import json
import time
from json import JSONDecodeError
from typing import Any, List, Optional

from drivers.common.generic_tester import GenericTester


class UXM_Driver(GenericTester):
    """
    Keysight UXM (E7515) 综合测试仪驱动。

    Ref: manual_library/integrated_tester/Keysight_UXM/5G_NR_Test_Application_SCPI_Reference.html
    """
    scpi_catalog_id = "keysight_uxm"

    def __init__(self, resource_name: str, name: str = "Keysight_UXM", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)
        self._cell = "CELL1"
        self._cell_type = "NR5G"

    def set_tech_standard(self, standard: str) -> None:
        """
        设置当前技术制式。

        Args:
            standard: NR5G 或 LTE
        """
        standard_upper = standard.upper()
        if standard_upper in ("NR", "NR5G", "5G"):
            self._cell_type = "NR5G"
        elif standard_upper in ("LTE",):
            self._cell_type = "LTE"
        else:
            self.logger.warning("UXM 未识别的制式: %s", standard)

    def start_signaling(self, tech: str = "NR") -> None:
        """
        启动信令（开启指定小区）。

        Ref: UXM SCPI Reference, section "Switch Cell On/Off"
        Command: BSE:CONFig:<celltype>:<cell>:ACTive[:STATe]
        """
        if self.simulation_mode:
            self.logger.info("UXM: [模拟] 启动信令 (%s)", tech)
            return

        cell_type = "NR5G" if tech.upper() in ("NR", "NR5G", "5G") else "LTE"
        self._cell_type = cell_type
        self.write(f"BSE:CONFig:{cell_type}:{self._cell}:ACTive ON")
        self.logger.info("UXM: 已开启 %s %s", cell_type, self._cell)

    def stop_signaling(self) -> None:
        """
        停止信令（关闭指定小区）。

        Ref: UXM SCPI Reference, section "Switch Cell On/Off"
        Command: BSE:CONFig:<celltype>:<cell>:ACTive[:STATe]
        """
        if self.simulation_mode:
            self.logger.info("UXM: [模拟] 停止信令")
            return

        self.write(f"BSE:CONFig:{self._cell_type}:{self._cell}:ACTive OFF")
        self.logger.info("UXM: 已关闭 %s %s", self._cell_type, self._cell)

    def start_call(self) -> None:
        """
        兼容旧接口：开启信令。
        """
        self.start_signaling(self._cell_type)

    def stop_call(self) -> None:
        """
        兼容旧接口：关闭信令。
        """
        self.stop_signaling()

    def get_connection_status(self) -> str:
        """
        获取连接状态。

        Ref: UXM SCPI Reference, section "NR Connection Status"
        Command: BSE:STATus:NR5G:<cell>?
        """
        if self.simulation_mode:
            return "SIM"

        cmd = f"BSE:STATus:{self._cell_type}:{self._cell}?"
        try:
            return self.query(cmd)
        except Exception as exc:
            self.logger.error("UXM: 查询连接状态失败: %s", exc)
            return "ERROR"

    def configure_cell(self, freq_hz: float, bandwidth_mhz: float, power_dbm: float) -> None:
        """
        配置 NR 小区参数（DL/UL 带宽、ARFCN、下行功率）。

        Args:
            freq_hz: 下行中心频率 (Hz)
            bandwidth_mhz: 带宽 (MHz)
            power_dbm: DL 参考信号功率 (dBm, EPRE)

        Ref:
            - UXM SCPI Reference, section "NR DL Bandwidth"
              Command: BSE:CONFig:NR5G:<cell>:DL:BW
            - UXM SCPI Reference, section "NR UL Bandwidth"
              Command: BSE:CONFig:NR5G:<cell>:UL:BW
            - UXM SCPI Reference, section "NR DL ARFCN"
              Command: BSE:CONFig:NR5G:<cell>:DL:ARFCN
            - UXM SCPI Reference, section "NR UL ARFCN"
              Command: BSE:CONFig:NR5G:<cell>:UL:ARFCN
            - UXM SCPI Reference, section "DL Reference Signal Power"
              Command: BSE:CONFig:NR5G:<cell>:DL:POWer[:EPRE]
        """
        if self.simulation_mode:
            self.logger.info(
                "UXM: [模拟] 配置小区 freq=%.3f MHz bw=%.1f MHz pwr=%.2f dBm",
                freq_hz / 1e6,
                bandwidth_mhz,
                power_dbm,
            )
            return

        bw_token = self._format_bandwidth_token(bandwidth_mhz)
        self.write(f"BSE:CONFig:NR5G:{self._cell}:DL:BW {bw_token}")
        self.write(f"BSE:CONFig:NR5G:{self._cell}:UL:BW {bw_token}")

        dl_arfcn = self._calc_nr_arfcn(freq_hz)
        ul_arfcn = dl_arfcn
        self.write(f"BSE:CONFig:NR5G:{self._cell}:DL:ARFCN {dl_arfcn}")
        self.write(f"BSE:CONFig:NR5G:{self._cell}:UL:ARFCN {ul_arfcn}")

        self.write(f"BSE:CONFig:NR5G:{self._cell}:DL:POWer:EPRE {power_dbm}")
        self.logger.info(
            "UXM: 小区配置完成 freq=%.3f MHz arfcn=%d bw=%s pwr=%.2f dBm",
            freq_hz / 1e6,
            dl_arfcn,
            bw_token,
            power_dbm,
        )

    def get_throughput(self) -> float:
        """
        获取下行吞吐量 (Mbps)。

        Ref: UXM SCPI Reference, section "DL OTA Results CSV (format-qualified)"
        Command: BSE:MEASure:NR5G:BTHRoughput:DL:THRoughput:OTA:CSValues:<cell>? <format>
        """
        if self.simulation_mode:
            return super().get_throughput()

        cmd = f"BSE:MEASure:NR5G:BTHRoughput:DL:THRoughput:OTA:CSValues:{self._cell}? FORMAT_1"
        try:
            values = self._parse_csv_floats(self.query(cmd))
            if len(values) >= 2:
                return float(values[1])
        except Exception as exc:
            self.logger.error("UXM: 查询吞吐量失败: %s", exc)
        return 0.0

    def get_bler(self) -> float:
        """
        获取下行 BLER。

        Ref: UXM SCPI Reference, section "DL BLER Results"
        Command: BSE:MEASure:NR5G:BTHRoughput:DL:BLER:<cell>?
        """
        if self.simulation_mode:
            return super().get_bler()

        cmd = f"BSE:MEASure:NR5G:BTHRoughput:DL:BLER:{self._cell}?"
        try:
            values = self._parse_csv_floats(self.query(cmd))
            if len(values) >= 9:
                bler = float(values[8])
                return bler / 100.0 if bler > 1.0 else bler
        except Exception as exc:
            self.logger.error("UXM: 查询 BLER 失败: %s", exc)
        return 0.0

    def get_rsrp(self) -> float:
        """
        获取 RSRP (dBm)。

        Ref:
            - UXM SCPI Reference, section "NR RSRP Measurement Start"
              Command: BSE:MEASure:NR5G:<cell>:L1:RSRPower:STARt
            - UXM SCPI Reference, section "NR RSRP Measurement State Query"
              Command: BSE:MEASure:NR5G:<cell>:L1:RSRPower:STATe?
            - UXM SCPI Reference, section "NR RSRP Measurement Report Query"
              Command: BSE:MEASure:NR5G:<cell>:L1:RSRPower:REPorts:JSON?
        """
        if self.simulation_mode:
            return super().get_rsrp()

        self._ensure_rsrp_measurement()
        cmd = f"BSE:MEASure:NR5G:{self._cell}:L1:RSRPower:REPorts:JSON?"
        try:
            data = self._parse_json_text(self.query(cmd))
            rsrp = self._extract_rsrp_from_report(data)
            if rsrp is not None:
                return rsrp
        except Exception as exc:
            self.logger.error("UXM: 查询 RSRP 失败: %s", exc)
        return -999.0

    def get_sinr(self) -> float:
        """
        获取 SINR (dB)。

        Ref: UXM SCPI Reference, section "Csi Read Meas Samples"
        Command: BSE:MEASure:NR5G:<cell>:CSI:VALues[:JSON]
        """
        if self.simulation_mode:
            return super().get_sinr()

        self._ensure_csi_measurement()
        cmd = f"BSE:MEASure:NR5G:{self._cell}:CSI:VALues:JSON"
        try:
            data = self._parse_json_text(self.query(cmd))
            sinr = self._extract_numeric_from_json(data, ["sinr", "csinr"])
            if sinr is not None:
                return sinr
            self.logger.warning("UXM: CSI 样本中未找到 SINR 字段")
        except Exception as exc:
            self.logger.error("UXM: 查询 SINR 失败: %s", exc)
        return 0.0

    def trigger_handover(self, target_config: dict) -> None:
        """
        触发小区切换（占位）。

        当前未找到 UXM SCPI 中直接的手切换触发命令，需后续补充。
        """
        self.logger.warning("UXM: 触发切换尚未实现，配置: %s", target_config)

    def _format_bandwidth_token(self, bandwidth_mhz: float) -> str:
        bw_int = int(round(bandwidth_mhz))
        if bw_int <= 0:
            raise ValueError("带宽必须为正数")
        return f"BW{bw_int}"

    def _calc_nr_arfcn(self, freq_hz: float) -> int:
        """
        根据手册给出的频率-ARFCN公式计算 ARFCN。

        Ref: UXM SCPI Reference, section "NR DL Frequency"
        """
        if freq_hz >= 24_250_080_000:
            arfcn = (freq_hz - 24_250_080_000) / 60000 + 2_016_667
        elif freq_hz >= 3_000_000_000:
            arfcn = (freq_hz - 3_000_000_000) / 15000 + 600_000
        else:
            arfcn = freq_hz / 5000
        return int(round(arfcn))

    def _ensure_rsrp_measurement(self) -> None:
        state_cmd = f"BSE:MEASure:NR5G:{self._cell}:L1:RSRPower:STATe?"
        try:
            state = self.query(state_cmd).strip().upper()
        except Exception as exc:
            self.logger.warning("UXM: 查询 RSRP 状态失败: %s", exc)
            return

        if state == "MEAS":
            return

        if state in ("STOP", "WAIT"):
            self.write(f"BSE:MEASure:NR5G:{self._cell}:L1:RSRPower:STARt")
            self._poll_measurement_state(state_cmd, target_state="STOP", timeout_s=2.0)

    def _ensure_csi_measurement(self) -> None:
        state_cmd = f"BSE:MEASure:NR5G:{self._cell}:CSI:STATe?"
        try:
            state = self.query(state_cmd).strip().upper()
        except Exception as exc:
            self.logger.warning("UXM: 查询 CSI 状态失败: %s", exc)
            return

        if state == "MEAS":
            return

        if state in ("STOP", "WAIT"):
            self.write(f"BSE:MEASure:NR5G:{self._cell}:CSI:STARt")
            self._poll_measurement_state(state_cmd, target_state="MEAS", timeout_s=2.0)

    def _poll_measurement_state(self, cmd: str, target_state: str, timeout_s: float) -> None:
        end_time = time.monotonic() + timeout_s
        while time.monotonic() < end_time:
            try:
                state = self.query(cmd).strip().upper()
            except Exception:
                state = ""
            if state == target_state:
                return
            time.sleep(0.1)

    def _parse_csv_floats(self, text: str) -> List[float]:
        cleaned = text.strip().strip("[]")
        if not cleaned:
            return []
        values: List[float] = []
        for part in cleaned.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                values.append(float(part))
            except ValueError:
                self.logger.debug("UXM: 无法解析数值: %s", part)
        return values

    def _parse_json_text(self, text: str) -> Optional[Any]:
        cleaned = text.strip()
        if not cleaned:
            return None
        try:
            return json.loads(cleaned)
        except JSONDecodeError:
            try:
                return json.loads(cleaned.replace("'", "\""))
            except JSONDecodeError:
                self.logger.warning("UXM: JSON 解析失败")
                return None

    def _extract_rsrp_from_report(self, data: Any) -> Optional[float]:
        if not isinstance(data, dict):
            return None
        fields = data.get("measurement_fields")
        measurements = data.get("measurements")
        if not isinstance(fields, list) or not isinstance(measurements, list) or not measurements:
            return None
        try:
            idx = next(
                i for i, name in enumerate(fields)
                if isinstance(name, str) and name.lower() == "measrsrp"
            )
        except StopIteration:
            return None
        last = measurements[-1]
        if not isinstance(last, list) or idx >= len(last):
            return None
        try:
            return float(last[idx])
        except (TypeError, ValueError):
            return None

    def _extract_numeric_from_json(self, data: Any, key_candidates: List[str]) -> Optional[float]:
        if data is None:
            return None

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(key, str) and any(k in key.lower() for k in key_candidates):
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        return None
                nested = self._extract_numeric_from_json(value, key_candidates)
                if nested is not None:
                    return nested
        elif isinstance(data, list):
            for item in data:
                nested = self._extract_numeric_from_json(item, key_candidates)
                if nested is not None:
                    return nested
        return None
