import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 确保项目根目录在 sys.path 中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.api import endpoints

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="UniCon Debug Console", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载手册静态文件目录
manual_lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "manuals")
app.mount("/manuals_static", StaticFiles(directory=manual_lib_path), name="manuals")

app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to UniCon Debug Console API"}
