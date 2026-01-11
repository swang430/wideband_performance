from drivers.common.generic_vna import GenericVNA

class ZNA_Driver(GenericVNA):
    """
    Rohde & Schwarz ZNA 专用驱动。
    """
    
    def __init__(self, resource_name: str, name: str = "RS_ZNA", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def measure_s_parameter(self, parameter: str = "S21") -> str:
        """
        [重写] 完整配置 Trace 并测量。
        """
        trace_name = f"Trc_{parameter}"
        # 1. 定义 Trace: CALC1:PAR:DEF 'Trc_S21', 'S21'
        self.write(f"CALC1:PAR:DEF '{trace_name}', '{parameter}'")
        # 2. 显示 Trace: DISP:WIND1:TRAC1:FEED 'Trc_S21'
        self.write(f"DISP:WIND1:TRAC1:FEED '{trace_name}'")
        
        # 3. 触发并等待
        self.write("INIT1:IMM; *WAI")
        
        # 4. 读取格式化数据 (Real, Imag 或 Magnitude depending on format)
        # 默认设为 Magnitude dB
        self.write(f"CALC1:FORM MLOG") 
        data = self.query(f"CALC1:DATA? FDAT")
        return data
