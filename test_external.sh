#!/bin/bash

# RAG Store 外部連線測試腳本

EXTERNAL_IP="${EXTERNAL_IP:-YOUR_EXTERNAL_IP}"
BACKEND_PORT="8000"
FRONTEND_PORT="8001"

echo "🧪 測試 RAG Store 外部連線..."
echo "📡 外部 IP: $EXTERNAL_IP"
echo ""

# 測試後端 API
echo "1️⃣ 測試後端 API 連線..."
echo "   URL: http://$EXTERNAL_IP:$BACKEND_PORT"

# 健康檢查
echo "   🔍 健康檢查..."
if curl -s -o /dev/null -w "%{http_code}" "http://$EXTERNAL_IP:$BACKEND_PORT/health" --connect-timeout 5 | grep -q "200"; then
    echo "   ✅ 健康檢查通過"

    # 測試 root endpoint
    echo "   🔍 Root endpoint 測試..."
    RESPONSE=$(curl -s "http://$EXTERNAL_IP:$BACKEND_PORT/" --connect-timeout 5)
    if [ $? -eq 0 ]; then
        echo "   ✅ Root endpoint 回應: $RESPONSE"
    else
        echo "   ❌ Root endpoint 測試失敗"
    fi

    # 測試查詢 API
    echo "   🔍 查詢 API 測試..."
    QUERY_RESPONSE=$(curl -s -X POST "http://$EXTERNAL_IP:$BACKEND_PORT/query" --connect-timeout 5 \
        -H "Content-Type: application/json" \
        -d '{"query": "測試連線"}')
    if [ $? -eq 0 ]; then
        echo "   ✅ 查詢 API 可用"
        echo "   📋 回應: $(echo $QUERY_RESPONSE | head -c 100)..."
    else
        echo "   ❌ 查詢 API 測試失敗"
    fi
else
    echo "   ❌ 後端服務無法連線"
    echo "   💡 請檢查："
    echo "      - 服務是否已啟動"
    echo "      - ISP 路由器 port 8000 轉發設定"
    echo "      - 防火牆設定"
fi

echo ""

# 測試前端
echo "2️⃣ 測試前端連線..."
echo "   URL: http://$EXTERNAL_IP:$FRONTEND_PORT"
echo "   🔍 前端可用性測試..."

if curl -s -o /dev/null -w "%{http_code}" "http://$EXTERNAL_IP:$FRONTEND_PORT" --connect-timeout 5 | grep -q "200"; then
    echo "   ✅ 前端服務可以連線"
else
    echo "   ❌ 前端服務無法連線"
    echo "   💡 請檢查："
    echo "      - Next.js 服務是否已啟動在 port 3002"
    echo "      - ISP 路由器 port 8001 → 3002 轉發設定"
    echo "      - 防火牆設定"
fi

echo ""

# 顯示設定建議
echo "🔧 ISP 路由器設定建議："
echo "   外部 Port 8000 → 內網 IP Port 8000 (FastAPI)"
echo "   外部 Port 8001 → 內網 IP Port 3002 (Next.js)"
echo ""

echo "🔗 完整測試連結："
echo "   API: http://$EXTERNAL_IP:$BACKEND_PORT/health"
echo "   Web: http://$EXTERNAL_IP:$FRONTEND_PORT"
echo ""

# 檢查內網服務狀態
echo "3️⃣ 檢查內網服務狀態..."
if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo "   ✅ FastAPI 服務運行中 (Port 8000)"
else
    echo "   ❌ FastAPI 服務未運行"
fi

if netstat -tlnp 2>/dev/null | grep -q ":3002 "; then
    echo "   ✅ Next.js 服務運行中 (Port 3002)"
else
    echo "   ❌ Next.js 服務未運行"
fi
exit 0;
# 顯示防火牆狀態
echo ""
echo "4️⃣ 防火牆檢查..."
if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status | grep -q "8000.*ALLOW"; then
        echo "   ✅ UFW 允許 port 8000"
    else
        echo "   ⚠️  UFW 可能未允許 port 8000"
        echo "   💡 執行: sudo ufw allow 8000/tcp"
    fi

    if sudo ufw status | grep -q "3002.*ALLOW"; then
        echo "   ✅ UFW 允許 port 3002"
    else
        echo "   ⚠️  UFW 可能未允許 port 3002"
        echo "   💡 執行: sudo ufw allow 3002/tcp"
    fi
else
    echo "   ℹ️  未檢測到 UFW 防火牆"
fi

echo ""
echo "🎉 測試完成！"
