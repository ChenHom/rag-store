# RAG Store

RAG Store 是一個檢索增強生成（Retrieval-Augmented Generation, RAG）系統，支援文件上傳、OCR、向量化、語意查詢與智能問答。

## 架構
- **後端**：FastAPI + Python（`rag_store/`）
- **前端**：Next.js + TypeScript + Tailwind CSS（`frontend/`）
- **資料庫**：TiDB Cloud（向量搜尋）
- **向量化/AI**：OpenAI text-embedding-3-small, GPT

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
```bash
# 安裝 Python 依賴
poetry install

# 安裝前端依賴
cd frontend && npm install

# 啟動後端
poetry run python -m rag_store serve

# 啟動前端
cd frontend && npm run dev
```

## 主要開發指令
詳見 `docs/` 內指令文件與腳本註解。

## 依賴與環境變數
- Python >=3.10, Node.js (Next.js 15)
- 請複製 `.env.example` 為 `.env` 並填入實際值
- 主要環境變數：OpenAI API 金鑰、TiDB Cloud 連線資訊等

## 文件說明
所有說明文件已集中於 `docs/` 目錄，請依需求查閱。

---
如需詳細 API、部署、開發指引，請參考 `docs/` 內相關文件。