from typing import Optional
from core.sequencer import TestSequencer

class AppState:
    """
    简单的全局状态管理。
    """
    sequencer: Optional[TestSequencer] = None
    is_running: bool = False

# 全局实例
state = AppState()
