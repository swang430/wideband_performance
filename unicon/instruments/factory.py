import logging
from typing import Any, Type

# Channel Emulator
from .common.generic_ce import GenericChannelEmulator

# SA
from .common.generic_sa import GenericSA

# Tester
from .common.generic_tester import GenericTester

# VNA
from .common.generic_vna import GenericVNA

# VSG
from .common.generic_vsg import GenericVSG
from .keysight.propsim import PROPSIM_Driver
from .rohde_schwarz.cmw500 import CMW500_Driver
from .rohde_schwarz.fsw import FSW_Driver
from .rohde_schwarz.smw200a import SMW200A_Driver
from .rohde_schwarz.zna import ZNA_Driver
from .spirent.vertex import Vertex_Driver

# 注册表
VSG_REGISTRY = {"SMW": SMW200A_Driver}
SA_REGISTRY = {"FSW": FSW_Driver}
VNA_REGISTRY = {"ZNA": ZNA_Driver}
TESTER_REGISTRY = {"CMW": CMW500_Driver}
CE_REGISTRY = {
    "Vertex": Vertex_Driver,
    "PROPSIM": PROPSIM_Driver,
    "F64": PROPSIM_Driver
}

class DriverFactory:
    """
    驱动工厂，负责根据仪表 IDN 自动创建对应的驱动实例。
    """
    def __init__(self):
        self.logger = logging.getLogger("DriverFactory")

    @staticmethod
    def _create_driver(resource_name: str, idn_string: str, registry: dict, default_class: Type, simulation_mode: bool) -> Any:
        logger = logging.getLogger("DriverFactory")
        for keyword, driver_class in registry.items():
            if keyword in idn_string:
                logger.info(f"识别到仪表 ({keyword})，加载驱动: {driver_class.__name__}")
                return driver_class(resource_name, name=keyword, simulation_mode=simulation_mode)

        logger.warning(f"未识别的仪表 IDN ('{idn_string}')，加载通用驱动: {default_class.__name__}")
        return default_class(resource_name, name="Generic", simulation_mode=simulation_mode)

    @staticmethod
    def create_vsg_driver(resource_name: str, idn_string: str, simulation_mode: bool = False) -> GenericVSG:
        return DriverFactory._create_driver(resource_name, idn_string, VSG_REGISTRY, GenericVSG, simulation_mode)

    @staticmethod
    def create_sa_driver(resource_name: str, idn_string: str, simulation_mode: bool = False) -> GenericSA:
        return DriverFactory._create_driver(resource_name, idn_string, SA_REGISTRY, GenericSA, simulation_mode)

    @staticmethod
    def create_vna_driver(resource_name: str, idn_string: str, simulation_mode: bool = False) -> GenericVNA:
        return DriverFactory._create_driver(resource_name, idn_string, VNA_REGISTRY, GenericVNA, simulation_mode)

    @staticmethod
    def create_tester_driver(resource_name: str, idn_string: str, simulation_mode: bool = False) -> GenericTester:
        return DriverFactory._create_driver(resource_name, idn_string, TESTER_REGISTRY, GenericTester, simulation_mode)

    @staticmethod
    def create_chan_em_driver(resource_name: str, idn_string: str, simulation_mode: bool = False) -> GenericChannelEmulator:
        return DriverFactory._create_driver(resource_name, idn_string, CE_REGISTRY, GenericChannelEmulator, simulation_mode)
