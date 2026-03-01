import os
import sys
import asyncio
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from unicon.core.config_loader import ConfigLoader
from unicon.instruments.base_instrument import BaseInstrument
import importlib

router = APIRouter()

# --- 全局单例：仪器连接池 ---
class InstrumentPool:
    def __init__(self):
        self.instruments: Dict[str, BaseInstrument] = {}

    def get_instrument(self, inst_id: str) -> BaseInstrument:
        if inst_id not in self.instruments:
            raise HTTPException(status_code=404, detail=f"Instrument {inst_id} not connected")
        return self.instruments[inst_id]

    def connect_all(self, config: dict, simulation_mode: bool = True):
        inst_config = config.get('instruments', {})
        for key, cfg in inst_config.items():
            if key in self.instruments:
                continue
            driver_class_name = cfg.get('driver_class')
            address = cfg.get('address')
            name = cfg.get('name', key)
            if not driver_class_name:
                continue
            try:
                module = importlib.import_module('unicon.instruments')
                driver_class = getattr(module, driver_class_name)
                inst = driver_class(resource_name=address, name=name, simulation_mode=simulation_mode)
                inst.connect()
                self.instruments[key] = inst
            except Exception as e:
                print(f"Failed to connect {name}: {e}")

    def disconnect_all(self):
        for key, inst in list(self.instruments.items()):
            try:
                inst.disconnect()
            except:
                pass
        self.instruments.clear()

pool = InstrumentPool()

# --- Data Models ---
class HealthResponse(BaseModel):
    status: str
    version: str

class InstrumentStatus(BaseModel):
    id: str
    name: str
    address: str
    connected: bool
    driver_class: str

class ScpiCommand(BaseModel):
    instrument_id: str
    command: str
    is_query: bool = True
    timeout_ms: int = 5000

class ScpiResponse(BaseModel):
    instrument_id: str
    command: str
    response: Optional[str] = None
    error: Optional[str] = None

class BatchScpiRequest(BaseModel):
    instrument_id: str
    commands: List[str]

class BatchScpiResponse(BaseModel):
    instrument_id: str
    results: List[Dict[str, Any]]

class ProbeRequest(BaseModel):
    manual_address: Optional[str] = None

class ProbeResult(BaseModel):
    address: str
    idn: str
    status: str
    configured_as: Optional[str] = None

class InstrumentConfigItem(BaseModel):
    id: str
    address: str
    driver_class: str
    name: str

class UpdateConfigRequest(BaseModel):
    instruments: List[InstrumentConfigItem]

class MethodExecutionRequest(BaseModel):
    method_name: str
    kwargs: Dict[str, Any]

# --- API Endpoints ---

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok", "version": "0.2.0"}

@router.post("/instruments/probe", response_model=List[ProbeResult])
async def probe_instruments(req: ProbeRequest):
    """
    扫描局域网 VISA 资源，支持补充手动地址验证。
    """
    import pyvisa
    
    results = []
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "unicon", "config.yaml")
    
    configured_addresses = {}
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
            for k, v in cfg.get('instruments', {}).items():
                if 'address' in v:
                    configured_addresses[v['address']] = k
    except:
        pass

    try:
        # 强制使用纯 Python 后端，避免 NI-VISA C 库导致的各种玄学闪退
        rm = pyvisa.ResourceManager('@py')
        resources = []
        
        # 现在已经通过 hidden-imports 解决了依赖问题，可以安全地在所有环境执行广播嗅探
        try:
            # list_resources 会触发 mDNS 和 VXI-11 发现机制
            resources = list(rm.list_resources())
        except Exception as e:
            print(f"[Probe] Auto-discovery failed: {e}")
                
        # 如果用户提供了手动地址，且不在扫描结果中，则加入探测列表
        if req.manual_address and req.manual_address not in resources:
            resources.append(req.manual_address)
            
        # 如果 config.yaml 里配置了地址，也加入探测列表做对比验证
        for addr in configured_addresses.keys():
            if addr not in resources:
                resources.append(addr)
            
        for addr in resources:
            # We skip ASRL/COM ports usually unless specifically requested, but let's test all TCPIP or GPIB
            if not addr.startswith("TCPIP") and not addr.startswith("GPIB") and addr != req.manual_address:
                continue
                
            res_info = ProbeResult(address=addr, idn="Unknown", status="timeout")
            if addr in configured_addresses:
                res_info.configured_as = configured_addresses[addr]
                
            try:
                # Set a short timeout for probing to avoid long hangs
                inst = rm.open_resource(addr, open_timeout=2000)
                inst.timeout = 2000
                idn = inst.query("*IDN?")
                res_info.idn = idn.strip()
                res_info.status = "success"
                inst.close()
            except Exception as e:
                res_info.status = "error"
                res_info.idn = str(e)
            
            results.append(res_info)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return results

