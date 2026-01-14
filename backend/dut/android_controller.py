import subprocess
import logging
import time
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModemStatus:
    """Modem 状态数据类"""
    rsrp: Optional[float] = None      # 参考信号接收功率 (dBm)
    rsrq: Optional[float] = None      # 参考信号接收质量 (dB)
    sinr: Optional[float] = None      # 信噪比 (dB)
    cqi: Optional[int] = None         # 信道质量指示
    pci: Optional[int] = None         # 物理小区 ID
    earfcn: Optional[int] = None      # E-UTRA 绝对射频信道号
    band: Optional[str] = None        # 频段
    network_type: Optional[str] = None # 网络类型 (LTE/NR)
    mcc: Optional[str] = None         # 移动国家码
    mnc: Optional[str] = None         # 移动网络码
    cell_id: Optional[str] = None     # 小区 ID

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rsrp": self.rsrp,
            "rsrq": self.rsrq,
            "sinr": self.sinr,
            "cqi": self.cqi,
            "pci": self.pci,
            "earfcn": self.earfcn,
            "band": self.band,
            "network_type": self.network_type,
            "mcc": self.mcc,
            "mnc": self.mnc,
            "cell_id": self.cell_id
        }


class AndroidController:
    """
    ADB 封装类，用于控制 Android 被测设备 (DUT)。
    支持深度 Modem 参数抓取 (RSRP/RSRQ/SINR/CQI 等)。
    """
    def __init__(self, device_id: str = None, simulation_mode: bool = False):
        self.device_id = device_id
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger("DUT.Android")
        self._last_modem_status: Optional[ModemStatus] = None

    def _run_adb(self, command: str) -> str:
        """
        运行原生 ADB 指令。
        """
        if self.simulation_mode:
            self.logger.debug(f"[模拟] ADB 执行: adb {command}")
            if "devices" in command:
                return "List of devices attached\nemulator-5554\tdevice"
            elif "telephony.registry" in command:
                return self._get_simulated_telephony_dump()
            elif "connectivity" in command:
                return "NetworkInfo: type: MOBILE[LTE], state: CONNECTED"
            return "SIM_OUTPUT"

        cmd_list = ["adb"]
        if self.device_id:
            cmd_list.extend(["-s", self.device_id])
        cmd_list.extend(command.split())

        self.logger.debug(f"ADB 执行: {' '.join(cmd_list)}")
        try:
            result = subprocess.run(
                cmd_list, capture_output=True, text=True, check=True, timeout=10
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ADB 错误: {e.stderr.strip()}")
            raise
        except subprocess.TimeoutExpired:
            self.logger.error("ADB 命令超时")
            raise

    def _get_simulated_telephony_dump(self) -> str:
        """返回模拟的 telephony.registry dump 数据"""
        import random
        rsrp = -80 + random.randint(-15, 5)
        rsrq = -10 + random.randint(-5, 3)
        sinr = 15 + random.randint(-5, 10)
        cqi = random.randint(8, 15)

        return f"""
  mCellInfo=[CellInfoLte:{{
    mRegistered=YES
    mTimeStamp=1234567890ns
    mCellConnectionStatus=1
    CellIdentityLte:{{ mCi=12345678 mPci=123 mTac=1234 mEarfcn=1300 mBands=[3] mBandwidth=20000 mMcc=460 mMnc=00 mAlphaLong=CHINA MOBILE mAlphaShort=CMCC }}
    CellSignalStrengthLte: rssi=-89 rsrp={rsrp} rsrq={rsrq} rssnr={sinr} cqi={cqi} ta=0
  }}]
  mServiceState=0 0 voice home data home CHINA MOBILE CHINA MOBILE 46000 CHINA MOBILE CHINA MOBILE 46000  LTE LTE CSS not supported -1 -1 RoijngIndicator=0 EriAlerts=0 cdmaDbm=-1 cdmaEcio=-1 evdoDbm=-1 evdoEcio=-1 evdoSnr=-1 isEmergencyOnly=false
        """

    def connect(self):
        """
        验证设备连接。
        """
        devices = self._run_adb("devices")
        if self.device_id:
            if self.device_id not in devices:
                raise ConnectionError(f"未找到设备 {self.device_id}。")
        else:
            # 如果未指定 ID，检查是否至少有一个设备存在
            lines = devices.splitlines()
            if len(lines) <= 1:
                raise ConnectionError("未找到 ADB 设备。")
        self.logger.info("DUT 已通过 ADB 连接")

    def shell(self, command: str) -> str:
        """
        运行 ADB shell 指令。
        """
        return self._run_adb(f"shell {command}")

    def start_traffic(self, server_ip: str, duration: int = 10, bandwidth: str = "100M"):
        """
        在 DUT 上启动 iPerf 流量 (假设已安装 iPerf3)。
        """
        cmd = f"iperf3 -c {server_ip} -t {duration} -b {bandwidth} -R"
        self.logger.info(f"启动流量: {cmd}")
        return self.shell(cmd)

    def get_wifi_rssi(self) -> int:
        """
        获取当前 WiFi RSSI (示例实现)。
        """
        try:
            dump = self.shell("dumpsys wifi | grep RSSI")
            # 从 dump 中解析 RSSI (简化版)
            # 这主要取决于 Android 版本和输出格式
            if "RSSI:" in dump:
                rssi = dump.split("RSSI:")[1].split()[0]
                return int(rssi)
            return -100
        except Exception:
            return -100

    # ========== Modem 深度集成方法 ==========

    def get_modem_status(self) -> ModemStatus:
        """
        获取 Modem 状态信息，包括 RSRP/RSRQ/SINR/CQI 等参数。
        通过解析 dumpsys telephony.registry 输出获取。

        Returns:
            ModemStatus: 包含各项无线参数的数据对象
        """
        status = ModemStatus()

        try:
            # 获取 telephony.registry dump
            dump = self.shell("dumpsys telephony.registry")

            # 解析 LTE 信号强度参数
            status = self._parse_lte_signal(dump, status)

            # 解析小区标识信息
            status = self._parse_cell_identity(dump, status)

            # 解析网络类型
            status = self._parse_network_type(dump, status)

            self._last_modem_status = status
            self.logger.debug(f"Modem 状态: RSRP={status.rsrp}, SINR={status.sinr}, CQI={status.cqi}")

        except Exception as e:
            self.logger.error(f"获取 Modem 状态失败: {e}")

        return status

    def _parse_lte_signal(self, dump: str, status: ModemStatus) -> ModemStatus:
        """解析 LTE 信号强度参数"""
        # 匹配 CellSignalStrengthLte 行
        # 格式: CellSignalStrengthLte: rssi=-89 rsrp=-85 rsrq=-10 rssnr=15 cqi=12 ta=0
        pattern = r'CellSignalStrengthLte:.*?rsrp=(-?\d+).*?rsrq=(-?\d+).*?rssnr=(-?\d+).*?cqi=(\d+)'
        match = re.search(pattern, dump)

        if match:
            status.rsrp = float(match.group(1))
            status.rsrq = float(match.group(2))
            status.sinr = float(match.group(3))
            status.cqi = int(match.group(4))

        return status

    def _parse_cell_identity(self, dump: str, status: ModemStatus) -> ModemStatus:
        """解析小区标识信息"""
        # 匹配 CellIdentityLte 行
        # 格式: CellIdentityLte:{ mCi=12345678 mPci=123 mTac=1234 mEarfcn=1300 mBands=[3] ...
        ci_match = re.search(r'mCi=(\d+)', dump)
        pci_match = re.search(r'mPci=(\d+)', dump)
        earfcn_match = re.search(r'mEarfcn=(\d+)', dump)
        bands_match = re.search(r'mBands=\[(\d+)', dump)
        mcc_match = re.search(r'mMcc=(\d+)', dump)
        mnc_match = re.search(r'mMnc=(\d+)', dump)

        if ci_match:
            status.cell_id = ci_match.group(1)
        if pci_match:
            status.pci = int(pci_match.group(1))
        if earfcn_match:
            status.earfcn = int(earfcn_match.group(1))
        if bands_match:
            status.band = f"B{bands_match.group(1)}"
        if mcc_match:
            status.mcc = mcc_match.group(1)
        if mnc_match:
            status.mnc = mnc_match.group(1)

        return status

    def _parse_network_type(self, dump: str, status: ModemStatus) -> ModemStatus:
        """解析网络类型"""
        if 'NR' in dump or '5G' in dump:
            status.network_type = 'NR'
        elif 'LTE' in dump:
            status.network_type = 'LTE'
        elif 'WCDMA' in dump or 'HSPA' in dump:
            status.network_type = '3G'
        else:
            status.network_type = 'Unknown'

        return status

    def get_signal_quality(self) -> Dict[str, Any]:
        """
        获取简化的信号质量摘要。

        Returns:
            包含关键信号指标的字典
        """
        status = self.get_modem_status()
        return {
            "rsrp_dbm": status.rsrp,
            "rsrq_db": status.rsrq,
            "sinr_db": status.sinr,
            "cqi": status.cqi,
            "network": status.network_type,
            "cell_id": status.cell_id
        }

    def monitor_modem(self, duration: int = 10, interval: float = 1.0) -> list:
        """
        持续监控 Modem 状态一段时间。

        Args:
            duration: 监控持续时间 (秒)
            interval: 采样间隔 (秒)

        Returns:
            时序状态数据列表
        """
        samples = []
        start_time = time.time()

        while time.time() - start_time < duration:
            status = self.get_modem_status()
            samples.append({
                "timestamp": time.time() - start_time,
                **status.to_dict()
            })
            time.sleep(interval)

        self.logger.info(f"Modem 监控完成，共采集 {len(samples)} 个样本")
        return samples

    def get_data_connection_state(self) -> str:
        """
        获取数据连接状态。

        Returns:
            连接状态字符串 (CONNECTED/DISCONNECTED/CONNECTING)
        """
        try:
            dump = self.shell("dumpsys connectivity | grep -i 'NetworkInfo.*MOBILE'")
            if "CONNECTED" in dump:
                return "CONNECTED"
            elif "CONNECTING" in dump:
                return "CONNECTING"
            else:
                return "DISCONNECTED"
        except Exception:
            return "UNKNOWN"

    def enable_airplane_mode(self, enable: bool = True):
        """
        开启/关闭飞行模式。

        Args:
            enable: True 开启飞行模式，False 关闭
        """
        value = "1" if enable else "0"
        self.shell(f"settings put global airplane_mode_on {value}")
        # 广播状态变更
        self.shell("am broadcast -a android.intent.action.AIRPLANE_MODE")
        self.logger.info(f"飞行模式: {'开启' if enable else '关闭'}")

    def set_preferred_network_type(self, network_type: str):
        """
        设置首选网络类型 (需要 root 权限)。

        Args:
            network_type: 'LTE_ONLY', 'NR_ONLY', 'LTE_NR', 'AUTO'
        """
        # 网络类型映射 (基于 Android RIL 定义)
        type_map = {
            'LTE_ONLY': 11,
            'NR_ONLY': 23,
            'LTE_NR': 25,
            'AUTO': 0
        }

        if network_type not in type_map:
            self.logger.warning(f"未知网络类型: {network_type}")
            return

        value = type_map[network_type]
        self.shell(f"settings put global preferred_network_mode {value}")
        self.logger.info(f"首选网络类型设置为: {network_type}")
