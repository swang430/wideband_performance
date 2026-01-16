from drivers.common.generic_ce import GenericChannelEmulator


class PROPSIM_Driver(GenericChannelEmulator):
    """
    Keysight (Anite) PROPSIM F64 信道模拟器驱动。
    已根据 Propsim User Reference (ATE 章节) 验证。
    """

    def __init__(self, resource_name: str, name: str = "Keysight_PROPSIM", simulation_mode: bool = False):
        super().__init__(resource_name, name, simulation_mode)

    def load_channel_model(self, model: str):
        """
        加载仿真模型。
        """
        self.logger.info(f"PROPSIM 加载模型: {model}")
        # 根据 PROPSIM ATE 语法，参数间空格，字符串通常不带引号
        self.write(f"CALCulate:FILTer:FILE {model}")

        # 检查错误
        err = self.query("SYSTem:ERRor?")
        if "0," not in err:
            self.logger.error(f"PROPSIM 加载模型报错: {err}")

    def set_velocity(self, kmh: float):
        """
        设置移动速度 (km/h)。
        Ref: Propsim User Reference (ATE Commands)
        Command: DIAGnostic:SIMUlation:MOBilespeed:MANual:CH <ch>, <speed>
        """
        self.logger.info(f"PROPSIM 设置速度: {kmh} km/h")
        # 对通道 1 设置速度
        self.write(f"DIAGnostic:SIMUlation:MOBilespeed:MANual:CH 1,{kmh}")

    def rf_on(self):
        """
        开始仿真并开启发射。
        """
        self.write("SIMulation:STARt")
        self.logger.info("PROPSIM: 仿真已启动")

    def rf_off(self):
        """
        停止所有发射。
        """
        self.write("SYSTem:TRANSmitter:OFF")
        self.logger.info("PROPSIM: 所有射频输出已关闭")

    # === 场景测试扩展方法 ===
    # Ref: manual_library/channel_emulator/Keysight_PROPSIM/Propsim ATE environment and practices AN.pdf

    def set_path_loss(self, db: float):
        """
        设置路径损耗/增益 (dB)。
        Ref: Propsim User Reference, 'Remote Control, ATE' chapter
        
        PROPSIM 通过调整通道增益来实现路损变化。
        """
        # 增益设置 (负值表示衰减)
        # DIAG:SIMU:GAIN:CH <channel>,<gain_dB>
        attenuation = -abs(db)  # 路损为负增益
        self.write(f"DIAG:SIMU:GAIN:CH 1,{attenuation}")
        self.logger.info(f"PROPSIM 设置路径损耗: {db} dB (通道 1)")

    def set_distance(self, km: float):
        """
        设置模拟距离 (km)。
        PROPSIM 通过调整增益模拟距离效应。
        """
        # 使用自由空间路损公式近似 (假设 3.5GHz)
        # FSPL = 20*log10(d) + 20*log10(f) + 32.44
        import math
        fspl = 20 * math.log10(max(km, 0.1)) + 20 * math.log10(3500) + 32.44
        self.set_path_loss(fspl)
        self.logger.info(f"PROPSIM 模拟距离: {km} km (FSPL: {fspl:.1f} dB)")

    def set_fading_profile(self, profile: str, duration_ms: int = 0):
        """
        切换衰落配置。
        Ref: Propsim ATE AN, p.12 (Fading Channels)
        
        PROPSIM 主要通过加载不同仿真文件来切换衰落配置。
        运行时可调整的参数有限。
        """
        if profile == "deep_fade":
            # 临时增加通道衰减模拟深衰落
            self.write("DIAG:SIMU:GAIN:CH 1,-30")
            self.logger.info(f"PROPSIM 模拟深衰落事件 ({duration_ms}ms)")
        elif profile == "bypass":
            # 校准旁路模式
            self.write("DIAG:SIMU:GAIN:CH 1,-10")
            self.logger.info("PROPSIM 切换到旁路模式")
        else:
            self.logger.warning(f"PROPSIM 不支持运行时衰落配置: {profile}，建议通过仿真文件预定义")

    def trigger_handover(self, target_cell: int):
        """
        触发小区切换模拟。
        Ref: Propsim User Reference, p.23 (Handover)
        
        PROPSIM 通过 Shadowing 编辑器配置切换触发，此处调整增益模拟切换效果。
        """
        self.logger.info(f"PROPSIM 模拟切换到小区 {target_cell}")
        # 模拟切换过程中的信号变化
        # 1. 源小区信号减弱
        self.write("DIAG:SIMU:GAIN:CH 1,-20")
        # 2. 目标小区信号增强 (假设通道 2)
        self.write("DIAG:SIMU:GAIN:CH 2,0")
