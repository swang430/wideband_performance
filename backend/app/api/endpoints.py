from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
import yaml
import shutil
import json
import time

# 将 backend 根目录加入路径以导入 core 和 drivers
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config_loader import ConfigLoader
from core.sequencer import TestSequencer
from manual_library.scan_local_library import scan_and_update_catalog
from app.state import state
from app.log_manager import manager
from app.database import TestRunRepository, MetricsSampleRepository
from app.report_generator import ReportGenerator

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
    run_id: Optional[int] = None

# --- History Data Models ---
class TestRunInfo(BaseModel):
    id: int
    scenario_id: str
    scenario_name: str
    test_type: str
    status: str
    start_time: Optional[str]
    end_time: Optional[str]
    result_summary: Optional[str]

class MetricsSample(BaseModel):
    elapsed_time: float
    throughput_mbps: Optional[float]
    bler: Optional[float]
    power_dbm: Optional[float]

class TestRunDetail(BaseModel):
    run_info: TestRunInfo
    metrics: List[MetricsSample]
    statistics: Dict[str, Any]

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

def create_metrics_callback_with_db(run_id: int):
    """创建一个同时推送 WebSocket 和写入数据库的 metrics 回调"""
    def callback(metrics_data: Dict[str, Any]):
        # 推送到 WebSocket
        manager.sync_broadcast_metrics(metrics_data)
        # 写入数据库
        try:
            MetricsSampleRepository.insert(
                run_id=run_id,
                timestamp=time.time(),
                elapsed_time=metrics_data.get('elapsed_time', 0),
                throughput_mbps=metrics_data.get('throughput_mbps'),
                bler=metrics_data.get('bler'),
                power_dbm=metrics_data.get('power_dbm'),
                extra_data=json.dumps({k: v for k, v in metrics_data.items()
                                       if k not in ('throughput_mbps', 'bler', 'power_dbm', 'elapsed_time')})
            )
        except Exception as e:
            print(f"[DB] Failed to save metrics: {e}")
    return callback


async def run_sequencer_task():
    """
    后台运行 Sequencer 任务的包装器，用于处理完成后的状态重置
    """
    final_status = "completed"
    result_summary = None

    try:
        if state.sequencer:
            await state.sequencer.run()
            result_summary = "测试正常完成"
    except Exception as e:
        final_status = "failed"
        result_summary = f"测试异常: {str(e)}"
        manager.sync_broadcast(f"测试发生错误: {e}")
    finally:
        # 更新数据库状态
        if state.current_run_id:
            if not state.is_running:
                final_status = "stopped"
                result_summary = "用户手动停止"
            TestRunRepository.update_status(state.current_run_id, final_status, result_summary)
            state.current_run_id = None

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
        return {"message": "Test is already running", "running": True, "run_id": state.current_run_id}

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "config.yaml")
    loader = ConfigLoader(config_path)
    base_config = loader.load()

    # 如果指定了场景文件，加载它
    target_scenario = None
    scenario_id = "default"
    scenario_name = "默认灵敏度测试"
    test_type = "sensitivity"

    if filename:
        scenario_path = os.path.join(base_dir, "scenarios", filename)
        if os.path.exists(scenario_path):
            with open(scenario_path, 'r', encoding='utf-8') as f:
                target_scenario = yaml.safe_load(f)
                meta = target_scenario.get('metadata', {})
                scenario_id = meta.get('id', filename)
                scenario_name = meta.get('name', filename)
                test_type = target_scenario.get('config', {}).get('type', 'unknown')

    # 创建数据库记录
    run_id = TestRunRepository.create(
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        test_type=test_type,
        config_snapshot=json.dumps(target_scenario) if target_scenario else None
    )
    state.current_run_id = run_id

    # 初始化全局 Sequencer，使用带数据库写入的 metrics 回调
    state.sequencer = TestSequencer(
        base_config,
        simulation_mode=True,
        log_callback=manager.sync_broadcast,
        metrics_callback=create_metrics_callback_with_db(run_id)
    )
    state.is_running = True

    # 如果有特定场景，将它传递给 Sequencer
    if target_scenario:
        state.sequencer.current_scenario = target_scenario

    background_tasks.add_task(run_sequencer_task)

    return {"message": f"Test started ({filename if filename else 'Default'})", "running": True, "run_id": run_id}

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

