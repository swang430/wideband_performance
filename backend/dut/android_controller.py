import subprocess
import logging
import time

class AndroidController:
    """
    ADB 封装类，用于控制 Android 被测设备 (DUT)。
    """
    def __init__(self, device_id: str = None, simulation_mode: bool = False):
        self.device_id = device_id
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger("DUT.Android")

    def _run_adb(self, command: str) -> str:
        """
        运行原生 ADB 指令。
        """
        if self.simulation_mode:
            self.logger.debug(f"[模拟] ADB 执行: adb {command}")
            return "List of devices attached\nemulator-5554\tdevice" if "devices" in command else "SIM_OUTPUT"

        cmd_list = ["adb"]
        if self.device_id:
            cmd_list.extend(["-s", self.device_id])
        cmd_list.extend(command.split())
        
        self.logger.debug(f"ADB 执行: {' '.join(cmd_list)}")
        try:
            result = subprocess.run(
                cmd_list, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ADB 错误: {e.stderr.strip()}")
            raise

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
