#!/bin/bash

# RAG Store ngrok 管理腳本
# 由於免費帳戶限制，此腳本可以幫助在前端和後端 ngrok tunnel 之間切換

set -e

echo "🔄 RAG Store ngrok 管理工具"
echo "============================="

# 檢查 ngrok 是否安裝
if [ ! -f "./ngrok" ]; then
    echo "❌ ngrok 執行檔案不存在"
    exit 1
fi

# 停止現有的 ngrok 進程
stop_ngrok() {
    echo "🛑 停止現有的 ngrok 進程..."
    pkill ngrok 2>/dev/null || true
    sleep 2
}

# 啟動後端 ngrok
start_backend_ngrok() {
    echo "🚀 啟動後端 ngrok tunnel (port 8000)..."
    ./ngrok http 8000 &
    sleep 3
    echo "✅ 後端 ngrok 已啟動"
    echo "📋 檢查 http://127.0.0.1:4040 查看 tunnel URL"
}

# 啟動前端 ngrok
start_frontend_ngrok() {
    echo "🚀 啟動前端 ngrok tunnel (port 3001)..."
    ./ngrok http 3001 &
    sleep 3
    echo "✅ 前端 ngrok 已啟動"
    echo "📋 檢查 http://127.0.0.1:4040 查看 tunnel URL"
}

# 顯示 ngrok 狀態
show_status() {
    echo "📊 當前 ngrok 狀態："
    if pgrep ngrok > /dev/null; then
        echo "✅ ngrok 正在運行"
        echo "🌐 Web 介面: http://127.0.0.1:4040"
    else
        echo "❌ ngrok 未運行"
    fi
}

# 顯示幫助
show_help() {
    echo "使用方法："
    echo "  $0 backend    - 啟動後端 ngrok tunnel"
    echo "  $0 frontend   - 啟動前端 ngrok tunnel"
    echo "  $0 stop       - 停止所有 ngrok tunnel"
    echo "  $0 status     - 顯示當前狀態"
    echo "  $0 help       - 顯示此幫助"
    echo ""
    echo "💡 注意: 免費帳戶只能同時運行一個 tunnel"
}

# 主程式
case "${1:-help}" in
    "backend")
        stop_ngrok
        start_backend_ngrok
        ;;
    "frontend")
        stop_ngrok
        start_frontend_ngrok
        ;;
    "stop")
        stop_ngrok
        echo "✅ 所有 ngrok 進程已停止"
        ;;
    "status")
        show_status
        ;;
    "help"|*)
        show_help
        ;;
esac

echo ""
echo "🎉 操作完成！"
