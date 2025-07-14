#!/bin/bash
"""
部署家庭資料管理分類系統
"""

echo "🚀 部署家庭資料管理分類系統"
echo "================================"

# 檢查環境
echo "🔍 檢查環境..."
if [ ! -f ".env" ]; then
    echo "❌ 找不到 .env 檔案，請先設定環境變數"
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "❌ 找不到虛擬環境，請先執行 python3 -m venv .venv"
    exit 1
fi

# 啟動虛擬環境
echo "🔌 啟動虛擬環境..."
source .venv/bin/activate

# 安裝或更新依賴
echo "📦 檢查並安裝依賴..."
pip install openai mysql-connector-python python-dotenv

# 設置分類系統資料庫
echo "🗄️ 設置分類系統資料庫..."
python setup_classification.py

if [ $? -eq 0 ]; then
    echo "✅ 資料庫設置成功"
else
    echo "❌ 資料庫設置失敗"
    exit 1
fi

# 測試分類系統
echo "🧪 測試分類系統..."
python test_classification.py

# 安裝前端依賴（如果需要）
if [ -d "frontend" ]; then
    echo "🎨 檢查前端依賴..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "📦 安裝前端依賴..."
        npm install
    fi
    cd ..
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "可用功能："
echo "- 📤 文件上傳與智能分類: /upload"
echo "- 🗂️ 分類管理介面: /classification"  
echo "- 💬 智能問答: /chat"
echo ""
echo "API 端點："
echo "- GET /api/categories - 取得分類列表"
echo "- GET /api/tags - 取得標籤列表"
echo "- GET /api/documents - 查詢文件"
echo "- GET /api/statistics - 取得統計資訊"
echo ""
echo "啟動服務："
echo "  ./deploy_internal.sh start"
echo ""
