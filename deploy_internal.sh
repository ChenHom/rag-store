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
            # 等待正常終止，如果失敗則強制終止
            sleep 2
            if ps -p $backend_pid > /dev/null 2>&1; then
                log_warning "正常終止失敗，強制終止後端服務"
                kill -9 $backend_pid 2>/dev/null || true
            fi
            rm -f .backend.pid
        fi
    fi

    # 停止 Next.js 前端
    if [ -f ".frontend.pid" ]; then
        local frontend_pid=$(cat .frontend.pid)
        if ps -p $frontend_pid > /dev/null 2>&1; then
            log_info "停止前端服務 (PID: $frontend_pid)"
            # 首先嘗試終止整個進程組
            kill -TERM -$frontend_pid 2>/dev/null || kill $frontend_pid
            # 等待正常終止，如果失敗則強制終止
            sleep 2
            if ps -p $frontend_pid > /dev/null 2>&1; then
                log_warning "正常終止失敗，強制終止前端服務進程組"
                kill -9 -$frontend_pid 2>/dev/null || kill -9 $frontend_pid 2>/dev/null || true
            fi
            rm -f .frontend.pid
        fi
    fi
    
    # 額外檢查並清理所有 Next.js 相關進程
    local next_pids=$(pgrep -f "next-server" 2>/dev/null || true)
    if [ -n "$next_pids" ]; then
        log_info "發現額外的 Next.js 進程，進行清理..."
        echo "$next_pids" | while read -r pid; do
            if [ -n "$pid" ] && ps -p $pid > /dev/null 2>&1; then
                log_info "終止 Next.js 進程 PID: $pid"
                kill -TERM $pid 2>/dev/null || true
                sleep 1
                if ps -p $pid > /dev/null 2>&1; then
                    kill -9 $pid 2>/dev/null || true
                fi
            fi
        done
    fi

    # 停止可能佔用端口 3000 和 3001 的進程（支援 IPv4 和 IPv6）
    cleanup_port_processes() {
        local port=$1
        local port_name=$2
        
        # 方法1: lsof -ti
        local pids=$(lsof -ti :$port 2>/dev/null)
        
        # 方法2: 解析 lsof -i 輸出
        if [ -z "$pids" ]; then
            pids=$(lsof -i :$port 2>/dev/null | awk 'NR>1 && /LISTEN/ {print $2}')
        fi
        
        # 方法3: netstat
        if [ -z "$pids" ]; then
            pids=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
        fi
        
        # 方法4: ss 命令
        if [ -z "$pids" ] && command -v ss &> /dev/null; then
            pids=$(ss -tlnp 2>/dev/null | grep ":$port " | sed 's/.*pid=\([0-9]*\).*/\1/')
        fi
        
        if [ -n "$pids" ]; then
            log_info "停止佔用端口 $port 的所有進程 ($port_name)"
            echo "$pids" | while read -r pid; do
                if [ -n "$pid" ] && [ "$pid" != "0" ]; then
                    log_info "  終止進程 PID: $pid"
                    kill $pid 2>/dev/null || true
                    sleep 1
                    # 如果進程仍然存在，強制終止
                    if ps -p $pid > /dev/null 2>&1; then
                        kill -9 $pid 2>/dev/null || true
                    fi
                fi
            done
        fi
    }
    
    # cleanup_port_processes 3000 "開發服務"
    cleanup_port_processes 3001 "生產服務"

    # 停止 nginx (如果由此腳本管理)
    if [ -f ".nginx.pid" ]; then
        local nginx_pid=$(cat .nginx.pid)
        if ps -p $nginx_pid > /dev/null 2>&1; then
            log_info "停止 nginx 服務 (PID: $nginx_pid)"
            kill $nginx_pid
            sleep 2
            if ps -p $nginx_pid > /dev/null 2>&1; then
                log_warning "正常終止失敗，強制終止 nginx"
                kill -9 $nginx_pid 2>/dev/null || true
            fi
            rm -f .nginx.pid
        fi
    fi

    # 也嘗試停止任何 nginx 進程
    pkill -f "nginx: master process" 2>/dev/null || true
    sleep 1
    pkill -9 -f "nginx: master process" 2>/dev/null || true

    # 使用 pkill 來確保所有相關的 Node.js 進程都被終止
    log_info "確保清理所有 Node.js 相關進程..."
    pkill -f "next start" 2>/dev/null || true
    pkill -f "npm.*start" 2>/dev/null || true
    sleep 1
    pkill -9 -f "next start" 2>/dev/null || true
    pkill -9 -f "npm.*start" 2>/dev/null || true

    # 最終等待進程完全終止
    log_info "等待所有進程完全終止..."
    sleep 3

    # 最終檢查端口是否已釋放（支援 IPv4 和 IPv6）
    check_remaining_port() {
        local port=$1
        local remaining=""
        
        # 使用多種方法檢查端口
        remaining=$(lsof -ti :$port 2>/dev/null)
        if [ -z "$remaining" ]; then
            remaining=$(lsof -i :$port 2>/dev/null | awk 'NR>1 && /LISTEN/ {print $2}')
        fi
        if [ -z "$remaining" ]; then
            remaining=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
        fi
        
        echo "$remaining"
    }
    
    # local remaining_3000=$(check_remaining_port 3000)
    local remaining_3001=$(check_remaining_port 3001)
    
    # if [ -n "$remaining_3000" ]; then
    #     log_warning "端口 3000 仍被佔用，強制終止剩餘進程"
    #     echo "$remaining_3000" | xargs -r kill -9 2>/dev/null || true
    # fi
    
    if [ -n "$remaining_3001" ]; then
        log_warning "端口 3001 仍被佔用，強制終止剩餘進程"
        echo "$remaining_3001" | xargs -r kill -9 2>/dev/null || true
    fi

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

    # 首先確保端口 3001 可用
    check_and_cleanup_port 3001 "前端服務"
    if [ $? -ne 0 ]; then
        log_error "無法清理端口 3001，啟動前端服務失敗"
        exit 1
    fi

    # 建構前端
    cd frontend
    if ! npm run build; then
        log_error "前端建構失敗"
        cd ..
        exit 1
    fi

    # 啟動 Next.js 生產模式在端口 3001
    log_info "在端口 3001 啟動 Next.js 服務..."
    nohup npm run start -- --port 3001 > ../frontend.log 2>&1 &
    local npm_pid=$!
    cd ..

    # 等待服務啟動並找到實際的 Next.js 進程
    log_info "等待 Next.js 服務啟動..."
    sleep 5

    # 找到實際佔用端口 3001 的 Next.js 進程（支援 IPv4 和 IPv6）
    local actual_pid=""
    
    # 方法1: 使用 lsof 檢查 IPv4 和 IPv6 (更完整的檢查)
    actual_pid=$(lsof -ti :3001 2>/dev/null | head -n1)
    
    # 方法2: 如果 lsof -ti 失敗，使用 lsof -i 並支援 IPv6
    if [ -z "$actual_pid" ]; then
        actual_pid=$(lsof -i :3001 2>/dev/null | awk 'NR>1 && /LISTEN/ {print $2}' | head -n1)
    fi
    
    # 方法3: 使用 netstat 檢查 IPv4 和 IPv6
    if [ -z "$actual_pid" ]; then
        # 檢查 IPv4
        actual_pid=$(netstat -tlnp 2>/dev/null | grep "127.0.0.1:3001\|0.0.0.0:3001" | awk '{print $7}' | cut -d'/' -f1 | head -n1)
        # 如果 IPv4 沒找到，檢查 IPv6
        if [ -z "$actual_pid" ]; then
            actual_pid=$(netstat -tlnp 2>/dev/null | grep ":::3001" | awk '{print $7}' | cut -d'/' -f1 | head -n1)
        fi
    fi
    
    # 方法4: 使用 ss 命令檢查 IPv4 和 IPv6
    if [ -z "$actual_pid" ] && command -v ss &> /dev/null; then
        # 檢查 IPv4
        actual_pid=$(ss -tlnp 2>/dev/null | grep ":3001 " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -n1)
        # 如果 IPv4 沒找到，檢查 IPv6  
        if [ -z "$actual_pid" ]; then
            actual_pid=$(ss -tlnp 2>/dev/null | grep ":::3001" | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -n1)
        fi
    fi
    
    # 方法5: 使用 fuser 作為最後手段
    if [ -z "$actual_pid" ] && command -v fuser &> /dev/null; then
        actual_pid=$(fuser 3001/tcp 2>/dev/null | awk '{print $1}' | head -n1)
    fi
    
    if [ -n "$actual_pid" ] && [ "$actual_pid" != "$npm_pid" ]; then
        echo $actual_pid > .frontend.pid
        log_info "記錄實際的 Next.js 進程 PID: $actual_pid (npm wrapper PID: $npm_pid)"
        
        # 驗證找到的 PID 是否為 Next.js 進程
        if ps -p $actual_pid -o comm= 2>/dev/null | grep -q "node\|next"; then
            log_success "確認 PID $actual_pid 是 Node.js/Next.js 進程"
        else
            log_warning "PID $actual_pid 可能不是 Next.js 進程，檢查進程資訊："
            ps -p $actual_pid -o pid,ppid,comm,args 2>/dev/null || true
        fi
    else
        echo $npm_pid > .frontend.pid
        log_warning "未找到佔用端口 3001 的進程，記錄 npm 進程 PID: $npm_pid"
    fi

    # 檢查服務是否正常運行
    if ! ps -p $(cat .frontend.pid) > /dev/null 2>&1; then
        log_error "前端服務啟動失敗"
        log_error "錯誤日誌："
        tail -20 frontend.log
        exit 1
    fi

    # 檢查端口是否真的被佔用
    if ! netstat -tlnp 2>/dev/null | grep -q ":3001 \|:::3001 "; then
        log_error "前端服務進程存在但端口 3001 未被佔用"
        log_error "可能是服務啟動失敗，檢查日誌："
        tail -20 frontend.log
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

