#!/bin/bash

# 簡化版本測試腳本 - 驗證 nginx 代理功能

set -e

echo "🔧 RAG Store 系統測試"
echo "===================="

# 檢查 nginx 配置
echo "1. 測試 nginx 配置..."
if nginx -t -c "$(pwd)/nginx.conf"; then
    echo "✅ nginx 配置正確"
else
    echo "❌ nginx 配置有問題"
    exit 1
fi

# 建立必要的臨時目錄
echo "2. 建立臨時目錄..."
mkdir -p /tmp/nginx_client_temp
mkdir -p /tmp/nginx_proxy_temp
mkdir -p /tmp/nginx_fastcgi_temp
mkdir -p /tmp/nginx_uwsgi_temp
mkdir -p /tmp/nginx_scgi_temp
echo "✅ 臨時目錄已建立"

# 檢查端口是否可用
echo "3. 檢查端口可用性..."
if netstat -tlnp | grep :8080 > /dev/null; then
    echo "⚠️  端口 8080 已被使用"
else
    echo "✅ 端口 8080 可用"
fi

if netstat -tlnp | grep :8000 > /dev/null; then
    echo "⚠️  端口 8000 已被使用"
else
    echo "✅ 端口 8000 可用"
fi

if netstat -tlnp | grep :3000 > /dev/null; then
    echo "⚠️  端口 3000 已被使用"
else
    echo "✅ 端口 3000 可用"
fi

echo ""
echo "🎯 準備就緒！"
echo "接下來的步驟："
echo "1. 啟動後端：uvicorn rag_store.app.main:app --host 127.0.0.1 --port 8000"
echo "2. 啟動前端：cd frontend && npm run dev"
echo "3. 啟動 nginx：nginx -c \$(pwd)/nginx.conf"
echo "4. 訪問：http://localhost:8080"
