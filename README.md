# RAG Store

RAG Store 是一個檢索增強生成（Retrieval-Augmented Generation, RAG）系統，支援文件上傳、OCR、向量化、語意查詢與智能問答。

## 系統架構

### 內網部署架構
```
內網用戶 -> nginx (port 8888) -> 前端 (port 3000) / 後端 (port 8000)
```

### 元件說明
- **反向代理:** nginx - 統一入口，負載均衡
- **後端:** FastAPI + Python - REST API 服務
- **前端:** Next.js + TypeScript - 使用者介面
- **資料庫:** TiDB Cloud - 向量搜尋與資料儲存
- **AI 服務:** OpenAI - 文字嵌入與問答生成

### 安全特性
- 🔒 僅限內網存取，無外部暴露
- 🛡️ nginx 安全標頭配置
- 🔐 環境變數管理敏感資訊
- 📝 完整的存取日誌記錄

## 核心功能
1. 文件上傳與 OCR 處理
2. 文字分塊與向量化
3. 向量儲存與檢索
4. RAG 查詢（檢索+生成）
5. Web 介面與 CLI 工具

## 目錄結構
- `rag_store/`：Python 後端 API 與 CLI
- `frontend/`：Next.js 前端
- `scripts/`：資料處理腳本
- `raw/`：原始文件
- `ocr_txt/`：OCR 文字
- `chunks/`：分塊結果
- `docs/`：所有說明文件（依類型分類）

## 快速啟動

### 內網部署
```bash
# 安裝系統依賴
sudo apt-get install nginx  # Ubuntu/Debian
# 或 sudo yum install nginx  # CentOS/RHEL

# 安裝 Python 依賴
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 安裝前端依賴
cd frontend && npm install && cd ..

# 配置環境變數
cp .env.example .env
# 編輯 .env 填入 OpenAI API 金鑰和 TiDB 連線資訊

# 啟動服務
./deploy_internal.sh start
```

### 服務訪問
- 🌐 **Web 介面:** http://localhost:8888
- 🗨️ **聊天介面:** http://localhost:8888/chat
- 📎 **文件上傳:** http://localhost:8888/upload
- 📚 **API 文檔:** http://localhost:8888/docs

### 開發模式
```bash
# 啟動後端開發服務
source .venv/bin/activate
uvicorn rag_store.app.main:app --reload --host 127.0.0.1 --port 8000

# 啟動前端開發服務
cd frontend && npm run dev
```

## 管理指令

### 服務管理
```bash
# 啟動所有服務
./deploy_internal.sh start

# 停止所有服務
./deploy_internal.sh stop

# 重啟所有服務
./deploy_internal.sh restart

# 檢查服務狀態
./deploy_internal.sh status
```

### 系統維護
```bash
# 查看系統日誌
tail -f fastapi.log
tail -f frontend.log
sudo tail -f /var/log/nginx/rag-store-access.log
```

## 依賴與環境變數
- Python >=3.10, Node.js (Next.js 15)
- 請複製 `.env.example` 為 `.env` 並填入實際值
- 主要環境變數：OpenAI API 金鑰、TiDB Cloud 連線資訊等

## 文件說明
所有說明文件已集中於 `docs/` 目錄，請依需求查閱。

---
如需詳細 API、部署、開發指引，請參考 `docs/` 內相關文件。