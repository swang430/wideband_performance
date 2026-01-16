from drivers.common.generic_tester import GenericTester


class CMW500_Driver(GenericTester):
    """
    Rohde & Schwarz CMW500 专用驱动。
    注: CMW500 信令极其复杂，本驱动仅实现基础 LTE 信令控制框架。
    """

    def __init__(self, resource_name: str, name: str = "RS_CMW500", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def set_tech_standard(self, standard: str):
        """
        切换信令场景 (例如 LTE)。
        """
        if standard.upper() == "LTE":
            self.write("ROUT:SIGN:LTE:SCEN:MOD STAN")
            self.logger.info("CMW500: 切换到 LTE Standard 信令模式")
        elif standard.upper() == "NR5G":
            self.write("ROUT:SIGN:NR5G:SCEN:MOD STAN") # 假设指令
            self.logger.info("CMW500: 切换到 5G NR 信令模式")
        else:
            self.logger.warning(f"CMW500: 未知标准 {standard}")

    def start_call(self):
        """
        开启信令并等待 Attach。
        """
        self.write("SOUR:LTE:SIGN:STAT ON")
        self.logger.info("CMW500: 开启 LTE 信令...")

    def stop_call(self):
        self.write("SOUR:LTE:SIGN:STAT OFF")
        self.logger.info("CMW500: 关闭 LTE 信令")

    def get_connection_status(self) -> str:
        """
        查询 LTE 连接状态。
        """
        # 返回如 'ATT', 'CONN', 'IDLE'
        try:
            return self.query("FETC:LTE:SIGN:PSW:STAT?")
        except Exception:
            return "ERROR"
