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
