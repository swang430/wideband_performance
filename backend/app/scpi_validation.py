import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml

from drivers.channel_emulator import ChannelEmulator
from drivers.integrated_tester import IntegratedTester
from drivers.power_meter import PowerMeter
from drivers.signal_generator import SignalGenerator
from drivers.field_probe import FieldProbe
from drivers.positioner import Positioner
from drivers.spectrum_analyzer import SpectrumAnalyzer
from drivers.tcu import TCU
from drivers.vna import VNA
from drivers.vsg import VSG


@dataclass
class ValidationStepResult:
    name: str
    status: str
    message: str
    duration_ms: float
    error: Optional[str] = None


SCPI_CATALOG_DIR = Path(__file__).parent.parent / "scpi_catalog"

DEFAULT_SCPI_PLACEHOLDERS = {
    "cell": "CELL1",
    "celltype": "NR5G",
    "resultcell": "CELL1",
    "bwp": "BWP1",
    "bwpn": "BWP1",
    "cbwp": "BWP1",
    "direction": "DL",
    "duplextype": "FDD",
    "technology": "NR5G",
    "sidelink": "SL1",
    "i": "1",
    "s": "1",
    "n": "1",
    "index": "1",
    "no": "1",
    "ch_index": "1",
    "antennas": "1",
    "format": "FORMAT_1",
    "nrotatputcsvresultformat": "FORMAT_1",
    "lteotatputcsvresultformat": "FORMAT_1",
    "nrv2xotatputcsvresultformat": "FORMAT_1",
    "nrv2xcasttype": "UNICAST",
    "nrv2xrespoolid": "0",
}


