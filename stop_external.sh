#!/bin/bash

# RAG Store 外部存取服務停止腳本

echo "🛑 停止 RAG Store 外部存取服務..."

# 讀取 PID 檔案並停止服務
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "✅ 後端服務已停止 (PID: $BACKEND_PID)"
    else
        echo "⚠️  後端服務已經停止"
    fi
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "✅ 前端服務已停止 (PID: $FRONTEND_PID)"
    else
        echo "⚠️  前端服務已經停止"
    fi
    rm .frontend.pid
fi

# 強制停止可能遺留的服務
echo "🧹 清理可能遺留的服務..."
pkill -f "rag_store serve"
pkill -f "next.*3002"

echo "🎉 所有服務已停止！"
