from typing import Optional

from core.sequencer import TestSequencer


class AppState:
    """
    简单的全局状态管理。
    """
    sequencer: Optional[TestSequencer] = None
    is_running: bool = False
    current_run_id: Optional[int] = None  # 当前测试运行的数据库 ID

# 全局实例
state = AppState()
