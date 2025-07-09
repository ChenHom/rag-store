#!/bin/bash

# RAG Store 快速 ngrok 啟動腳本
# 快速設置前端和後端的 ngrok 對外訪問

echo "🚀 RAG Store 快速 ngrok 設置"
echo "=============================="

# 檢查服務狀態
check_service() {
    local service=$1
    local port=$2
    if netstat -tlnp 2>/dev/null | grep -q ":$port.*LISTEN"; then
        echo "✅ $service 正在運行 (port $port)"
        return 0
    else
        echo "❌ $service 未運行 (port $port)"
        return 1
    fi
}

echo "🔍 檢查當前服務狀態..."
check_service "FastAPI" 8000
BACKEND_RUNNING=$?

check_service "Next.js" 3000 || check_service "Next.js" 3001
FRONTEND_RUNNING=$?

# 獲取當前 ngrok 狀態
echo ""
echo "🔍 檢查 ngrok 狀態..."
if pgrep ngrok > /dev/null; then
    echo "✅ ngrok 正在運行"
    echo "🌐 Web 介面: http://127.0.0.1:4040"

    # 嘗試獲取當前 URL
    CURRENT_URL=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data['tunnels']:
        if tunnel['proto'] == 'https':
            print(f\"當前 tunnel: {tunnel['public_url']} -> {tunnel['config']['addr']}\")
except:
    pass
" 2>/dev/null)

    if [ -n "$CURRENT_URL" ]; then
        echo "📍 $CURRENT_URL"
    fi
else
    echo "❌ ngrok 未運行"
fi

echo ""
echo "請選擇操作："
echo "1) 🖥️  設置前端 ngrok (Web 介面對外)"
echo "2) 🔌 設置後端 ngrok (API 對外)"
echo "3) 🔄 完整重新部署"
echo "4) 📊 查看當前狀態"
echo "5) 🛑 停止所有服務"
echo "q) 退出"

read -p "請輸入選項 (1-5/q): " choice

case $choice in
    1)
        echo ""
        echo "🖥️ 設置前端 ngrok..."

        # 確保前端在運行
        if [ $FRONTEND_RUNNING -ne 0 ]; then
            echo "🚀 啟動前端服務..."
            cd frontend
            npm run dev > ../frontend.log 2>&1 &
            cd ..
            sleep 5
        fi

        # 啟動前端 ngrok
        ./ngrok_manager.sh frontend

        echo ""
        echo "✅ 前端 ngrok 設置完成！"
        echo "📋 請到 http://127.0.0.1:4040 查看前端 URL"
        echo "🌐 外部用戶可以通過 ngrok URL 訪問 Web 介面"
        ;;

    2)
        echo ""
        echo "🔌 設置後端 ngrok..."

        # 確保後端在運行
        if [ $BACKEND_RUNNING -ne 0 ]; then
            echo "🚀 啟動後端服務..."
            poetry run python -m uvicorn rag_store.app.main:app --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &
            sleep 5
        fi

        # 啟動後端 ngrok
        ./ngrok_manager.sh backend

        echo ""
        echo "✅ 後端 ngrok 設置完成！"
        echo "📋 請到 http://127.0.0.1:4040 查看 API URL"
        echo "🔌 外部應用可以通過 ngrok URL 調用 API"
        echo ""
        echo "💡 記得更新前端配置："
        echo "   cd frontend"
        echo "   echo 'NEXT_PUBLIC_FASTAPI_URL=https://YOUR_NGROK_URL' > .env.local"
        ;;

    3)
        echo ""
        echo "🔄 完整重新部署..."
        ./deploy_with_ngrok.sh
        ;;

    4)
        echo ""
        echo "📊 當前服務狀態："
        check_service "FastAPI" 8000
        check_service "Next.js" 3000
        check_service "Next.js" 3001

        if pgrep ngrok > /dev/null; then
            echo "✅ ngrok 正在運行 - http://127.0.0.1:4040"
        else
            echo "❌ ngrok 未運行"
        fi
        ;;

    5)
        echo ""
        echo "🛑 停止所有服務..."
        pkill ngrok 2>/dev/null || true
        pkill -f "uvicorn.*main:app" 2>/dev/null || true
        pkill -f "next dev" 2>/dev/null || true
        echo "✅ 所有服務已停止"
        ;;

    q|Q)
        echo "👋 再見！"
        exit 0
        ;;

    *)
        echo "❌ 無效選項"
        exit 1
        ;;
esac

echo ""
echo "🎉 操作完成！"
