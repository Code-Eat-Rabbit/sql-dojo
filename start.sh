#!/bin/bash
# SQL Dojo — 一键启动后端 + 前端
# Usage: bash start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 uv
if ! command -v uv &>/dev/null; then
    echo "❌ 未找到 uv，请先安装：curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 检查 Docker
if ! command -v docker &>/dev/null; then
    echo "❌ 未找到 docker，请先安装 Docker Desktop：https://www.docker.com/products/docker-desktop/"
    exit 1
fi
if ! docker info &>/dev/null; then
    echo "❌ Docker daemon 未运行，请先启动 Docker Desktop"
    exit 1
fi

echo "========================================"
echo "  🥋 SQL Dojo"
echo "========================================"

# 1. 同步依赖（首次会自动创建 venv + 安装）
echo ""
echo "📦 同步 Python 依赖..."
uv sync

# 2. 启动 MySQL 并等待就绪
echo ""
echo "🐳 启动 MySQL 8 容器..."
docker compose up -d || {
    echo "❌ 容器启动失败——若为 3306 端口被占用，请停掉占用进程或修改 docker-compose.yml 的端口映射"
    exit 1
}
echo "⏳ 等待 MySQL 就绪..."
READY=0
for i in $(seq 1 60); do
    if docker compose exec -T mysql mysql -uroot -ppractice -e "SELECT 1" &>/dev/null; then
        READY=1
        break
    fi
    sleep 1
done
if [ "$READY" -ne 1 ]; then
    echo "❌ MySQL 健康检查超时（60s），请检查：docker compose logs mysql"
    exit 1
fi

# 3. 生成数据（幂等：每次重建 schema，progress.db 中的进度保留）
echo ""
echo "📦 生成练习数据..."
uv run python data_builder/generate_data.py

# 4. 安装前端依赖（如果需要）
if [ ! -d frontend/node_modules ]; then
    echo ""
    echo "📦 安装前端依赖..."
    cd frontend && npm install && cd "$SCRIPT_DIR"
fi

# 5. 启动后端
echo ""
echo "🚀 启动后端 (http://localhost:8000)..."
uv run uvicorn backend.main:app --port 8000 &
BACKEND_PID=$!

# 6. 启动前端
echo "🚀 启动前端 (http://localhost:5173)..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

# 等待后端就绪
echo "⏳ 等待后端就绪..."
for i in $(seq 1 15); do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
    if [ "$i" -eq 15 ]; then
        echo "⚠️  后端启动超时，请检查日志"
    fi
done

echo ""
echo "========================================"
echo "  ✅ 全部就绪！"
echo ""
echo "  前端:  http://localhost:5173"
echo "  后端:  http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "========================================"

# 捕获退出信号，清理子进程
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo "👋 已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 等待子进程
wait
