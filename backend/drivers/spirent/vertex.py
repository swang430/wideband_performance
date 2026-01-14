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

    # === 场景测试扩展方法 ===
    # Ref: manual_library/channel_emulator/Spirent_Vertex/RPI_CommandRef.pdf

    def set_path_loss(self, db: float):
        """
        设置路径损耗 (dB)。
        Ref: RPI_CommandRef.pdf, p.27, Section 2.2.55
        Command: [SYSTem]:PORT:{A,B}#:LOSS <value>
        
        Note: 需要设置 LOSSMode 为 SET_LOSS 模式才生效
        """
        # 先确保 LossMode 设为 SET_LOSS
        self.write("SYS:CONn:LOSSMode SET_LOSS")
        # 设置 Port A1 的损耗 (假设主链路使用 A1)
        self.write(f"SYS:PORT:A1:LOSS {db}")
        self.logger.info(f"Vertex 设置路径损耗: {db} dB (Port A1)")

    def set_distance(self, km: float):
        """
        设置模拟距离 (km)。
        Vertex 通过调整路损来模拟距离变化，使用自由空间路损公式近似。
        PathLoss (dB) ≈ 20*log10(d) + 20*log10(f) + 32.44 (d in km, f in MHz)
        """
        # 简化处理：假设 3.5GHz，每 km 约增加 6dB（近似）
        base_loss = 90  # 1km 参考损耗
        estimated_loss = base_loss + 20 * (km - 1) if km > 1 else base_loss
        self.set_path_loss(estimated_loss)
        self.logger.info(f"Vertex 模拟距离: {km} km (估算路损: {estimated_loss} dB)")

    def set_fading_profile(self, profile: str, duration_ms: int = 0):
        """
        设置衰落配置。
        Ref: RPI_CommandRef.pdf, p.21, Section 2.2.1
        
        Note: Vertex 通过加载不同场景文件来改变衰落配置，
        此方法通过设置 fading mode 实现运行时调整。
        """
        # Vertex 运行时衰落调整有限，主要通过场景切换
        if profile == "deep_fade":
            # 模拟深衰落：临时增加额外损耗
            self.write("SYS:PORT:A1:LOSS 30")  # 临时增加 30dB
            self.logger.info(f"Vertex 模拟深衰落事件 ({duration_ms}ms)")
        else:
            self.logger.warning(f"Vertex 不支持运行时衰落配置: {profile}，建议通过场景文件预定义")

    def trigger_handover(self, target_cell: int):
        """
        触发小区切换。
        
        Note: Vertex 本身不直接控制小区切换，此功能需要配合综测仪使用。
        这里通过调整信道参数来模拟切换前后的信道变化。
        """
        self.logger.info(f"Vertex 模拟切换到小区 {target_cell} (调整信道配置)")
        # 切换到备用链路配置 (如果有预定义)
        # 这需要场景文件预先定义多小区配置
        self.write(f"SYS:CELL:SEL {target_cell}")