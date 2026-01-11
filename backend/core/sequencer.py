import logging
import asyncio
import time
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

from drivers.vna import VNA
from drivers.vsg import VSG
from drivers.channel_emulator import ChannelEmulator
from drivers.integrated_tester import IntegratedTester
from drivers.spectrum_analyzer import SpectrumAnalyzer
from dut.android_controller import AndroidController

class TestSequencer:
    """
    编排测试执行的核心逻辑 (Asyncio Version).
    """
    def __init__(self, config: Dict[str, Any], simulation_mode: bool = False, log_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger("Sequencer")
        self.instruments = {}
        self.dut = None
        self.log_callback = log_callback
        self._running = False

    def _log(self, message: str, level: str = "INFO"):
        """
        统一日志记录：同时输出到 Python Logger 和 回调函数 (WebSocket)。
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
            
        if self.log_callback:
            try:
                self.log_callback(formatted_msg) 
            except Exception as e:
                self.logger.error(f"日志回调执行失败: {e}")

    def initialize_instruments(self):
        """
        初始化并连接配置中定义的所有仪器。
        """
        inst_config = self.config.get('instruments', {})
        self._log("正在初始化仪器连接...")
        
        # 定义仪器工厂映射
        factory_map = {
            'vna': (VNA, "VNA"),
            'vsg': (VSG, "VSG"),
            'channel_emulator': (ChannelEmulator, "ChanEm"),
            'integrated_tester': (IntegratedTester, "Tester"),
            'spectrum_analyzer': (SpectrumAnalyzer, "SpecAn")
        }

        for key, (cls, default_name) in factory_map.items():
            if key in inst_config:
                cfg = inst_config[key]
                name = cfg.get('name', default_name)
                address = cfg['address']
                
                try:
                    self._log(f"正在连接 {name} ({address})...")
                    inst = cls(address, name=name, simulation_mode=self.simulation_mode)
                    inst.connect()
                    self.instruments[key] = inst
                    self._log(f"✅ {name} 连接成功")
                except Exception as e:
                    err_msg = f"❌ {name} 连接失败: {e}"
                    self._log(err_msg, level="ERROR")
                    print(f"!!! Exception during {name} init !!!")
                    traceback.print_exc()

    def initialize_dut(self):
        """
        初始化 DUT 控制。
        """
        dut_conf = self.config.get('dut', {})
        device_id = dut_conf.get('device_id')
        self._log("正在初始化 DUT...")
        self.dut = AndroidController(device_id, simulation_mode=self.simulation_mode)
        try:
            self.dut.connect()
            self._log("✅ DUT 连接成功")
        except Exception as e:
            self._log(f"❌ DUT 连接失败: {e}", level="WARNING")

    async def run(self):
        """
        运行测试序列 (Async Entry)。
        """
        self._running = True
        self._log("=== 测试序列启动 ===")
        
        # 1. 初始化资源
        self.initialize_instruments()
        self.initialize_dut()

        # 2. 执行测试用例
        test_cases = self.config.get('test_cases', [])
        for test in test_cases:
            if not self._running: break
            await self.run_test_case(test)

        # 3. 清理
        self.cleanup()
        self._running = False

    async def run_test_case(self, test_case: Dict[str, Any]):
        """
        执行单个测试用例。
        """
        name = test_case.get('name', 'Unknown')
        self._log(f"--- 开始执行用例: {name} ---")
        
        t_type = test_case.get('type')
        try:
            if t_type == 'throughput':
                await self._run_throughput_test(test_case)
            else:
                self._log(f"跳过未知类型用例: {t_type}", level="WARNING")
        except Exception as e:
            self._log(f"❌ 用例 {name} 执行异常: {e}", level="ERROR")
            import traceback
            self.logger.error(traceback.format_exc())

    async def _run_throughput_test(self, test_case: Dict[str, Any]):
        try:
            duration = int(test_case.get('duration', 10))
            freqs = [float(f) for f in test_case.get('frequencies', [])]
        except ValueError as e:
            self._log(f"❌ 配置参数类型错误: {e}", level="ERROR")
            return

        # 1. 准备信道环境
        if 'chan_em' in self.instruments:
            model = test_case.get('channel_model')
            if model:
                self._log(f"正在配置信道模拟器: {model}")
                self.instruments['chan_em'].load_channel_model(model)
                self.instruments['chan_em'].rf_on()

        # 2. 准备综测仪 (如果存在)
        if 'tester' in self.instruments:
            self._log("正在建立综测仪信令连接...")
            self.instruments['tester'].set_tech_standard("LTE") # 示例
            self.instruments['tester'].start_call()
            # 简单等待连接建立
            await asyncio.sleep(2) 

        # 3. 循环频率点测试
        for freq in freqs:
            if not self._running: break
            
            self._log(f"-> 切换测试频率: {freq/1e6} MHz")
            
            # 配置 VSG (作为干扰源或信号源)
            if 'vsg' in self.instruments:
                self.instruments['vsg'].set_frequency(freq)
                self.instruments['vsg'].enable_output(True)
            
            # 配置频谱仪
            if 'spec_an' in self.instruments:
                self.instruments['spec_an'].set_center_frequency(freq)
                self.instruments['spec_an'].set_span(100e6)
            
            # 运行流量
            self._log(f"   开始打流 (持续 {duration}s)...")
            
            if self.simulation_mode:
                # 模拟进度条
                for i in range(duration):
                    if not self._running: break
                    await asyncio.sleep(1)
                    # self._log(f"   ... {i+1}/{duration}s")
            elif self.dut:
                # 真实 DUT 操作
                # 注意: start_traffic 目前是同步阻塞的，未来应改为异步
                self.dut.start_traffic("192.168.1.50", duration=duration)
                await asyncio.sleep(duration)
            
            self._log(f"   频率 {freq/1e6} MHz 测试完成")

        # 4. 拆除环境
        if 'vsg' in self.instruments:
            self.instruments['vsg'].enable_output(False)
        if 'chan_em' in self.instruments:
            self.instruments['chan_em'].rf_off()
        if 'tester' in self.instruments:
            self.instruments['tester'].stop_call()

    def stop(self):
        """
        请求停止测试。
        """
        self._log("收到停止信号，正在中止...")
        self._running = False

    def cleanup(self):
        """
        关闭连接。
        """
        self._log("正在断开所有仪器连接...")
        for name, inst in self.instruments.items():
            try:
                inst.disconnect()
            except:
                pass
        self._log("=== 测试序列结束 ===")