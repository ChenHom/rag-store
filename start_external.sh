#!/bin/bash

# RAG Store 外部存取啟動腳本
# 用途：啟動支援外部存取的 RAG Store 服務

echo "🚀 啟動 RAG Store 外部存取服務..."

# 檢查外部 IP
EXTERNAL_IP="${EXTERNAL_IP:-YOUR_EXTERNAL_IP}"
echo "📡 外部 IP: $EXTERNAL_IP"

# 檢查 port 是否可用
check_port() {
    local port=$1
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "⚠️  Port $port 已被使用"
        return 1
    else
        echo "✅ Port $port 可用"
        return 0
    fi
}

# 檢查必要的 port
echo "🔍 檢查 port 可用性..."
check_port 8000 || exit 1
check_port 3002 || exit 1

# 設定環境變數檔案
echo "⚙️  設定外部存取環境變數..."
if [ ! -f .env ]; then
    cp .env.external .env
    echo "✅ 已複製外部存取環境變數檔案"
else
    echo "⚠️  .env 檔案已存在，請手動檢查設定"
fi

# 設定前端環境變數
echo "⚙️  設定前端外部存取環境變數..."
cd frontend
if [ ! -f .env.local ]; then
    cp .env.external .env.local
    echo "✅ 已複製前端外部存取環境變數檔案"
else
    echo "⚠️  frontend/.env.local 檔案已存在，請手動檢查設定"
fi
cd ..

# 啟動後端服務
echo "🔥 啟動 FastAPI 後端服務 (Port 8000)..."
python -m rag_store serve --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ 後端服務已啟動 (PID: $BACKEND_PID)"

# 等待後端啟動
echo "⏳ 等待後端服務準備就緒..."
sleep 5

# 測試後端服務
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ 後端服務健康檢查通過"
else
    echo "❌ 後端服務啟動失敗"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 啟動前端服務
echo "🔥 啟動 Next.js 前端服務 (Port 3002)..."
cd frontend
npm run dev -- --port 3002 &
FRONTEND_PID=$!
cd ..
echo "✅ 前端服務已啟動 (PID: $FRONTEND_PID)"

# 輸出服務資訊
echo "
🎉 RAG Store 外部存取服務已啟動！

📊 服務狀態：
  - 後端 API: http://$EXTERNAL_IP:8000
  - 前端介面: http://$EXTERNAL_IP:8001 (需要 ISP Port 轉發)
  - 健康檢查: http://$EXTERNAL_IP:8000/health

🔧 本機存取：
  - 後端 API: http://127.0.0.1:8000
  - 前端介面: http://127.0.0.1:3002

📋 Process IDs:
  - 後端 PID: $BACKEND_PID
  - 前端 PID: $FRONTEND_PID

⚡ 測試指令：
  curl http://$EXTERNAL_IP:8000/health

🛑 停止服務：
  kill $BACKEND_PID $FRONTEND_PID
"

# 保存 PID 到檔案，方便停止服務
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# 等待服務運行
wait
