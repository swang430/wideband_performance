from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
import yaml
import shutil
import asyncio

# 将 backend 根目录加入路径以导入 core 和 drivers
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_loader import ConfigLoader
from core.sequencer import TestSequencer
from manual_library.scan_local_library import scan_and_update_catalog
from app.state import state
from app.log_manager import manager

router = APIRouter()

# --- Data Models ---
class HealthResponse(BaseModel):
    status: str
    version: str

class InstrumentStatus(BaseModel):
    id: str
    name: str
    address: str
    connected: bool
    simulation: bool
    driver_info: Optional[Dict[str, Any]] = None

class ManualEntry(BaseModel):
    title: str
    type: str
    url: str
    notes: Optional[str] = None
    is_local: bool = False
    local_url: Optional[str] = None

class SeriesEntry(BaseModel):
    vendor: str
    series: str
    models: List[str]
    manuals: List[ManualEntry]

class CatalogResponse(BaseModel):
    categories: Dict[str, List[SeriesEntry]]

class TestControlResponse(BaseModel):
    message: str
    running: bool

# --- API Endpoints ---

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

@router.get("/instruments/status", response_model=List[InstrumentStatus])
async def get_instruments_status():
    """
    获取所有仪表的连接状态。
    优先使用当前正在运行的全局 Sequencer 实例，否则创建临时实例检查。
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.yaml")
    
    # 决定使用哪个 sequencer 实例
    if state.sequencer:
        sequencer = state.sequencer
        # 如果正在运行，大概率已经连接好了
        config = sequencer.config
    else:
        loader = ConfigLoader(config_path)
        config = loader.load()
        # 临时初始化一个 Sequencer 来检查状态
        sequencer = TestSequencer(config, simulation_mode=True)
        sequencer.initialize_instruments()
    
    results = []
    
    inst_config = config.get('instruments', {})
    for cfg_key, info in inst_config.items():
        driver_info = None
        connected = False
        
        # Sequencer.instruments 的键与 config.yaml 中的键保持一致
        if cfg_key in sequencer.instruments:
            inst_obj = sequencer.instruments[cfg_key]
            # 尝试获取驱动信息
            if hasattr(inst_obj, "get_driver_info"):
                try:
                    driver_info = inst_obj.get_driver_info()
                    connected = True
                except Exception:
                    pass
        
        results.append(InstrumentStatus(
            id=cfg_key,
            name=info.get('name', cfg_key.upper()),
            address=info.get('address', 'Unknown'),
            connected=connected, 
            simulation=True, # 暂时硬编码，未来应从 config 读取
            driver_info=driver_info
        ))
    
    return results

@router.get("/manuals", response_model=CatalogResponse)
async def get_manuals_catalog():
    """
    获取手册库目录，并检查本地文件是否存在
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    catalog_path = os.path.join(base_dir, "manual_library", "catalog.yaml")
    
    if not os.path.exists(catalog_path):
        return CatalogResponse(categories={})

    with open(catalog_path, 'r', encoding='utf-8') as f:
        raw_catalog = yaml.safe_load(f) or {}

    processed_catalog = {}

    for category, series_list in raw_catalog.items():
        processed_series = []
        for entry in series_list:
            processed_manuals = []
            
            vendor = entry.get('vendor', 'Unknown').replace(" ", "_").replace("&", "and")
            series = entry.get('series', 'Generic').replace(" ", "_")
            folder_name = f"{vendor}_{series}"
            local_folder_path = os.path.join(base_dir, "manual_library", category, folder_name)

            for m in entry.get('manuals', []):
                is_local = False
                local_url = None
                
                potential_filename = os.path.basename(m['url'])
                full_file_path = os.path.join(local_folder_path, potential_filename)
                
                if os.path.exists(full_file_path) and os.path.isfile(full_file_path):
                    is_local = True
                    local_url = f"/manuals_static/{category}/{folder_name}/{potential_filename}"
                
                processed_manuals.append(ManualEntry(
                    title=m.get('title', 'Unknown'),
                    type=m.get('type', 'manual'),
                    url=m.get('url', ''),
                    notes=m.get('notes'),
                    is_local=is_local,
                    local_url=local_url
                ))
            
            processed_series.append(SeriesEntry(
                vendor=entry.get('vendor'),
                series=entry.get('series'),
                models=entry.get('models', []),
                manuals=processed_manuals
            ))
        processed_catalog[category] = processed_series

    return CatalogResponse(categories=processed_catalog)

