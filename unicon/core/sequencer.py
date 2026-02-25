import asyncio
import logging
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from drivers.channel_emulator import ChannelEmulator
from drivers.integrated_tester import IntegratedTester
from drivers.spectrum_analyzer import SpectrumAnalyzer
from drivers.vna import VNA
from drivers.vsg import VSG
from dut.android_controller import AndroidController


class TestSequencer:
    """
    编排测试执行的核心逻辑 (Asyncio Version).
    支持 Timeline Strategy (动态场景) 和 Algorithm Strategy (灵敏度/阻塞)。
    """
    def __init__(self, config: Dict[str, Any], simulation_mode: bool = False,
                 log_callback: Optional[Callable[[str], None]] = None,
                 metrics_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.config = config
        self.simulation_mode = simulation_mode
        self.logger = logging.getLogger("Sequencer")
        self.instruments = {}
        self.dut = None
        self.log_callback = log_callback
        self.metrics_callback = metrics_callback  # 新增: 实时指标推送回调

        self._running = False
        self._start_time: Optional[float] = None
        self._elapsed_time = 0.0
        self.current_scenario: Optional[Dict[str, Any]] = None
        self.metrics_history = []

    def _log(self, message: str, level: str = "INFO"):
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
        inst_config = self.config.get('instruments', {})
        self._log("正在初始化仪器连接...")

        factory_map = {
            'vna': (VNA, "VNA"),
            'vsg': (VSG, "VSG"),
            'channel_emulator': (ChannelEmulator, "ChanEm"),
            'integrated_tester': (IntegratedTester, "Tester"),
            'spectrum_analyzer': (SpectrumAnalyzer, "SpecAn")
        }

        for key, (cls, default_name) in factory_map.items():
            if key in inst_config:
                # 避免重复初始化
                if key in self.instruments:
                    continue

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
        dut_conf = self.config.get('dut', {})
        device_id = dut_conf.get('device_id')
        self._log("正在初始化 DUT...")
        self.dut = AndroidController(device_id, simulation_mode=self.simulation_mode)
        try:
            self.dut.connect()
            self._log("✅ DUT 连接成功")
        except Exception as e:
            self._log(f"❌ DUT 连接失败: {e}", level="WARNING")

    # --- Test Strategy Implementations ---

    async def _run_blocking_test(self, scenario_cfg: Dict[str, Any]):
        """
        阻塞干扰测试 (Blocking Test)。
        逻辑: 在主信号建立后，开启 VSG 干扰源，扫描不同频偏和功率。
        """
        self._log(">>> 开始阻塞干扰测试 (Blocking) <<<")
        self._running = True
        self._start_time = asyncio.get_event_loop().time()  # 初始化起始时间

        self._log(f"当前可用仪表: {list(self.instruments.keys())}")

        main_sig = scenario_cfg.get('main_signal', {})
        interferer = scenario_cfg.get('interferer', {})
        try:
            limit_bler = float(scenario_cfg.get('limit', {}).get('max_bler', 0.05))
        except ValueError:
            limit_bler = 0.05

        # 1. 建立主连接
        if 'integrated_tester' in self.instruments:
            try:
                center_freq = float(main_sig.get('freq_hz', 3500e6))
                self._log(f"建立主连接: {center_freq/1e6} MHz")
            except ValueError:
                self._log(f"频率参数错误: {main_sig.get('freq_hz')}", level="ERROR")
                return

            # self.instruments['integrated_tester'].start_call()
            await asyncio.sleep(1)
        else:
            self._log("未找到综测仪 (integrated_tester)，跳过建立连接", level="WARNING")

        # 2. 干扰扫描循环
        start_p = interferer.get('start_power_dbm', -60)
        end_p = interferer.get('end_power_dbm', -30)
        step = interferer.get('step_db', 2)
        offsets = interferer.get('freq_offsets_mhz', [])

        self._log(f"扫描频偏: {offsets}")

        for offset in offsets:
            if not self._running: break

            # 计算干扰频率 (复用已转换的 center_freq，确保类型安全)
            interferer_freq = center_freq + (float(offset) * 1e6)
            self._log(f"=== 测试干扰频偏: {offset} MHz (Freq: {interferer_freq/1e6} MHz) ===")

            if 'vsg' in self.instruments:
                self.instruments['vsg'].set_frequency(interferer_freq)
                self.instruments['vsg'].enable_output(True)

            # 功率爬坡
            current_p = start_p
            while current_p <= end_p and self._running:
                self._log(f"-> 干扰功率: {current_p} dBm")
                if 'vsg' in self.instruments:
                    self.instruments['vsg'].set_power(current_p)

                await asyncio.sleep(0.5) # 测量等待

                # 模拟 BLER 和吞吐量: 功率越高，BLER 越高，吞吐量越低
                sim_bler = 0.0
                sim_throughput = 200.0  # 基准吞吐量 Mbps
                if self.simulation_mode:
                    if current_p > -40:
                        sim_bler = (current_p + 40) * 0.05
                        sim_throughput = max(0, 200 - (current_p + 40) * 10)

                # 推送实时指标到前端
                if self.metrics_callback:
                    self._elapsed_time = asyncio.get_event_loop().time() - (self._start_time or asyncio.get_event_loop().time())
                    self.metrics_callback({
                        "throughput_mbps": round(sim_throughput, 2),
                        "bler": round(sim_bler, 4),
                        "interferer_power_dbm": current_p,
                        "freq_offset_mhz": offset,
                        "elapsed_time": round(self._elapsed_time, 2)
                    })

                if sim_bler > limit_bler:
                    self._log(f"!!! 阻塞失效点: {current_p} dBm (BLER {sim_bler*100:.1f}%) !!!", level="WARNING")
                    break

                current_p += step

            if 'vsg' in self.instruments:
                self.instruments['vsg'].enable_output(False)

        self._running = False

    async def run_sensitivity_test(self, test_case: Dict[str, Any]):
        """
        灵敏度搜索测试 (闭环反馈控制)。
        """
        import random
        start_power = test_case.get('start_power', -70.0)
        end_power = test_case.get('end_power', -110.0)
        step = test_case.get('step', 1.0)
        target_bler = test_case.get('target_bler', 0.05)

        self._log(f">>> 开始灵敏度测试 (目标 BLER: {target_bler*100}%) <<<")
        self._running = True

        current_power = start_power
        sensitivity_point = None

        while current_power >= end_power and self._running:
            self._log(f"-> 设置下行功率: {current_power} dBm")
            if 'vsg' in self.instruments:
                self.instruments['vsg'].set_power(current_power)

            await asyncio.sleep(0.5)

            # 模拟 BLER 和吞吐量
            if self.simulation_mode:
                current_bler = 0.0 if current_power > -100 else 0.1 * ((-100 - current_power))
                # 模拟吞吐量: 基准 200Mbps，随功率下降而降低
                sim_throughput = max(0, 200 - abs(current_power + 70) * 2 + random.uniform(-5, 5))
            else:
                current_bler = 0.0
                sim_throughput = 0.0

            # 推送实时指标
            if self.metrics_callback:
                self.metrics_callback({
                    "throughput_mbps": round(sim_throughput, 2),
                    "bler": round(current_bler, 4),
                    "power_dbm": current_power,
                    "elapsed_time": self._elapsed_time
                })

            self._log(f"   当前 BLER: {current_bler*100:.2f}%")

            if current_bler > target_bler:
                sensitivity_point = current_power
                self._log(f"!!! 发现灵敏度点: {current_power} dBm !!!", level="WARNING")
                break

            current_power -= step

        self._running = False

    async def run_dynamic_scenario(self, scenario_config: Dict[str, Any]):
        """执行基于时间轴的动态场景"""
        import random
        name = scenario_config.get('name', '未命名场景')
        total_duration = scenario_config.get('total_duration', 30)
        timeline = scenario_config.get('timeline', [])
        metrics_interval = scenario_config.get('metrics', {}).get('interval', 0.5)

        # 按时间排序事件
        events = sorted(timeline, key=lambda x: x['time'])

        self._log(f">>> 开始场景: {name} (预计耗时 {total_duration}s) <<<")
        self._start_time = asyncio.get_event_loop().time()
        self._running = True

        event_idx = 0
        last_metrics_time = 0.0

        while self._elapsed_time < total_duration and self._running:
            # 更新已流逝时间
            self._elapsed_time = asyncio.get_event_loop().time() - self._start_time

            # 检查是否有待触发的事件
            while event_idx < len(events) and events[event_idx]['time'] <= self._elapsed_time:
                event = events[event_idx]
                await self._execute_event(event)
                event_idx += 1

            # 定期采样并推送指标
            if self.metrics_callback and (self._elapsed_time - last_metrics_time) >= metrics_interval:
                # 模拟指标数据
                sim_throughput = 180 + random.uniform(-20, 20)
                sim_bler = 0.01 + random.uniform(0, 0.02)
                self.metrics_callback({
                    "throughput_mbps": round(sim_throughput, 2),
                    "bler": round(sim_bler, 4),
                    "elapsed_time": round(self._elapsed_time, 2)
                })
                last_metrics_time = self._elapsed_time

            await asyncio.sleep(0.1)  # Tick 精度 100ms

        self._log(">>> 场景执行流结束 <<<")
        self._running = False

    async def _execute_event(self, event: Dict[str, Any]):
        """执行单个时间轴事件"""
        target = event.get('target')
        action = event.get('action')
        params = event.get('params', {})
        comment = event.get('comment', '')

        self._log(f"执行事件: [{target}] {action} {params} {f'# {comment}' if comment else ''}")

        if target in self.instruments:
            inst = self.instruments[target]
            try:
                func = getattr(inst, action)
                if asyncio.iscoroutinefunction(func):
                    await func(**params)
                else:
                    func(**params)
            except Exception as e:
                self._log(f"事件执行失败: {e}", level="ERROR")
        else:
            self._log(f"未找到目标仪表: {target}", level="WARNING")

    # --- Main Entry ---

    async def run(self):
        """入口函数：根据 current_scenario 分发任务"""
        self._log(f"Config Keys: {list(self.config.keys())}")
        # self._log(f"Scenario Keys: {list(self.current_scenario.keys()) if self.current_scenario else 'None'}")

        # 确保运行标志已开启
        self._running = True

        self.initialize_instruments()
        self.initialize_dut()

        if self.current_scenario:
            cfg = self.current_scenario.get('config', {})
            test_type = cfg.get('type')
            self._log(f"加载场景文件: {self.current_scenario.get('metadata', {}).get('name', 'Unknown')}")

            try:
                if test_type == 'sensitivity':
                    # 适配灵敏度参数
                    search_cfg = cfg.get('search', {})
                    adapt_cfg = {
                        "start_power": search_cfg.get('start_power_dbm'),
                        "end_power": search_cfg.get('end_power_dbm'),
                        "step": search_cfg.get('step_db'),
                        "target_bler": search_cfg.get('target_bler')
                    }
                    await self.run_sensitivity_test(adapt_cfg)

                elif test_type == 'blocking':
                    await self._run_blocking_test(cfg)

                elif test_type == 'dynamic_scenario':
                    # 动态场景通常需要整个 config 部分（包含 timeline）
                    await self.run_dynamic_scenario(cfg)

                else:
                    self._log(f"未知的测试类型: {test_type}", level="ERROR")
            finally:
                self.cleanup()
            return

        # Default: 灵敏度测试 Demo
        self._log("未指定场景，执行默认灵敏度测试...")
        default_case = {
            "name": "Default_Sensitivity",
            "start_power": -90, "end_power": -110, "step": 2, "target_bler": 0.05
        }
        await self.run_sensitivity_test(default_case)
        self.cleanup()

    def stop(self):
        self._log("收到停止信号，正在中止...")
        self._running = False

    def cleanup(self):
        self._log("正在断开所有仪器连接...")
        for name, inst in self.instruments.items():
            try: inst.disconnect()
            except: pass
        self._log("=== 测试序列关闭 ===")
