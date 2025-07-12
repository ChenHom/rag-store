#!/bin/bash

# RAG Store 內網部署腳本
# 使用 nginx 作為反向代理，移除 ngrok 依賴

set -e

echo "🏠 RAG Store 內網部署"
echo "===================="

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

# 檢查系統需求
check_requirements() {
    log_info "檢查系統需求..."

    # 檢查 nginx 是否已安裝
    if ! command -v nginx &> /dev/null; then
        log_error "nginx 未安裝，請先安裝 nginx"
        echo "Ubuntu/Debian: sudo apt-get install nginx"
        echo "CentOS/RHEL: sudo yum install nginx"
        exit 1
    fi

    # 檢查 Python 虛擬環境
    if [ ! -d ".venv" ]; then
        log_warning "Python 虛擬環境不存在，正在建立..."
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
    fi

    # 檢查 Node.js 依賴
    if [ ! -d "frontend/node_modules" ]; then
        log_warning "Node.js 依賴不存在，正在安裝..."
        cd frontend
        npm install
        cd ..
    fi

    # 檢查環境變數檔案
    if [ ! -f ".env" ]; then
        log_warning ".env 檔案不存在，正在建立..."
        cp .env.internal .env
        log_info "請編輯 .env 檔案並填入正確的配置值"
    fi

    log_success "系統需求檢查完成"
}

# 停止現有服務
stop_services() {
    log_info "停止現有服務..."

    # 停止 Python 後端
    if [ -f ".backend.pid" ]; then
        local backend_pid=$(cat .backend.pid)
        if ps -p $backend_pid > /dev/null 2>&1; then
            log_info "停止後端服務 (PID: $backend_pid)"
            kill $backend_pid
            rm .backend.pid
        fi
    fi

    # 停止 Next.js 前端
    if [ -f ".frontend.pid" ]; then
        local frontend_pid=$(cat .frontend.pid)
        if ps -p $frontend_pid > /dev/null 2>&1; then
            log_info "停止前端服務 (PID: $frontend_pid)"
            kill $frontend_pid
            rm .frontend.pid
        fi
    fi

    # 停止 nginx (如果由此腳本管理)
    if [ -f ".nginx.pid" ]; then
        local nginx_pid=$(cat .nginx.pid)
        if ps -p $nginx_pid > /dev/null 2>&1; then
            log_info "停止 nginx 服務 (PID: $nginx_pid)"
            kill $nginx_pid
            rm .nginx.pid
        fi
    fi

    # 也嘗試停止任何 nginx 進程
    pkill -f "nginx: master process" 2>/dev/null || true

    log_success "服務停止完成"
}

# 配置 nginx
setup_nginx() {
    log_info "配置 nginx..."

    # 檢查 nginx 配置檔案
    if [ ! -f "nginx.conf" ]; then
        log_error "nginx.conf 配置檔案不存在"
        exit 1
    fi

    # 測試 nginx 配置
    if ! nginx -t -c "$(pwd)/nginx.conf"; then
        log_error "nginx 配置檔案有錯誤"
        exit 1
    fi

    log_success "nginx 配置檢查通過"
}

# 啟動後端服務
start_backend() {
    log_info "啟動後端服務..."

    # 啟動 Python 虛擬環境
    source .venv/bin/activate

    # 啟動 FastAPI 服務
    nohup uvicorn rag_store.app.main:app --host 127.0.0.1 --port 8000 \
        --log-level info > fastapi.log 2>&1 &
    echo $! > .backend.pid

    # 等待服務啟動
    sleep 3

    # 檢查服務是否正常運行
    if ! ps -p $(cat .backend.pid) > /dev/null 2>&1; then
        log_error "後端服務啟動失敗"
        cat fastapi.log
        exit 1
    fi

    log_success "後端服務已啟動 (PID: $(cat .backend.pid))"
}

# 啟動前端服務
start_frontend() {
    log_info "啟動前端服務..."

    # 建構前端
    cd frontend
    npm run build

    # 啟動 Next.js 生產模式
    nohup npm run start > ../frontend.log 2>&1 &
    echo $! > ../.frontend.pid
    cd ..

    # 等待服務啟動
    sleep 3

    # 檢查服務是否正常運行
    if ! ps -p $(cat .frontend.pid) > /dev/null 2>&1; then
        log_error "前端服務啟動失敗"
        cat frontend.log
        exit 1
    fi

    log_success "前端服務已啟動 (PID: $(cat .frontend.pid))"
}

# 啟動 nginx
start_nginx() {
    log_info "啟動 nginx..."

    # 建立臨時目錄
    mkdir -p /tmp/nginx_client_temp
    mkdir -p /tmp/nginx_proxy_temp
    mkdir -p /tmp/nginx_fastcgi_temp
    mkdir -p /tmp/nginx_uwsgi_temp
    mkdir -p /tmp/nginx_scgi_temp

    # 啟動 nginx
    nginx -c "$(pwd)/nginx.conf"

    # 取得 nginx 主進程 PID
    local nginx_pid=$(pgrep -f "nginx: master process")
    if [ -n "$nginx_pid" ]; then
        echo $nginx_pid > .nginx.pid
        log_success "nginx 已啟動 (PID: $nginx_pid)"
    else
        log_error "nginx 啟動失敗"
        exit 1
    fi
}

# 顯示服務狀態
show_status() {
    log_info "服務狀態檢查..."

    # 檢查後端服務
    if [ -f ".backend.pid" ] && ps -p $(cat .backend.pid) > /dev/null 2>&1; then
        log_success "後端服務運行中 (PID: $(cat .backend.pid))"
    else
        log_error "後端服務未運行"
    fi

    # 檢查前端服務
    if [ -f ".frontend.pid" ] && ps -p $(cat .frontend.pid) > /dev/null 2>&1; then
        log_success "前端服務運行中 (PID: $(cat .frontend.pid))"
    else
        log_error "前端服務未運行"
    fi

    # 檢查 nginx 服務
    if pgrep nginx > /dev/null; then
        log_success "nginx 服務運行中"
    else
        log_error "nginx 服務未運行"
    fi

    echo ""
    log_info "服務訪問資訊："
    echo "🌐 Web 介面: http://localhost"
    echo "🔌 API 文檔: http://localhost/docs"
    echo "📊 健康檢查: http://localhost/health"
    echo ""
    log_info "日誌檔案："
    echo "📋 後端日誌: fastapi.log"
    echo "📋 前端日誌: frontend.log"
    echo "📋 nginx 日誌: /var/log/nginx/rag-store-*.log"
}

# 主要執行流程
main() {
    case "${1:-start}" in
        "start")
            check_requirements
            stop_services
            setup_nginx
            start_backend
            start_frontend
            start_nginx
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            start_backend
            start_frontend
            start_nginx
            show_status
            ;;
        "status")
            show_status
            ;;
        *)
            echo "使用方法: $0 {start|stop|restart|status}"
            echo ""
            echo "指令說明："
            echo "  start   - 啟動所有服務"
            echo "  stop    - 停止所有服務"
            echo "  restart - 重啟所有服務"
            echo "  status  - 檢查服務狀態"
            exit 1
            ;;
    esac
}

# 執行主要功能
main "$@"
