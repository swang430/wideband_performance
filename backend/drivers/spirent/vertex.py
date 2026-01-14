from drivers.common.generic_ce import GenericChannelEmulator

class Vertex_Driver(GenericChannelEmulator):
    """
    Spirent Vertex 信道模拟器驱动。
    已根据 Vertex User Guide (RPI 章节) 验证。
    """
    
    def __init__(self, resource_name: str, name: str = "Spirent_Vertex", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def load_channel_model(self, model_name: str):
        """
        加载场景文件 (.scn)。
        """
        if not model_name.endswith(".scn"):
            model_name += ".scn"
            
        self.logger.info(f"Vertex 加载场景: {model_name}")
        # 根据 RPI 规范加载
        self.write(f"SYS:FILE:LOAD '{model_name}'")
        
        # 验证加载结果
        res = self.query("*OPC?")
        err = self.query(":ERR?")
        if "0," not in err and "No Error" not in err:
            self.logger.error(f"Vertex 加载场景失败: {err}")
        else:
            self.logger.info("Vertex 场景加载成功")

    def set_velocity(self, velocity_kmh: float):
        """
        设置移动速度 (km/h)。
        Ref: Vertex User Guide, p.69 (MSVelocity parameter)
        Command: CHM1:GCM:PATH1:MSVelocity <val>
        """
        self.logger.info(f"Vertex 设置速度: {velocity_kmh} km/h (Target: CH1/Path1)")
        # 假设当前模型处于 GCM 模式，或者 Vertex 能智能识别
        self.write(f"CHM1:GCM:PATH1:MSVelocity {velocity_kmh}")

    def rf_on(self):
        """
        开始播放场景。
        """
        # Vertex 通常在加载并设置好端口后通过此指令开启
        self.write("OUTP:STAT ON")
        self.logger.info("Vertex: 射频输出/场景播放已开启")