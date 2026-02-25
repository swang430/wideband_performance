from drivers.common.generic_sa import GenericSA


class FSW_Driver(GenericSA):
    """
    Rohde & Schwarz FSW 频谱仪专用驱动。
    """

    def __init__(self, resource_name: str, name: str = "RS_FSW", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def get_trace_data(self) -> list:
        """
        [重写] 读取 Trace 1 的幅度数据 (dBm)。
        """
        # R&S 格式: TRACe:DATA? TRACE1 -> 返回逗号分隔的 ASCII 字符串
        try:
            # 确保数据格式为 ASCII
            self.write("FORM:DATA ASC")
            raw_data = self.query("TRAC:DATA? TRACE1")

            if not raw_data:
                return []

            # 解析数据
            points = [float(x) for x in raw_data.split(',')]
            self.logger.info(f"成功读取 Trace 1，共 {len(points)} 个点")
            return points
        except Exception as e:
            self.logger.error(f"读取 Trace 失败: {e}")
            return []

    def set_display_update(self, enable: bool):
        """
        [扩展] 控制屏幕刷新以提高速度。
        """
        state = "ON" if enable else "OFF"
        self.write(f"SYST:DISP:UPD {state}")
