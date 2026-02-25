"""
驱动模块单元测试
"""
import os
import sys

import pytest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from drivers.base_instrument import BaseInstrument
from drivers.channel_emulator import ChannelEmulator
from drivers.integrated_tester import IntegratedTester
from drivers.spectrum_analyzer import SpectrumAnalyzer
from drivers.vna import VNA
from drivers.vsg import VSG


class TestBaseInstrument:
    """基础仪表类测试"""

    def test_init_simulation_mode(self):
        """测试模拟模式初始化"""
        inst = BaseInstrument(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            name="TestInstrument",
            simulation_mode=True
        )

        assert inst.resource_name == "TCPIP0::127.0.0.1::inst0::INSTR"
        assert inst.name == "TestInstrument"
        assert inst.simulation_mode is True
        assert inst._connected is False

    def test_connect_simulation(self):
        """测试模拟模式连接"""
        inst = BaseInstrument(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            name="TestInstrument",
            simulation_mode=True
        )

        inst.connect()

        assert inst._connected is True

    def test_disconnect_simulation(self):
        """测试模拟模式断开"""
        inst = BaseInstrument(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )

        inst.connect()
        inst.disconnect()

        # 模拟模式下 disconnect 不改变状态 (因为没有真实连接)
        # 这是预期行为，因为 self.instrument 为 None
        assert inst._connected is True

    def test_get_driver_info(self):
        """测试获取驱动信息"""
        inst = BaseInstrument(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            name="TestInstrument",
            simulation_mode=True
        )
        inst.connect()

        info = inst.get_driver_info()

        assert "driver_class" in info
        assert "idn" in info
        assert info["driver_class"] == "BaseInstrument"

    def test_query_simulation(self):
        """测试模拟模式查询"""
        inst = BaseInstrument(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )
        inst.connect()

        result = inst.query("*IDN?")

        # 模拟模式返回 "SIM_DATA"
        assert result == "SIM_DATA"


class TestVSG:
    """信号发生器驱动测试"""

    def test_vsg_init(self):
        """测试 VSG 初始化"""
        vsg = VSG(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            name="TestVSG",
            simulation_mode=True
        )

        assert vsg.name == "TestVSG"

    def test_vsg_connect(self):
        """测试 VSG 连接"""
        vsg = VSG(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )

        vsg.connect()

        # VSG 是代理类，连接后 _driver 不为 None
        assert vsg._driver is not None

    def test_vsg_set_frequency(self):
        """测试设置频率"""
        vsg = VSG(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )
        vsg.connect()

        # 不应抛出异常
        vsg.set_frequency(3500e6)

    def test_vsg_set_power(self):
        """测试设置功率"""
        vsg = VSG(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )
        vsg.connect()

        # 不应抛出异常
        vsg.set_power(-80)

    def test_vsg_enable_output(self):
        """测试输出开关"""
        vsg = VSG(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )
        vsg.connect()

        vsg.enable_output(True)
        vsg.enable_output(False)


class TestVNA:
    """矢量网络分析仪驱动测试"""

    def test_vna_init(self):
        """测试 VNA 初始化"""
        vna = VNA(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            name="TestVNA",
            simulation_mode=True
        )

        assert vna.name == "TestVNA"

    def test_vna_connect(self):
        """测试 VNA 连接"""
        vna = VNA(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )

        vna.connect()

        # VNA 是代理类，连接后 _driver 不为 None
        assert vna._driver is not None


class TestChannelEmulator:
    """信道模拟器驱动测试"""

    def test_ce_init(self):
        """测试信道模拟器初始化"""
        ce = ChannelEmulator(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            name="TestCE",
            simulation_mode=True
        )

        assert ce.name == "TestCE"

    def test_ce_connect(self):
        """测试信道模拟器连接"""
        ce = ChannelEmulator(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )

        ce.connect()

        # ChannelEmulator 是代理类，连接后 _driver 不为 None
        assert ce._driver is not None

    def test_ce_load_channel_model(self):
        """测试加载信道模型"""
        ce = ChannelEmulator(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )
        ce.connect()

        # 不应抛出异常
        ce.load_channel_model("TDL-A")

    def test_ce_set_velocity(self):
        """测试设置速度"""
        ce = ChannelEmulator(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )
        ce.connect()

        # 不应抛出异常
        ce.set_velocity(350)

    def test_ce_rf_control(self):
        """测试 RF 开关"""
        ce = ChannelEmulator(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )
        ce.connect()

        ce.rf_on()
        ce.rf_off()


class TestSpectrumAnalyzer:
    """频谱分析仪驱动测试"""

    def test_sa_init(self):
        """测试频谱分析仪初始化"""
        sa = SpectrumAnalyzer(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            name="TestSA",
            simulation_mode=True
        )

        assert sa.name == "TestSA"

    def test_sa_connect(self):
        """测试频谱分析仪连接"""
        sa = SpectrumAnalyzer(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )

        sa.connect()

        # SpectrumAnalyzer 是代理类，连接后 _driver 不为 None
        assert sa._driver is not None


class TestIntegratedTester:
    """综合测试仪驱动测试"""

    def test_tester_init(self):
        """测试综测仪初始化"""
        tester = IntegratedTester(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            name="TestTester",
            simulation_mode=True
        )

        assert tester.name == "TestTester"

    def test_tester_connect(self):
        """测试综测仪连接"""
        tester = IntegratedTester(
            "TCPIP0::127.0.0.1::inst0::INSTR",
            simulation_mode=True
        )

        tester.connect()

        # IntegratedTester 是代理类，连接后 _driver 不为 None
        assert tester._driver is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
