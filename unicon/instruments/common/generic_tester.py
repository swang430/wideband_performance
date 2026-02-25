from drivers.base_instrument import BaseInstrument


class GenericTester(BaseInstrument):
    """
    通用综测仪驱动。
    """
    def __init__(self, resource_name: str, name: str = "Generic_Tester", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def set_tech_standard(self, standard: str):
        """[标准接口] 设置技术制式 (如 LTE, NR5G)"""
        self.logger.info(f"设置标准: {standard} (Generic)")

    def start_call(self):
        """[标准接口] 发起信令呼叫"""
        self.logger.info("发起呼叫 (Generic)")

    def stop_call(self):
        """[标准接口] 结束呼叫"""
        self.logger.info("停止呼叫 (Generic)")

    def get_connection_status(self) -> str:
        """[标准接口] 获取连接状态 (e.g. CONN, IDLE)"""
        return "UNKNOWN"

    # === 场景测试扩展方法 ===
    # TODO: 以下方法的实际 SCPI 指令需核对手册确认
    # Ref: manual_library/integrated_tester/Rohde_and_Schwarz_CMW/Remote_Control_SCPI_GettingStarted_en_04.pdf

    def start_signaling(self, tech: str = "NR"):
        """[标准接口] 启动信令连接"""
        self.logger.info(f"启动信令: {tech}")

    def stop_signaling(self):
        """[标准接口] 停止信令连接"""
        self.logger.info("停止信令")

    def get_throughput(self) -> float:
        """[标准接口] 获取当前吞吐量 (Mbps)"""
        if self.simulation_mode:
            import random
            return 180.0 + random.uniform(-20, 20)
        return 0.0

    def get_bler(self) -> float:
        """[标准接口] 获取当前 BLER"""
        if self.simulation_mode:
            import random
            return 0.01 + random.uniform(0, 0.02)
        return 0.0

    def get_rsrp(self) -> float:
        """[标准接口] 获取 RSRP (dBm)"""
        if self.simulation_mode:
            import random
            return -90.0 + random.uniform(-10, 10)
        return -999.0

    def get_sinr(self) -> float:
        """[标准接口] 获取 SINR (dB)"""
        if self.simulation_mode:
            import random
            return 15.0 + random.uniform(-5, 5)
        return 0.0

    def configure_cell(self, freq_hz: float, bandwidth_mhz: float, power_dbm: float):
        """[标准接口] 配置小区参数"""
        self.logger.info(f"配置小区: freq={freq_hz/1e6}MHz, bw={bandwidth_mhz}MHz, pwr={power_dbm}dBm")

    def trigger_handover(self, target_config: dict):
        """[标准接口] 触发小区切换"""
        self.logger.info(f"触发切换: {target_config}")
