import asyncio
import json
from typing import Any, Dict, List


class LogManager:
    """
    管理 WebSocket 日志和实时指标广播。
    消息格式:
    - 日志: 纯字符串
    - 指标: JSON 字符串 {"type": "metrics", "timestamp": ..., "data": {...}}
    """
    def __init__(self):
        self.active_connections: List[asyncio.Queue] = []

    async def connect(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.active_connections.append(queue)
        return queue

    def disconnect(self, queue: asyncio.Queue):
        if queue in self.active_connections:
            self.active_connections.remove(queue)

    async def broadcast(self, message: str):
        for queue in self.active_connections:
            await queue.put(message)

    def sync_broadcast(self, message: str):
        """
        供同步代码调用的广播方法 (fire-and-forget)。
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(message))
        except RuntimeError as e:
            print(f"[DEBUG] LogManager Failed: No running loop. {e}")
        except Exception as e:
            print(f"[DEBUG] LogManager Failed: {e}")

    def sync_broadcast_metrics(self, metrics_data: Dict[str, Any]):
        """
        广播实时指标数据（JSON 格式），供 Sequencer 采样循环调用。

        Args:
            metrics_data: 包含 throughput_mbps, bler 等字段的字典
        """
        import time
        message = json.dumps({
            "type": "metrics",
            "timestamp": time.time(),
            "data": metrics_data
        }, ensure_ascii=False)
        self.sync_broadcast(message)

manager = LogManager()