# --- History API Endpoints ---

@router.get("/history", response_model=List[TestRunInfo])
async def list_test_history(limit: int = 50, offset: int = 0):
    """获取测试历史记录列表"""
    runs = TestRunRepository.list_recent(limit=limit, offset=offset)
    return [TestRunInfo(
        id=r['id'],
        scenario_id=r['scenario_id'],
        scenario_name=r['scenario_name'],
        test_type=r['test_type'],
        status=r['status'],
        start_time=r['start_time'],
        end_time=r['end_time'],
        result_summary=r['result_summary']
    ) for r in runs]

@router.get("/history/{run_id}", response_model=TestRunDetail)
async def get_test_run_detail(run_id: int):
    """获取单次测试的详细信息，包括所有指标采样"""
    run = TestRunRepository.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    metrics = MetricsSampleRepository.get_by_run_id(run_id)
    statistics = MetricsSampleRepository.get_statistics(run_id)

    return TestRunDetail(
        run_info=TestRunInfo(
            id=run['id'],
            scenario_id=run['scenario_id'],
            scenario_name=run['scenario_name'],
            test_type=run['test_type'],
            status=run['status'],
            start_time=run['start_time'],
            end_time=run['end_time'],
            result_summary=run['result_summary']
        ),
        metrics=[MetricsSample(
            elapsed_time=m['elapsed_time'],
            throughput_mbps=m['throughput_mbps'],
            bler=m['bler'],
            power_dbm=m['power_dbm']
        ) for m in metrics],
        statistics=statistics
    )

@router.delete("/history/{run_id}")
async def delete_test_run(run_id: int):
    """删除指定的测试记录"""
    run = TestRunRepository.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    TestRunRepository.delete(run_id)
    return {"message": f"Test run {run_id} deleted successfully"}

# --- Report Generation API ---

@router.get("/report/{run_id}/html", response_class=HTMLResponse)
async def get_report_html(run_id: int):
    """获取 HTML 格式的测试报告"""
    run = TestRunRepository.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    metrics = MetricsSampleRepository.get_by_run_id(run_id)
    statistics = MetricsSampleRepository.get_statistics(run_id)

    generator = ReportGenerator(run, metrics, statistics)
    html_content = generator.to_html()

    return HTMLResponse(content=html_content)


@router.get("/report/{run_id}/pdf")
async def get_report_pdf(run_id: int):
    """获取 PDF 格式的测试报告"""
    run = TestRunRepository.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    metrics = MetricsSampleRepository.get_by_run_id(run_id)
    statistics = MetricsSampleRepository.get_statistics(run_id)

    generator = ReportGenerator(run, metrics, statistics)
    pdf_bytes = generator.to_pdf()

    if not pdf_bytes:
        raise HTTPException(
            status_code=500,
            detail="PDF generation failed. Please ensure weasyprint is installed."
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{run_id}.pdf"
        }
    )

# --- Config Editor API ---

class ConfigFileInfo(BaseModel):
    filename: str
    filepath: str
    file_type: str  # 'config' or 'scenario'

class ConfigContent(BaseModel):
    content: str
    filename: str

@router.get("/config/files", response_model=List[ConfigFileInfo])
async def list_config_files():
    """列出所有可编辑的配置文件"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    files = []

    # 主配置文件
    config_path = os.path.join(base_dir, "config.yaml")
    if os.path.exists(config_path):
        files.append(ConfigFileInfo(
            filename="config.yaml",
            filepath=config_path,
            file_type="config"
        ))

    # 场景文件
    scenarios_dir = os.path.join(base_dir, "scenarios")
    if os.path.exists(scenarios_dir):
        for f in os.listdir(scenarios_dir):
            if f.endswith((".yaml", ".yml")):
                files.append(ConfigFileInfo(
                    filename=f,
                    filepath=os.path.join(scenarios_dir, f),
                    file_type="scenario"
                ))

    return files

@router.get("/config/{file_type}/{filename}")
async def get_config_content(file_type: str, filename: str):
    """获取配置文件内容"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if file_type == "config":
        filepath = os.path.join(base_dir, filename)
    elif file_type == "scenario":
        filepath = os.path.join(base_dir, "scenarios", filename)
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    # 安全检查：确保文件在允许的目录内
    real_path = os.path.realpath(filepath)
    if not real_path.startswith(os.path.realpath(base_dir)):
        raise HTTPException(status_code=403, detail="Access denied")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    return {"content": content, "filename": filename}

