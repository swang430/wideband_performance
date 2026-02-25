"""
Sequencer 模块单元测试
"""
import os
import sys

import pytest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sequencer import TestSequencer


class TestSequencerInit:
    """Sequencer 初始化测试"""

    def test_init_with_empty_config(self):
        """测试空配置初始化"""
        config = {}
        sequencer = TestSequencer(config, simulation_mode=True)

        assert sequencer.config == {}
        assert sequencer.simulation_mode is True
        assert sequencer.instruments == {}

    def test_init_with_callbacks(self):
        """测试带回调函数的初始化"""
        log_messages = []
        metrics_data = []

        def log_callback(msg):
            log_messages.append(msg)

        def metrics_callback(data):
            metrics_data.append(data)

        config = {"instruments": {}}
        sequencer = TestSequencer(
            config,
            simulation_mode=True,
            log_callback=log_callback,
            metrics_callback=metrics_callback
        )

        assert sequencer.log_callback == log_callback
        assert sequencer.metrics_callback == metrics_callback


class TestSequencerLogging:
    """Sequencer 日志功能测试"""

    def test_log_callback_invoked(self):
        """测试日志回调被正确调用"""
        log_messages = []

        def log_callback(msg):
            log_messages.append(msg)

        config = {}
        sequencer = TestSequencer(config, simulation_mode=True, log_callback=log_callback)

        sequencer._log("测试消息")

        assert len(log_messages) == 1
        assert "测试消息" in log_messages[0]

    def test_log_without_callback(self):
        """测试无回调时不报错"""
        config = {}
        sequencer = TestSequencer(config, simulation_mode=True)

        # 不应抛出异常
        sequencer._log("测试消息")


class TestSequencerInstruments:
    """Sequencer 仪表初始化测试"""

    def test_initialize_with_no_instruments(self):
        """测试无仪表配置时的初始化"""
        config = {"instruments": {}}
        sequencer = TestSequencer(config, simulation_mode=True)

        sequencer.initialize_instruments()

        assert len(sequencer.instruments) == 0

    def test_initialize_with_mock_instruments(self):
        """测试模拟模式下的仪表初始化"""
        config = {
            "instruments": {
                "vsg": {
                    "name": "TestVSG",
                    "address": "TCPIP0::127.0.0.1::inst0::INSTR"
                }
            }
        }

        sequencer = TestSequencer(config, simulation_mode=True)
        sequencer.initialize_instruments()

        assert "vsg" in sequencer.instruments


class TestSequencerExecution:
    """Sequencer 执行测试"""

    @pytest.mark.asyncio
    async def test_sensitivity_test_simulation(self):
        """测试模拟模式下的灵敏度测试"""
        metrics_collected = []

        def metrics_callback(data):
            metrics_collected.append(data)

        config = {"instruments": {}}
        sequencer = TestSequencer(
            config,
            simulation_mode=True,
            metrics_callback=metrics_callback
        )

        test_case = {
            "name": "Test",
            "start_power": -90,
            "end_power": -95,
            "step": 1,
            "target_bler": 0.05
        }

        await sequencer.run_sensitivity_test(test_case)

        # 应该收集到指标数据
        assert len(metrics_collected) > 0
        assert "throughput_mbps" in metrics_collected[0]
        assert "bler" in metrics_collected[0]

    @pytest.mark.asyncio
    async def test_stop_signal(self):
        """测试停止信号"""
        config = {"instruments": {}}
        sequencer = TestSequencer(config, simulation_mode=True)

        sequencer._running = True
        sequencer.stop()

        assert sequencer._running is False


class TestSequencerDynamicScenario:
    """动态场景测试"""

    @pytest.mark.asyncio
    async def test_dynamic_scenario_simulation(self):
        """测试模拟模式下的动态场景"""
        metrics_collected = []

        def metrics_callback(data):
            metrics_collected.append(data)

        config = {"instruments": {}}
        sequencer = TestSequencer(
            config,
            simulation_mode=True,
            metrics_callback=metrics_callback
        )

        scenario_config = {
            "name": "Test Dynamic",
            "total_duration": 2,  # 2秒快速测试
            "timeline": [
                {"time": 0, "target": "vsg", "action": "set_power", "params": {"power": -80}}
            ],
            "metrics": {"interval": 0.5}
        }

        await sequencer.run_dynamic_scenario(scenario_config)

        # 2秒内应该至少收集到几个指标点
        assert len(metrics_collected) >= 2


class TestSequencerCleanup:
    """清理功能测试"""

    def test_cleanup_empty_instruments(self):
        """测试空仪表列表的清理"""
        config = {}
        sequencer = TestSequencer(config, simulation_mode=True)

        # 不应抛出异常
        sequencer.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
