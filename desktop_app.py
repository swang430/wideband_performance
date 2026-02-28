import os
import sys
import threading
import time
import webview
import uvicorn
from server.main import app

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == '__main__':
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()
    
    # Wait for the server to be ready
    time.sleep(2)
    
    # Create the desktop window
    # In a real build, we'd serve the React static files, but for now we'll point to Vite if running, or the bundled static path.
    # To keep it completely independent, we would configure FastAPI to serve frontend/dist at /
    webview.create_window('UniCon Hardware Control', 'http://127.0.0.1:8000/', width=1200, height=800)
    webview.start()
