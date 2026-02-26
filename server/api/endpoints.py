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

# --- API Endpoints ---

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok", "version": "0.2.0"}

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
    """获取当前连接池中的仪器状态"""
    results = []
    for inst_id, inst in pool.instruments.items():
        results.append(InstrumentStatus(
            id=inst_id,
            name=inst.name,
            address=inst.resource_name,
            connected=inst._connected,
            driver_class=inst.__class__.__name__
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
