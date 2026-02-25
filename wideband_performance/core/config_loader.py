import json
import logging
from typing import Any, Dict

import yaml


class ConfigLoader:
    """
    从文件加载测试配置。
    """
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.logger = logging.getLogger("ConfigLoader")

    def load(self) -> Dict[str, Any]:
        """
        从 YAML 或 JSON 加载配置。
        """
        self.logger.info(f"正在从 {self.config_path} 加载配置")
        try:
            with open(self.config_path, 'r') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                elif self.config_path.endswith('.json'):
                    config = json.load(f)
                else:
                    raise ValueError("不支持的配置文件格式。请使用 .yaml 或 .json")
            return config
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            raise
