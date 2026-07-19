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

echo "========================================"
echo "  🥋 SQL Dojo"
echo "========================================"

# 1. 同步依赖（首次会自动创建 venv + 安装）
echo ""
echo "📦 同步 Python 依赖..."
uv sync

# 2. 生成数据（如果还没生成）
if [ ! -f databases/progress.db ]; then
    echo ""
    echo "📦 首次运行，正在生成练习数据..."
    uv run python data_builder/generate_data.py
else
    echo ""
    echo "✅ 练习数据已就绪 (databases/)"
fi

# 3. 安装前端依赖（如果需要）
if [ ! -d frontend/node_modules ]; then
    echo ""
    echo "📦 安装前端依赖..."
    cd frontend && npm install && cd "$SCRIPT_DIR"
fi

# 4. 启动后端
echo ""
echo "🚀 启动后端 (http://localhost:8000)..."
uv run uvicorn backend.main:app --port 8000 &
BACKEND_PID=$!

# 5. 启动前端
echo "🚀 启动前端 (http://localhost:5173)..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

# 等待启动
sleep 3

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
