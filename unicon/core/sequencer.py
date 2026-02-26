import asyncio
import logging
import traceback
import importlib
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from unicon.dut.android_controller import AndroidController

class TestSequencer:
    """
    编排测试执行的核心逻辑 (Asyncio Version).
    支持 Timeline Strategy (动态场景)。
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
        self.metrics_callback = metrics_callback

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
        elif level == "TRACE":
            if hasattr(self.logger, "trace"):
                self.logger.trace(message)
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

        for key, cfg in inst_config.items():
            if key in self.instruments:
                continue
                
            driver_class_name = cfg.get('driver_class')
            address = cfg.get('address')
            name = cfg.get('name', key)

            if not driver_class_name:
                self._log(f"仪器 {key} 缺少 driver_class 配置，跳过初始化。", level="WARNING")
                continue

            try:
                # 动态加载驱动类 (基于反射)
                module = importlib.import_module('unicon.instruments')
                driver_class = getattr(module, driver_class_name)
                
                self._log(f"正在连接 {name} ({address}) using {driver_class_name}...")
                inst = driver_class(resource_name=address, name=name, simulation_mode=self.simulation_mode)
                inst.connect()
                self.instruments[key] = inst
                self._log(f"✅ {name} 连接成功")
            except Exception as e:
                err_msg = f"❌ {name} 连接失败: {e}"
                self._log(err_msg, level="ERROR")
                traceback.print_exc()

    def initialize_dut(self):
        dut_conf = self.config.get('dut', {})
        device_id = dut_conf.get('device_id')
        if not device_id:
            return
            
        self._log("正在初始化 DUT...")
        self.dut = AndroidController(device_id, simulation_mode=self.simulation_mode)
        try:
            self.dut.connect()
            self._log("✅ DUT 连接成功")
        except Exception as e:
            self._log(f"❌ DUT 连接失败: {e}", level="WARNING")

    async def run_dynamic_scenario(self, scenario_config: Dict[str, Any]):
        """执行基于时间轴的非阻塞动态场景"""
        name = scenario_config.get('name', '未命名场景')
        total_duration = scenario_config.get('total_duration', 30)
        timeline = scenario_config.get('timeline', [])
        
        # 按时间排序事件
        events = sorted(timeline, key=lambda x: x['time'])

        self._log(f">>> 开始动态场景: {name} (预计耗时 {total_duration}s) <<<")
        
        loop = asyncio.get_running_loop()
        self._start_time = loop.time()
        self._running = True

        event_idx = 0
        
        # 将事件投递到异步任务中执行，以实现非阻塞调度
        while self._running:
            self._elapsed_time = loop.time() - self._start_time
            
            if self._elapsed_time >= total_duration:
                break

            while event_idx < len(events) and events[event_idx]['time'] <= self._elapsed_time:
                event = events[event_idx]
                # 使用 create_task 防止阻塞主时间轴循环
                asyncio.create_task(self._execute_event(event))
                event_idx += 1

            await asyncio.sleep(0.05)  # 50ms tick precision

        self._log(">>> 场景执行结束 <<<")
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
                # 递归解析属性 (例如 wlan.configure_rf)
                obj = inst
                parts = action.split('.')
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                func = getattr(obj, parts[-1])
                
                # 在线程池中执行同步的仪器 I/O，防止阻塞 event loop
                await asyncio.to_thread(func, **params)
            except Exception as e:
                self._log(f"事件执行失败: {e}", level="ERROR")
        else:
            self._log(f"未找到目标仪表: {target}", level="WARNING")

    async def run(self):
        """入口函数"""
        self._running = True
        self.initialize_instruments()
        self.initialize_dut()

        if self.current_scenario:
            cfg = self.current_scenario.get('config', {})
            test_type = cfg.get('type')
            self._log(f"加载场景: {self.current_scenario.get('metadata', {}).get('name', 'Unknown')}")

            try:
                if test_type == 'dynamic_scenario':
                    await self.run_dynamic_scenario(cfg)
                else:
                    self._log(f"未知的测试类型: {test_type}", level="ERROR")
            finally:
                self.cleanup()
            return
            
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