@router.post("/config/instruments")
async def update_instrument_config(req: UpdateConfigRequest):
    """
    更新 config.yaml 中的仪器配置，实现根据 Probe 结果对图纸的真实修正
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "unicon", "config.yaml")
    
    cfg = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
            
    if 'instruments' not in cfg:
        cfg['instruments'] = {}
        
    # 根据提交的列表全量替换或更新
    new_instruments = {}
    for item in req.instruments:
        new_instruments[item.id] = {
            "name": item.name,
            "address": item.address,
            "driver_class": item.driver_class
        }
        
    cfg['instruments'] = new_instruments
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(cfg, f, allow_unicode=True, sort_keys=False)
        
    return {"message": "Config updated successfully"}

@router.post("/instruments/connect")
async def connect_instruments(simulation_mode: bool = True):
    """根据 config.yaml 建立所有仪器的连接池"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "unicon", "config.yaml")
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="config.yaml not found in unicon/")
        
    loader = ConfigLoader(config_path)
    config = loader.load()
    pool.connect_all(config, simulation_mode=simulation_mode)
    return {"message": f"Connected to {len(pool.instruments)} instruments"}

@router.post("/instruments/disconnect")
async def disconnect_instruments():
    """断开所有仪器"""
    pool.disconnect_all()
    return {"message": "All instruments disconnected"}

@router.get("/instruments/status", response_model=List[InstrumentStatus])
async def get_instruments_status():
    """获取仪器状态：合并 config.yaml 配置与当前连接池状态"""
    results = []
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "unicon", "config.yaml")
    
    config = {}
    if os.path.exists(config_path):
        # 避免频繁刷新的日志轰炸，可以直接静默加载
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except:
            pass
            
    inst_config = config.get('instruments', {})
    
    for key, cfg in inst_config.items():
        if key in pool.instruments:
            inst = pool.instruments[key]
            results.append(InstrumentStatus(
                id=key,
                name=inst.name,
                address=inst.resource_name,
                connected=inst._connected,
                driver_class=inst.__class__.__name__
            ))
        else:
            results.append(InstrumentStatus(
                id=key,
                name=cfg.get('name', key),
                address=cfg.get('address', 'Unknown'),
                connected=False,
                driver_class=cfg.get('driver_class', 'Unknown')
            ))
    return results

@router.post("/scpi/execute", response_model=ScpiResponse)
async def execute_scpi(req: ScpiCommand):
    """
    SCPI Playground: 执行单条指令
    """
    inst = pool.get_instrument(req.instrument_id)
    # 临时覆盖超时时间
    old_timeout = inst.timeout_ms
    inst.timeout_ms = req.timeout_ms
    
    res = ScpiResponse(instrument_id=req.instrument_id, command=req.command)
    try:
        if req.is_query or "?" in req.command:
            # 在异步线程中执行 IO，防阻塞 FastAPI
            result = await asyncio.to_thread(inst.query, req.command)
            res.response = result
        else:
            await asyncio.to_thread(inst.write, req.command)
            res.response = "OK (Write successful)"
    except Exception as e:
        res.error = str(e)
    finally:
        inst.timeout_ms = old_timeout
        
    return res

