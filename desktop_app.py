import socket
import threading
import time
from typing import Optional

import requests
import uvicorn
import webview
import sys

from server.main import app

def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])

def _wait_http(url: str, timeout_s: float = 10.0) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=0.5)
            if r.status_code in (200, 404):
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False

def start_server(port: int):
    # 使用 uvicorn 的 Config，避免因端口被占用时静默失败
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    # 为了解决 pyvisa 动态加载引起的打包缺失，强制引入并保持不被优化
    import pyvisa_py
    import psutil
    import zeroconf
    import pydantic
    import urllib3

    port = _pick_free_port()

    t = threading.Thread(target=start_server, args=(port,), daemon=True)
    t.start()

    base_url = f"http://127.0.0.1:{port}"

    # 等待服务启动
    _wait_http(base_url + "/", timeout_s=15.0)

    webview.create_window(
        "UniCon Hardware Control",
        base_url + "/",
        width=1200,
        height=800,
    )
    webview.start()
