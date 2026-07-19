#!/bin/bash
# SQL Dojo — 一键启动后端 + 前端
# Usage: bash start.sh
# Requires: Python 3.12+ (will auto-detect python3.12 or python3)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 找到可用的 Python 3.12+
PYTHON=""
for cmd in python3.12 python3.11 python3; do
    if command -v "$cmd" &>/dev/null && "$cmd" -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌ 未找到 Python 3.11+，请安装后再试"
    exit 1
fi

echo "========================================"
echo "  🥋 SQL Dojo"
echo "  Python: $($PYTHON --version)"
echo "========================================"

# 1. 生成数据（如果还没生成）
if [ ! -f databases/progress.db ]; then
    echo ""
    echo "📦 首次运行，正在生成练习数据..."
    $PYTHON data_builder/generate_data.py
else
    echo ""
    echo "✅ 练习数据已就绪 (databases/)"
fi

# 2. 检查后端依赖
if ! $PYTHON -c "import fastapi" 2>/dev/null; then
    echo ""
    echo "❌ 缺少 fastapi，请手动安装："
    echo "   $PYTHON -m pip install fastapi uvicorn"
    exit 1
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
$PYTHON -m uvicorn backend.main:app --port 8000 &
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