# 檢查並清理指定端口
check_and_cleanup_port() {
    local port=$1
    local service_name=$2
    
    log_info "檢查端口 $port ($service_name)"
    
    # 找到所有佔用該端口的進程（支援 IPv4 和 IPv6）
    local pids=""
    
    # 方法1: 使用 netstat 檢查 IPv4 和 IPv6（優先使用）
    # IPv4
    pids=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -v '^-$' || true)
    # IPv6 (如果 IPv4 沒找到)
    if [ -z "$pids" ]; then
        pids=$(netstat -tlnp 2>/dev/null | grep ":::$port " | awk '{print $7}' | cut -d'/' -f1 | grep -v '^-$' || true)
    fi
    
    # 方法2: 使用 ss 命令作為現代替代方案
    if [ -z "$pids" ] && command -v ss &> /dev/null; then
        pids=$(ss -tlnp 2>/dev/null | grep ":$port " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' || true)
    fi
    
    # 方法3: 使用 lsof 作為備用方案
    if [ -z "$pids" ] && command -v lsof &> /dev/null; then
        pids=$(lsof -ti :$port 2>/dev/null || true)
        # 如果 lsof -ti 失敗，使用 lsof -i 解析
        if [ -z "$pids" ]; then
            pids=$(lsof -i :$port 2>/dev/null | awk 'NR>1 && /LISTEN/ {print $2}' || true)
        fi
    fi
    if [ -n "$pids" ]; then
        log_warning "端口 $port 被以下進程佔用："
        echo "$pids" | while read -r pid; do
            if [ -n "$pid" ]; then
                local cmd=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
                log_warning "  PID: $pid ($cmd)"
            fi
        done
        
        log_info "清理端口 $port..."
        echo "$pids" | while read -r pid; do
            if [ -n "$pid" ]; then
                kill $pid 2>/dev/null || true
                sleep 1
                if ps -p $pid > /dev/null 2>&1; then
                    kill -9 $pid 2>/dev/null || true
                fi
            fi
        done
        
        # 再次檢查
        sleep 1
        local remaining=""
        
        # 使用相同的多重檢查方法（優先使用 netstat）
        remaining=$(netstat -tlnp 2>/dev/null | grep ":$port \|:::$port " | awk '{print $7}' | cut -d'/' -f1 | grep -v '^-$' || true)
        
        # 如果 netstat 沒找到，嘗試 ss
        if [ -z "$remaining" ] && command -v ss &> /dev/null; then
            remaining=$(ss -tlnp 2>/dev/null | grep ":$port " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' || true)
        fi
        
        # 最後嘗試 lsof 作為備用
        if [ -z "$remaining" ] && command -v lsof &> /dev/null; then
            remaining=$(lsof -ti :$port 2>/dev/null || true)
            if [ -z "$remaining" ]; then
                remaining=$(lsof -i :$port 2>/dev/null | awk 'NR>1 && /LISTEN/ {print $2}' || true)
            fi
        fi
        if [ -n "$remaining" ]; then
            log_error "無法清理端口 $port，請手動檢查"
            return 1
        else
            log_success "端口 $port 已清理完成"
        fi
    else
        log_success "端口 $port 可用"
    fi
    return 0
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
        "check-ports")
            log_info "檢查端口狀態..."
            check_and_cleanup_port 8000 "後端服務" || true
            check_and_cleanup_port 3001 "前端服務" || true
            check_and_cleanup_port 8888 "nginx 代理" || true
            ;;
        "cleanup")
            log_info "清理所有服務和端口..."
            stop_services
            check_and_cleanup_port 8000 "後端服務"
            check_and_cleanup_port 3001 "前端服務"  
            check_and_cleanup_port 8888 "nginx 代理"
            log_success "清理完成"
            ;;
        *)
            echo "使用方法: $0 {start|stop|restart|status|check-ports|cleanup}"
            echo ""
            echo "指令說明："
            echo "  start      - 啟動所有服務"
            echo "  stop       - 停止所有服務"
            echo "  restart    - 重啟所有服務"
            echo "  status     - 檢查服務狀態"
            echo "  check-ports - 檢查端口狀態"
            echo "  cleanup    - 清理所有服務和端口"
            exit 1
            ;;
    esac
}

# 執行主要功能
main "$@"