@router.post("/scpi/batch", response_model=BatchScpiResponse)
async def execute_batch_scpi(req: BatchScpiRequest):
    """
    互操作性验证核心: 批量遍历执行 SCPI 列表，快速验证仪表能力
    """
    inst = pool.get_instrument(req.instrument_id)
    results = []
    
    for cmd in req.commands:
        cmd = cmd.strip()
        if not cmd or cmd.startswith("#"):
            continue
            
        is_query = "?" in cmd
        result_entry = {"command": cmd, "type": "query" if is_query else "write"}
        
        try:
            if is_query:
                # 遍历测试时缩短超时，防止死锁
                old_timeout = inst.timeout_ms
                inst.timeout_ms = 2000 
                ans = await asyncio.to_thread(inst.query, cmd, retry=False)
                inst.timeout_ms = old_timeout
                result_entry["status"] = "success"
                result_entry["response"] = ans
            else:
                await asyncio.to_thread(inst.write, cmd, retry=False)
                result_entry["status"] = "success"
        except Exception as e:
            result_entry["status"] = "error"
            result_entry["error"] = str(e)
            
        results.append(result_entry)
        # 遍历保护：每条指令执行后停顿 100ms
        await asyncio.sleep(0.1)
        
    return BatchScpiResponse(instrument_id=req.instrument_id, results=results)

@router.get("/instruments/{inst_id}/methods")
async def get_instrument_methods(inst_id: str):
    """
    获取指定仪器驱动封装的所有公共方法（用于验证驱动）
    """
    inst = pool.get_instrument(inst_id)
    methods = []
    
    # 遍历仪器类的所有公共方法 (包括子系统如 lte, wlan)
    def scan_obj(obj, prefix=""):
        for attr_name in dir(obj):
            if attr_name.startswith('_'):
                continue
            attr = getattr(obj, attr_name)
            if callable(attr):
                doc = attr.__doc__ or "No documentation."
                import inspect
                try:
                    sig = str(inspect.signature(attr))
                except ValueError:
                    sig = "(...)"
                methods.append({
                    "name": f"{prefix}{attr_name}",
                    "signature": sig,
                    "doc": doc.strip()
                })
            elif hasattr(attr, '__class__') and "Subsystem" in attr.__class__.__name__:
                # 递归扫描子系统
                scan_obj(attr, prefix=f"{attr_name}.")
                
    scan_obj(inst)
    return {"instrument_id": inst_id, "methods": methods}

@router.post("/instruments/{inst_id}/methods/execute")
async def execute_instrument_method(inst_id: str, req: MethodExecutionRequest):
    """
    执行仪器的 Python 驱动层封装方法，并抓取系统底层错误
    """
    inst = pool.get_instrument(inst_id)
    import traceback
    
    try:
        # 递归解析方法 (如 wlan.configure_rf)
        obj = inst
        parts = req.method_name.split('.')
        for part in parts[:-1]:
            obj = getattr(obj, part)
        func = getattr(obj, parts[-1])
        
        # 执行
        if asyncio.iscoroutinefunction(func):
            res = await func(**req.kwargs)
        else:
            res = await asyncio.to_thread(func, **req.kwargs)
            
        # 主动轮询检查硬件级系统错误队列
        # 这要求 BaseInstrument 实现了 check_system_errors
        sys_errors = []
        if hasattr(inst, "check_system_errors"):
            sys_errors = await asyncio.to_thread(inst.check_system_errors)
            
        return {
            "status": "success", 
            "result": res, 
            "system_errors": sys_errors,
            "traceback": None
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e), 
            "system_errors": [],
            "traceback": traceback.format_exc()
        }