@router.post("/manuals/upload")
async def upload_manual(
    file: UploadFile = File(...),
    category: str = Form(...),
    vendor: str = Form(...),
    series: str = Form(...)
):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    folder_name = f"{vendor}_{series}".replace(" ", "_").replace("&", "and")
    target_dir = os.path.join(base_dir, "manual_library", category, folder_name)
    
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Failed to create directory: {e}")

    file_path = os.path.join(target_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    try:
        scan_and_update_catalog("catalog.yaml", "manual_library")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File saved but catalog update failed: {e}")

    return {"message": "File uploaded and catalog updated successfully", "filename": file.filename}

# --- Test Control & WebSocket ---

async def run_sequencer_task():
    """
    后台运行 Sequencer 任务的包装器，用于处理完成后的状态重置
    """
    if state.sequencer:
        await state.sequencer.run()
    state.is_running = False
    manager.sync_broadcast("测试任务已结束")

class ScenarioInfo(BaseModel):
    filename: str
    id: str
    name: str
    version: str

@router.get("/scenarios", response_model=List[ScenarioInfo])
async def list_scenarios():
    """
    扫描并列出所有可用的测试场景文件。
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    scenarios_dir = os.path.join(base_dir, "scenarios")
    
    results = []
    if not os.path.exists(scenarios_dir):
        return []
        
    for f in os.listdir(scenarios_dir):
        if f.endswith(".yaml") or f.endswith(".yml"):
            try:
                with open(os.path.join(scenarios_dir, f), 'r', encoding='utf-8') as file:
                    data = yaml.safe_load(file)
                    meta = data.get('metadata', {})
                    results.append(ScenarioInfo(
                        filename=f,
                        id=meta.get('id', 'unknown'),
                        name=meta.get('name', f),
                        version=meta.get('version', '1.0')
                    ))
            except Exception as e:
                print(f"Error loading scenario {f}: {e}")
    
    return results

@router.post("/test/start", response_model=TestControlResponse)
async def start_test(background_tasks: BackgroundTasks, filename: Optional[str] = None):
    if state.is_running:
        return {"message": "Test is already running", "running": True}

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "config.yaml")
    loader = ConfigLoader(config_path)
    base_config = loader.load()

    # 如果指定了场景文件，加载它
    target_scenario = None
    if filename:
        scenario_path = os.path.join(base_dir, "scenarios", filename)
        if os.path.exists(scenario_path):
            with open(scenario_path, 'r', encoding='utf-8') as f:
                target_scenario = yaml.safe_load(f)
    
    # 初始化全局 Sequencer
    state.sequencer = TestSequencer(
        base_config, 
        simulation_mode=True,
        log_callback=manager.sync_broadcast
    )
    state.is_running = True
    
    # 如果有特定场景，将它传递给 Sequencer (我们需要修改 run_sequencer_task 来支持参数)
    # 这里为了简单，我们将 target_scenario 注入到 sequencer 的某个属性中，或者修改 run 方法
    if target_scenario:
        state.sequencer.current_scenario = target_scenario

    background_tasks.add_task(run_sequencer_task)
    
    return {"message": f"Test started ({filename if filename else 'Default'})", "running": True}

@router.post("/test/stop", response_model=TestControlResponse)
async def stop_test():
    if state.sequencer and state.is_running:
        state.sequencer.stop()
        state.is_running = False # 标记为停止，虽然 task 可能还在收尾
        return {"message": "Stop signal sent", "running": False}
    return {"message": "No test running", "running": False}

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue = await manager.connect()
    try:
        while True:
            data = await queue.get()
            await websocket.send_text(data)
    except WebSocketDisconnect:
        manager.disconnect(queue)