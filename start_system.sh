#!/bin/bash

# 终端宽带标准信道验证系统 - 智能启动脚本

# 获取项目根目录绝对路径
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="$PROJECT_ROOT/venv/bin/python3"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}      终端宽带标准信道验证系统 - 启动中...         ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 检查环境
if [ ! -f "$VENV_PATH" ]; then
    echo -e "${YELLOW}警告: 未找到虚拟环境 $VENV_PATH，将尝试使用系统 python3${NC}"
    VENV_PATH="python3"
fi

# 函数: 检查并清理端口
check_and_clean_port() {
    local port=$1
    local name=$2
    
    # 使用 lsof 查找占用端口的 PID (macOS/Linux)
    local pid=$(lsof -ti :$port)
    
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}警告: 端口 $port ($name) 正被进程 PID $pid 占用。${NC}"
        # 尝试获取进程名称
        local proc_name=$(ps -p $pid -o comm=)
        echo -e "      进程: $proc_name"
        
        # 交互询问
        read -p "是否终止该进程以继续启动? [y/N]: " choice
        case "$choice" in 
            y|Y ) 
                echo -e "${RED}正在终止 PID $pid...${NC}"
                kill -9 $pid
                sleep 1
                # 二次确认
                if [ ! -z "$(lsof -ti :$port)" ]; then
                    echo -e "${RED}错误: 无法释放端口 $port。请手动处理。${NC}"
                    exit 1
                else
                    echo -e "${GREEN}端口 $port 已释放。${NC}"
                fi
                ;; 
            * ) 
                echo -e "${RED}启动中止: 端口冲突。${NC}"
                exit 1
                ;; 
        esac
    fi
}

# 清理函数：按下 Ctrl+C 时调用
cleanup() {
    echo -e "\n${YELLOW}正在停止所有服务...${NC}"
    # 杀掉当前脚本启动的所有后台作业
    kill $(jobs -p) 2>/dev/null
    echo -e "${GREEN}系统已关闭。${NC}"
    exit
}

# 捕获中断信号
trap cleanup SIGINT

# 0. 检查端口占用
check_and_clean_port 8000 "后端 API"
check_and_clean_port 5173 "前端 Web"

# 1. 启动后端 (后台运行)
echo -e "${GREEN}[1/2] 正在启动后端服务 (FastAPI @ Port 8000)...${NC}"
echo -e "${YELLOW}提示: 后端日志将输出到 backend/backend.log，请使用 'tail -f backend/backend.log' 查看${NC}"
cd "$PROJECT_ROOT/backend"
$VENV_PATH -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# 等待后端启动
sleep 2

# 2. 启动前端
echo -e "${GREEN}[2/2] 正在启动前端界面 (Vite)...${NC}"
echo -e "${YELLOW}提示: 前端启动后，请在浏览器访问输出的 Local URL (通常是 http://localhost:5173)${NC}"
echo -e "${BLUE}----------------------------------------------------${NC}"

cd "$PROJECT_ROOT/frontend"
npm run dev

# 如果前端意外退出，也执行清理
cleanup