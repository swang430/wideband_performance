import logging
import os
import sys

from app.api import channel_models, endpoints
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 确保 backend 目录在 sys.path 中，以便能导入 core, drivers 等模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="终端宽带标准信道验证系统 API", version="0.1.0")

# 配置 CORS，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许所有来源，生产环境需收紧
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录，用于直接访问手册文件
# 注意：manual_library 在 backend 目录下
manual_lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "manual_library")
app.mount("/manuals_static", StaticFiles(directory=manual_lib_path), name="manuals")

# 注册路由
app.include_router(endpoints.router, prefix="/api/v1")
app.include_router(channel_models.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Channel Verification System API"}