@router.put("/config/{file_type}/{filename}")
async def save_config_content(file_type: str, filename: str, data: ConfigContent):
    """保存配置文件内容"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if file_type == "config":
        filepath = os.path.join(base_dir, filename)
    elif file_type == "scenario":
        filepath = os.path.join(base_dir, "scenarios", filename)
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # 安全检查
    real_path = os.path.realpath(filepath)
    if not real_path.startswith(os.path.realpath(base_dir)):
        raise HTTPException(status_code=403, detail="Access denied")

    # 验证 YAML 语法
    try:
        yaml.safe_load(data.content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML syntax: {e}")

    # 备份原文件
    if os.path.exists(filepath):
        backup_path = filepath + ".bak"
        shutil.copy2(filepath, backup_path)

    # 保存新内容
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(data.content)

    return {"message": "File saved successfully", "filename": filename}

@router.post("/config/scenario")
async def create_scenario(data: ConfigContent):
    """创建新的场景文件"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    scenarios_dir = os.path.join(base_dir, "scenarios")

    if not data.filename.endswith(('.yaml', '.yml')):
        raise HTTPException(status_code=400, detail="Filename must end with .yaml or .yml")

    filepath = os.path.join(scenarios_dir, data.filename)

    if os.path.exists(filepath):
        raise HTTPException(status_code=409, detail="File already exists")

    # 验证 YAML 语法
    try:
        yaml.safe_load(data.content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML syntax: {e}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(data.content)

    return {"message": "Scenario created successfully", "filename": data.filename}

# --- DUT API Endpoints ---

from dut.android_controller import AndroidController

# 全局 DUT 控制器实例
_dut_controller: Optional[AndroidController] = None

def get_dut_controller() -> AndroidController:
    """获取或创建 DUT 控制器实例"""
    global _dut_controller
    if _dut_controller is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, "config.yaml")
        loader = ConfigLoader(config_path)
        config = loader.load()
        dut_config = config.get('dut', {})
        _dut_controller = AndroidController(
            device_id=dut_config.get('device_id'),
            simulation_mode=True  # 默认模拟模式
        )
    return _dut_controller


class ModemStatusResponse(BaseModel):
    rsrp: Optional[float] = None
    rsrq: Optional[float] = None
    sinr: Optional[float] = None
    cqi: Optional[int] = None
    pci: Optional[int] = None
    earfcn: Optional[int] = None
    band: Optional[str] = None
    network_type: Optional[str] = None
    mcc: Optional[str] = None
    mnc: Optional[str] = None
    cell_id: Optional[str] = None


@router.get("/dut/status")
async def get_dut_status():
    """获取 DUT 连接状态"""
    controller = get_dut_controller()
    try:
        controller.connect()
        data_state = controller.get_data_connection_state()
        return {
            "connected": True,
            "simulation_mode": controller.simulation_mode,
            "device_id": controller.device_id,
            "data_connection": data_state
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


@router.get("/dut/modem", response_model=ModemStatusResponse)
async def get_modem_status():
    """获取 Modem 状态 (RSRP/RSRQ/SINR/CQI 等)"""
    controller = get_dut_controller()
    try:
        controller.connect()
        status = controller.get_modem_status()
        return ModemStatusResponse(
            rsrp=status.rsrp,
            rsrq=status.rsrq,
            sinr=status.sinr,
            cqi=status.cqi,
            pci=status.pci,
            earfcn=status.earfcn,
            band=status.band,
            network_type=status.network_type,
            mcc=status.mcc,
            mnc=status.mnc,
            cell_id=status.cell_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get modem status: {e}")


@router.get("/dut/signal")
async def get_signal_quality():
    """获取简化的信号质量摘要"""
    controller = get_dut_controller()
    try:
        controller.connect()
        return controller.get_signal_quality()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signal quality: {e}")


@router.post("/dut/airplane-mode")
async def set_airplane_mode(enable: bool = True):
    """开启/关闭飞行模式"""
    controller = get_dut_controller()
    try:
        controller.connect()
        controller.enable_airplane_mode(enable)
        return {"message": f"Airplane mode {'enabled' if enable else 'disabled'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set airplane mode: {e}")