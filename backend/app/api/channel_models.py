"""
信道模型分析端点
提供场景与信道模型的映射关系和统计信息
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import yaml
from typing import List, Dict, Any
from collections import Counter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

SCENARIOS_DIR = Path(__file__).parent.parent.parent / "scenarios"


def extract_channel_models_from_scenario(scenario_file: Path) -> Dict[str, Any]:
    """从场景文件中提取信道模型信息"""
    try:
        with open(scenario_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        result = {
            'filename': scenario_file.name,
            'scenario_name': data.get('metadata', {}).get('name', scenario_file.stem),
            'scenario_id': data.get('metadata', {}).get('id', ''),
            'models': []
        }
        
        config = data.get('config', {})
        
        # 提取主信道模型
        if 'channel' in config:
            channel_config = config['channel']
            if 'model' in channel_config:
                result['models'].append({
                    'name': channel_config['model'],
                    'time': 0,
                    'is_initial': True
                })
        
        # 提取时间轴中的信道模型切换
        timeline = config.get('timeline', [])
        for event in timeline:
            if event.get('target') == 'channel_emulator' and event.get('action') == 'load_channel_model':
                model_name = event.get('params', {}).get('model', '')
                if model_name:
                    result['models'].append({
                        'name': model_name,
                        'time': event.get('time', 0),
                        'is_initial': False
                    })
        
        return result
    
    except Exception as e:
        logger.error(f"Error parsing {scenario_file}: {e}")
        return None


@router.get("/channel-models/scenarios")
async def get_channel_models_scenarios():
    """
    获取所有场景的信道模型使用情况
    
    返回:
    - scenarios: 场景列表及其使用的信道模型
    - statistics: 信道模型使用统计
    """
    if not SCENARIOS_DIR.exists():
        raise HTTPException(status_code=500, detail="Scenarios directory not found")
    
    scenarios = []
    all_models = []
    
    # 遍历所有场景文件
    for scenario_file in SCENARIOS_DIR.glob("*.yaml"):
        scenario_info = extract_channel_models_from_scenario(scenario_file)
        if scenario_info and scenario_info['models']:
            scenarios.append(scenario_info)
            # 收集所有模型名称用于统计
            for model in scenario_info['models']:
                all_models.append(model['name'])
    
    # 统计信道模型使用频率
    model_counter = Counter(all_models)
    statistics = {
        'total_scenarios': len(scenarios),
        'total_models': len(set(all_models)),
        'model_usage': [
            {'model': model, 'count': count}
            for model, count in model_counter.most_common()
        ]
    }
    
    return {
        'scenarios': scenarios,
        'statistics': statistics
    }


@router.get("/channel-models/list")
async def get_channel_models_list():
    """
    获取所有不同的信道模型列表
    """
    if not SCENARIOS_DIR.exists():
        raise HTTPException(status_code=500, detail="Scenarios directory not found")
    
    all_models = set()
    
    for scenario_file in SCENARIOS_DIR.glob("*.yaml"):
        scenario_info = extract_channel_models_from_scenario(scenario_file)
        if scenario_info:
            for model in scenario_info['models']:
                all_models.add(model['name'])
    
    return {
        'models': sorted(list(all_models))
    }
