#!/bin/bash

# RAG Store ngrok 完整部署腳本
# 同時啟動前端、後端服務並提供 ngrok 外部訪問

set -e

echo "🚀 RAG Store ngrok 完整部署"
echo "=============================="

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 檢查必要檔案
check_requirements() {
    log_info "檢查必要檔案..."

    if [ ! -f "./ngrok" ]; then
        log_error "ngrok 執行檔案不存在"
        exit 1
    fi

    if [ ! -d "frontend" ]; then
        log_error "frontend 目錄不存在"
        exit 1
    fi

    log_success "必要檔案檢查通過"
}

# 停止現有服務
stop_existing_services() {
    log_info "停止現有服務..."

    # 停止 ngrok
    pkill ngrok 2>/dev/null || true

    # 停止 FastAPI
    pkill -f "uvicorn.*main:app" 2>/dev/null || true

    # 停止 Next.js
    pkill -f "next dev" 2>/dev/null || true

    sleep 3
    log_success "現有服務已停止"
}

# 啟動 FastAPI 後端
start_backend() {
    log_info "啟動 FastAPI 後端服務..."

    # 使用 poetry 或直接使用 python
    if command -v poetry >/dev/null 2>&1; then
        poetry run python -m uvicorn rag_store.app.main:app --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &
    else
        python -m uvicorn rag_store.app.main:app --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &
    fi

    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid

    # 等待服務啟動
    sleep 5

    # 健康檢查
    if curl -s http://127.0.0.1:8000/health > /dev/null; then
        log_success "FastAPI 後端已啟動 (PID: $BACKEND_PID)"
    else
        log_error "FastAPI 後端啟動失敗"
        exit 1
    fi
}

# 啟動前端
start_frontend() {
    log_info "啟動 Next.js 前端服務..."

    cd frontend

    # 設置環境變數 (使用 ngrok 後端 URL)
    cat > .env.local << EOF
# Next.js Frontend 配置 - 使用 ngrok
NEXT_PUBLIC_FASTAPI_URL=https://YOUR_BACKEND_NGROK_URL
EOF

    # 啟動前端服務
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..

    echo $FRONTEND_PID > .frontend.pid

    # 等待服務啟動
    sleep 8

    # 檢查前端是否運行
    if curl -s http://127.0.0.1:3001 > /dev/null 2>&1 || curl -s http://127.0.0.1:3000 > /dev/null 2>&1; then
        log_success "Next.js 前端已啟動 (PID: $FRONTEND_PID)"

        # 檢測前端實際運行的端口
        if netstat -tlnp 2>/dev/null | grep -q ":3001.*node"; then
            FRONTEND_PORT=3001
        else
            FRONTEND_PORT=3000
        fi

        log_info "前端運行在 port $FRONTEND_PORT"
    else
        log_error "Next.js 前端啟動失敗"
        exit 1
    fi
}

# 啟動後端 ngrok
start_backend_ngrok() {
    log_info "啟動後端 ngrok tunnel..."

    ./ngrok http 8000 > ngrok_backend.log 2>&1 &
    NGROK_PID=$!
    echo $NGROK_PID > .ngrok.pid

    # 等待 ngrok 啟動
    sleep 5

    # 獲取 ngrok URL
    BACKEND_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data['tunnels']:
        if tunnel['proto'] == 'https':
            print(tunnel['public_url'])
            break
except:
    pass
" 2>/dev/null)

    if [ -n "$BACKEND_URL" ]; then
        log_success "後端 ngrok tunnel 已建立"
        log_info "🌐 後端 URL: $BACKEND_URL"

        # 更新前端環境變數
        cd frontend
        cat > .env.local << EOF
# Next.js Frontend 配置 - 使用 ngrok
NEXT_PUBLIC_FASTAPI_URL=$BACKEND_URL
EOF
        cd ..

        log_success "前端配置已更新以使用 ngrok 後端"

        # 儲存 URLs 到檔案
        cat > .ngrok_urls << EOF
BACKEND_URL=$BACKEND_URL
FRONTEND_PORT=$FRONTEND_PORT
EOF

    else
        log_error "無法獲取 ngrok URL"
        exit 1
    fi
}

# 顯示部署資訊
show_deployment_info() {
    log_success "🎉 RAG Store 部署完成！"
    echo ""
    echo "📊 服務狀態："
    echo "  • FastAPI 後端: http://127.0.0.1:8000"
    echo "  • Next.js 前端: http://127.0.0.1:$FRONTEND_PORT"
    echo "  • 後端 ngrok: $BACKEND_URL"
    echo ""
    echo "🌐 外部訪問："
    echo "  • API: $BACKEND_URL"
    echo "  • API 健康檢查: $BACKEND_URL/health"
    echo "  • Web 前端: 需要單獨設置前端 ngrok tunnel"
    echo ""
    echo "🔧 管理工具："
    echo "  • ngrok Web 介面: http://127.0.0.1:4040"
    echo "  • 前端 ngrok: ./ngrok_manager.sh frontend"
    echo "  • 查看日誌: tail -f fastapi.log (或 frontend.log)"
    echo ""
    echo "🛑 停止服務："
    echo "  • 停止全部: ./stop_external.sh"
    echo "  • 停止 ngrok: ./ngrok_manager.sh stop"
    echo ""
    log_warning "注意: 免費 ngrok 帳戶一次只能運行一個 tunnel"
    log_info "使用 ./ngrok_manager.sh 切換前端/後端 tunnel"
}

# 主程式
main() {
    check_requirements
    stop_existing_services
    start_backend
    start_frontend
    start_backend_ngrok
    show_deployment_info
}

# 執行主程式
main

echo ""
log_success "部署腳本執行完成！"