def _normalize_placeholders(raw: Dict[str, Any]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for key, value in raw.items():
        if key is None:
            continue
        normalized[str(key).strip().lower()] = str(value)
    return normalized


def _auto_placeholder_value(key: str) -> Optional[str]:
    if "cell" in key:
        return "CELL1"
    if "bwp" in key:
        return "BWP1"
    if key in ("i", "s", "n", "index", "no", "ch_index", "antennas"):
        return "1"
    if "sidelink" in key:
        return "SL1"
    if "direction" in key:
        return "DL"
    if "duplex" in key:
        return "FDD"
    if "tech" in key or "technology" in key:
        return "NR5G"
    if "format" in key:
        return "FORMAT_1"
    if "band" in key:
        return "N78"
    if "arfcn" in key:
        return "634666"
    if "freq" in key:
        return "3500000000"
    if "power" in key or "level" in key:
        return "-60"
    if key.endswith("id") or "id" in key or "index" in key or "count" in key or "num" in key:
        return "1"
    if "port" in key or "path" in key:
        return "1"
    if "state" in key:
        return "ON"
    if "mode" in key:
        return "AUTO"
    return None


def _render_scpi_command(template: str, placeholders: Dict[str, str], policy: str) -> Tuple[Optional[str], List[str]]:
    cleaned = re.sub(r"\[[^]]*]", "", template)
    missing: List[str] = []

    def replace(match: re.Match) -> str:
        raw_key = match.group(1).strip()
        key = raw_key.lower()
        if key in placeholders:
            return placeholders[key]
        if policy == "auto":
            auto_value = _auto_placeholder_value(key)
            if auto_value is not None:
                placeholders[key] = str(auto_value)
                return placeholders[key]
        missing.append(key)
        return match.group(0)

    rendered = re.sub(r"<([^>]+)>", replace, cleaned)
    if missing:
        return None, missing
    rendered = re.sub(r"\s+", " ", rendered).strip()
    return rendered, []


def _load_scpi_catalog(catalog_id: str) -> List[Dict[str, Any]]:
    catalog_path = SCPI_CATALOG_DIR / f"{catalog_id}.json"
    if not catalog_path.exists():
        raise FileNotFoundError(f"SCPI catalog not found: {catalog_path}")
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    return payload.get("commands", [])


def _build_scpi_options(
    config: Dict[str, Any],
    instrument_id: str,
    driver: Any,
    override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    options: Dict[str, Any] = {
        "catalog_id": getattr(driver, "scpi_catalog_id", None),
        "include_write": False,
        "max_commands": None,
        "filter_prefix": None,
        "delay_ms": 0,
        "placeholder_policy": "auto",
    }
    placeholders = dict(DEFAULT_SCPI_PLACEHOLDERS)

    validation_cfg = config.get("validation", {})
    scpi_cfg = validation_cfg.get("scpi", {})
    inst_scpi_cfg = (validation_cfg.get(instrument_id) or {}).get("scpi", {})

    def apply(cfg: Dict[str, Any]):
        if not isinstance(cfg, dict):
            return
        if "catalog_id" in cfg:
            options["catalog_id"] = cfg["catalog_id"]
        for key in ("include_write", "max_commands", "filter_prefix", "delay_ms", "placeholder_policy"):
            if key in cfg:
                options[key] = cfg[key]
        if isinstance(cfg.get("placeholders"), dict):
            placeholders.update(_normalize_placeholders(cfg["placeholders"]))

    apply(scpi_cfg)
    apply(inst_scpi_cfg)
    if override:
        apply(override)

    options["placeholders"] = placeholders
    return options


def _build_scpi_catalog_steps(
    driver: Any,
    options: Dict[str, Any],
) -> List[ValidationStepResult]:
    if driver is None:
        return [ValidationStepResult(name="SCPI 目录验证", status="skip", message="驱动不可用", duration_ms=0.0)]

    catalog_id = options.get("catalog_id")
    if not catalog_id:
        return [ValidationStepResult(name="SCPI 目录验证", status="skip", message="未匹配 SCPI 目录", duration_ms=0.0)]

    try:
        commands = _load_scpi_catalog(catalog_id)
    except FileNotFoundError as exc:
        return [
            ValidationStepResult(
                name="SCPI 目录验证",
                status="skip",
                message=f"未找到目录: {catalog_id}",
                duration_ms=0.0,
                error=str(exc),
            )
        ]

    if not commands:
        return [ValidationStepResult(name="SCPI 目录验证", status="skip", message="目录为空", duration_ms=0.0)]

    filter_prefix = options.get("filter_prefix")
    if filter_prefix:
        prefix = str(filter_prefix).upper()
        commands = [cmd for cmd in commands if str(cmd.get("command", "")).upper().startswith(prefix)]

    max_commands = options.get("max_commands")
    if max_commands:
        try:
            limit = max(0, int(max_commands))
            commands = commands[:limit]
        except (TypeError, ValueError):
            pass

    include_write = bool(options.get("include_write"))
    placeholder_policy = str(options.get("placeholder_policy", "auto")).lower()
    placeholders = options.get("placeholders") or {}
    delay_ms = options.get("delay_ms", 0) or 0
    try:
        delay_s = max(0.0, float(delay_ms) / 1000.0)
    except (TypeError, ValueError):
        delay_s = 0.0

    steps: List[ValidationStepResult] = []
    for entry in commands:
        template = str(entry.get("command", "")).strip()
        if not template:
            continue
        rendered, missing = _render_scpi_command(template, placeholders, placeholder_policy)
        if missing:
            steps.append(
                ValidationStepResult(
                    name=f"SCPI {template}",
                    status="skip",
                    message=f"缺少占位符: {', '.join(missing)}",
                    duration_ms=0.0,
                )
            )
            continue

        is_query = bool(entry.get("query", "?" in template))
        if is_query:
            steps.append(_run_step(f"SCPI {rendered}", lambda cmd=rendered: driver.query(cmd)))
        else:
            if not include_write:
                steps.append(
                    ValidationStepResult(
                        name=f"SCPI {rendered}",
                        status="skip",
                        message="写指令默认跳过",
                        duration_ms=0.0,
                    )
                )
            else:
                steps.append(_run_step(f"SCPI {rendered}", lambda cmd=rendered: driver.write(cmd)))

        if delay_s:
            time.sleep(delay_s)

    return steps


def _run_step(name: str, func: Optional[Callable[[], Any]], optional: bool = False) -> ValidationStepResult:
    if func is None:
        return ValidationStepResult(name=name, status="skip", message="未实现或不适用", duration_ms=0.0)

    start = time.perf_counter()
    try:
        result = func()
        message = "OK" if result is None else str(result)
        return ValidationStepResult(
            name=name,
            status="pass",
            message=message,
            duration_ms=(time.perf_counter() - start) * 1000,
        )
    except Exception as exc:
        status = "skip" if optional else "fail"
        message = f"{'跳过' if optional else '失败'}: {exc}"
        return ValidationStepResult(
            name=name,
            status=status,
            message=message,
            duration_ms=(time.perf_counter() - start) * 1000,
            error=str(exc),
        )


def _get_driver(inst: Any) -> Any:
    return getattr(inst, "_driver", None)


def _read_channel_models_from_scenarios() -> List[str]:
    scenarios_dir = Path(__file__).parent.parent / "scenarios"
    if not scenarios_dir.exists():
        return []

    models: List[str] = []
    for scenario_file in scenarios_dir.glob("*.yaml"):
        try:
            data = yaml.safe_load(scenario_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        cfg = (data or {}).get("config", {})
        channel_cfg = cfg.get("channel", {})
        if isinstance(channel_cfg, dict):
            model = channel_cfg.get("model")
            if model:
                models.append(model)
        for event in cfg.get("timeline", []) or []:
            if event.get("target") == "channel_emulator" and event.get("action") == "load_channel_model":
                model = event.get("params", {}).get("model")
                if model:
                    models.append(model)
    return sorted(set(models))


def _resolve_channel_model(config: Dict[str, Any], defaults: Dict[str, Any]) -> str:
    if defaults.get("model"):
        return defaults["model"]

    validation_cfg = config.get("validation", {})
    if validation_cfg.get("channel_model"):
        return validation_cfg["channel_model"]

    for case in config.get("test_cases", []) or []:
        model = case.get("channel_model")
        if model:
            return model

    models = _read_channel_models_from_scenarios()
    if models:
        return models[0]

    return "Static_LOS.scn"


def _build_defaults(config: Dict[str, Any], instrument_id: str, override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    base_defaults = {
        "vsg": {"frequency_hz": 1e9, "power_dbm": -20, "output": False},
        "vna": {"start_freq_hz": 1e9, "stop_freq_hz": 2e9, "points": 201, "power_dbm": -10},
        "spectrum_analyzer": {"center_frequency_hz": 1e9, "span_hz": 10e6, "reference_level_dbm": -10, "rbw_hz": 100e3},
        "channel_emulator": {"model": None, "velocity_kmh": 3.0, "path_loss_db": 80.0, "distance_km": 1.0,
                             "fading_profile": "Rayleigh", "fading_duration_ms": 1000, "rf_on": False},
        "integrated_tester": {"standard": "NR", "frequency_hz": 3.5e9, "bandwidth_mhz": 100, "power_dbm": -85,
                              "tech": "NR"},
        "tcu": {"path": "INT_RELAY_A_1", "attenuator_port": "ATT1", "attenuation_db": 10.0, "amplifier_port": "AMP1"},
        "power_meter": {"frequency_hz": 1e9, "offset_db": 0.0, "burst_count": 5},
        "emgen": {"frequency_hz": 1e9, "power_dbm": -20, "output": False},
        "signal_generator": {"frequency_hz": 1e9, "power_dbm": -20, "output": False},
        "field_probe": {"mode": "normal"},
        "positioner": {"speed": 5.0, "accel": 2.0},
    }

    defaults = dict(base_defaults.get(instrument_id, {}))
    validation_cfg = config.get("validation", {})
    defaults.update(validation_cfg.get("defaults", {}))
    defaults.update(validation_cfg.get(instrument_id, {}))
    if override:
        defaults.update(override)

    if instrument_id == "channel_emulator":
        defaults["model"] = _resolve_channel_model(config, defaults)

    return defaults


def _instrument_factory(instrument_id: str, cfg: Dict[str, Any], simulation_mode: bool):
    mapping: Dict[str, Tuple[Any, str]] = {
        "vna": (VNA, "VNA"),
        "vsg": (VSG, "VSG"),
        "channel_emulator": (ChannelEmulator, "ChanEm"),
        "integrated_tester": (IntegratedTester, "Tester"),
        "spectrum_analyzer": (SpectrumAnalyzer, "SpecAn"),
        "tcu": (TCU, "TCU"),
        "power_meter": (PowerMeter, "PowerMeter"),
        "emgen": (SignalGenerator, "SignalGenerator"),
        "signal_generator": (SignalGenerator, "SignalGenerator"),
        "field_probe": (FieldProbe, "FieldProbe"),
        "positioner": (Positioner, "Positioner"),
    }

    if instrument_id not in mapping:
        raise ValueError(f"不支持的仪表类型: {instrument_id}")

    cls, default_name = mapping[instrument_id]
    name = cfg.get("name", default_name)
    address = cfg.get("address")
    if not address:
        raise ValueError(f"仪表 {instrument_id} 未配置 address")

    kwargs: Dict[str, Any] = {}
    if instrument_id in ("power_meter", "emgen", "signal_generator", "field_probe", "positioner"):
        if "slot" in cfg:
            kwargs["slot"] = cfg["slot"]
    if instrument_id == "power_meter" and "port" in cfg:
        kwargs["port"] = cfg["port"]
    if instrument_id == "integrated_tester" and "driver_hint" in cfg:
        kwargs["driver_hint"] = cfg["driver_hint"]

    inst = cls(address, name=name, simulation_mode=simulation_mode, **kwargs)
    inst.connect()
    return inst


def _build_quick_steps(inst: Any) -> List[ValidationStepResult]:
    steps: List[ValidationStepResult] = []
    driver = _get_driver(inst)

    steps.append(
        _run_step(
            "SCPI *IDN?",
            None if not driver or not hasattr(driver, "query") else lambda: driver.query("*IDN?"),
        )
    )
    steps.append(
        _run_step(
            "SCPI *OPC?",
            None if not driver or not hasattr(driver, "query") else lambda: driver.query("*OPC?"),
            optional=True,
        )
    )
    steps.append(
        _run_step(
            "SCPI SYST:ERR?",
            None if not driver or not hasattr(driver, "query") else lambda: driver.query("SYST:ERR?"),
            optional=True,
        )
    )
    return steps


def _build_full_steps(instrument_id: str, inst: Any, defaults: Dict[str, Any]) -> List[ValidationStepResult]:
    steps: List[ValidationStepResult] = []
    driver = _get_driver(inst)

    def maybe(name: str, method: str, *args: Any, optional: bool = False, **kwargs: Any) -> ValidationStepResult:
        func = None
        if hasattr(inst, method):
            func = lambda: getattr(inst, method)(*args, **kwargs)
        return _run_step(name, func, optional=optional)

    if instrument_id == "vsg":
        steps.append(maybe("设置频率", "set_frequency", defaults["frequency_hz"]))
        steps.append(maybe("设置功率", "set_power", defaults["power_dbm"]))
        steps.append(maybe("关闭输出", "enable_output", defaults["output"], optional=True))

    elif instrument_id == "vna":
        steps.append(maybe("配置扫频", "set_frequency_sweep",
                           defaults["start_freq_hz"], defaults["stop_freq_hz"], defaults["points"]))
        steps.append(maybe("设置功率", "set_power", defaults["power_dbm"]))
        steps.append(maybe("触发测量", "measure_s_parameter", "S21", optional=True))

    elif instrument_id == "spectrum_analyzer":
        steps.append(maybe("设置中心频率", "set_center_frequency", defaults["center_frequency_hz"]))
        steps.append(maybe("设置频率跨度", "set_span", defaults["span_hz"]))
        steps.append(maybe("设置参考电平", "set_reference_level", defaults["reference_level_dbm"]))
        steps.append(maybe("设置 RBW", "set_resolution_bandwidth", defaults["rbw_hz"]))
        steps.append(maybe("峰值搜索", "get_peak_amplitude", optional=True))

    elif instrument_id == "channel_emulator":
        steps.append(maybe("加载信道模型", "load_channel_model", defaults["model"]))
        steps.append(maybe("设置速度", "set_velocity", defaults["velocity_kmh"]))
        steps.append(maybe("设置路损", "set_path_loss", defaults["path_loss_db"]))
        steps.append(maybe("设置距离", "set_distance", defaults["distance_km"], optional=True))
        steps.append(maybe("设置衰落配置", "set_fading_profile",
                           defaults["fading_profile"], defaults["fading_duration_ms"], optional=True))
        steps.append(maybe("RF 开启", "rf_on", optional=True))
        steps.append(maybe("RF 关闭", "rf_off", optional=True))

    elif instrument_id == "integrated_tester":
        steps.append(maybe("设置制式", "set_tech_standard", defaults["standard"]))
        if driver and hasattr(driver, "configure_nr_cell"):
            steps.append(_run_step(
                "配置 NR 小区",
                lambda: driver.configure_nr_cell(
                    defaults["frequency_hz"],
                    defaults["frequency_hz"],
                    int(defaults["bandwidth_mhz"]),
                    30,
                    1,
                ),
            ))
        elif hasattr(inst, "configure_cell"):
            steps.append(maybe("配置小区", "configure_cell",
                               defaults["frequency_hz"], defaults["bandwidth_mhz"], defaults["power_dbm"]))
        steps.append(maybe("启动信令", "start_signaling", defaults.get("tech", "NR"), optional=True))
        steps.append(maybe("停止信令", "stop_signaling", optional=True))
        steps.append(maybe("查询吞吐量", "get_throughput", optional=True))

    elif instrument_id == "tcu":
        steps.append(maybe("切换通路", "switch_rf_path", defaults["path"], optional=True))
        steps.append(maybe("设置衰减", "set_attenuation",
                           defaults["attenuator_port"], defaults["attenuation_db"], optional=True))
        steps.append(maybe("开关放大器", "enable_amplifier",
                           defaults["amplifier_port"], False, optional=True))
        steps.append(maybe("查询开关状态", "get_switch_state", defaults["path"], optional=True))

    elif instrument_id in ("emgen", "signal_generator"):
        steps.append(maybe("设置频率", "set_frequency", defaults["frequency_hz"]))
        steps.append(maybe("设置功率", "set_power", defaults["power_dbm"]))
        steps.append(maybe("关闭输出", "enable_output", defaults["output"], optional=True))
        steps.append(maybe("查询频率", "get_frequency", optional=True))
        steps.append(maybe("查询功率", "get_power", optional=True))

    elif instrument_id == "power_meter":
        steps.append(maybe("设置频率", "set_frequency", defaults["frequency_hz"], optional=True))
        steps.append(maybe("设置校准偏移", "calibrate", defaults["offset_db"], optional=True))
        steps.append(maybe("读取功率", "read_power", optional=True))
        steps.append(maybe("连续读取功率", "read_power_burst", defaults["burst_count"], optional=True))

    elif instrument_id == "field_probe":
        steps.append(maybe("设置测量模式", "set_mode", defaults["mode"], optional=True))
        steps.append(maybe("读取场强", "read_field", optional=True))
        steps.append(maybe("查询激光状态", "get_laser_status", optional=True))

    elif instrument_id == "positioner":
        steps.append(maybe("设置速度", "set_speed", defaults["speed"], optional=True))
        steps.append(maybe("设置加速度", "set_acceleration", defaults["accel"], optional=True))
        steps.append(maybe("查询位置", "get_position", optional=True))
        steps.append(maybe("查询运动状态", "is_moving", optional=True))
        steps.append(maybe("查询电机状态", "get_motor_status", optional=True))

    else:
        steps.append(_run_step("未定义的完整验证步骤", None))

    return steps


def run_scpi_validation(
    instrument_id: str,
    config: Dict[str, Any],
    mode: str,
    simulation_mode: bool,
    override_params: Optional[Dict[str, Any]] = None,
    scpi_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    inst_cfg = (config.get("instruments") or {}).get(instrument_id)
    if not inst_cfg:
        raise ValueError(f"未找到仪表配置: {instrument_id}")

    inst = _instrument_factory(instrument_id, inst_cfg, simulation_mode)

    start_time = time.time()
    steps: List[ValidationStepResult] = []

    try:
        if scpi_override is None and isinstance(override_params, dict):
            scpi_override = override_params.get("scpi")
        steps.extend(_build_quick_steps(inst))
        if mode == "full":
            defaults = _build_defaults(config, instrument_id, override_params)
            steps.extend(_build_full_steps(instrument_id, inst, defaults))
        elif mode == "full_scpi":
            driver = _get_driver(inst)
            scpi_options = _build_scpi_options(config, instrument_id, driver, scpi_override)
            steps.extend(_build_scpi_catalog_steps(driver, scpi_options))
    finally:
        inst.disconnect()

    duration_ms = (time.time() - start_time) * 1000
    summary = {"pass": 0, "fail": 0, "skip": 0}
    for step in steps:
        summary[step.status] = summary.get(step.status, 0) + 1

    driver_info = inst.get_driver_info() if hasattr(inst, "get_driver_info") else None

    return {
        "instrument_id": instrument_id,
        "mode": mode,
        "simulation_mode": simulation_mode,
        "driver_info": driver_info,
        "duration_ms": round(duration_ms, 2),
        "summary": summary,
        "steps": [step.__dict__ for step in steps],
    }
