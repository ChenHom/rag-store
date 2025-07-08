# RAG Store 專案概覽

## 專案目的
RAG Store 是一個檢索增強生成 (Retrieval-Augmented Generation) 系統，用於處理和查詢文檔。

## 架構
- **後端**: FastAPI + Python (rag_store/)
- **前端**: Next.js + TypeScript + Tailwind CSS (frontend/)  
- **資料庫**: TiDB Cloud (向量搜尋)
- **向量化**: OpenAI text-embedding-3-small
- **LLM**: OpenAI GPT 模型

## 核心功能
1. 文檔上傳和處理 (PDF, 圖片 OCR)
2. 文字分塊和向量化
3. 向量儲存到 TiDB Cloud
4. RAG 查詢 (檢索 + 生成)
5. Web 界面和 CLI 工具

## 目錄結構
- `rag_store/` - Python 後端 API 和 CLI
- `frontend/` - Next.js 前端應用程式
- `scripts/` - 資料處理腳本 (OCR, 嵌入, 上傳)
- `raw/` - 原始文檔
- `ocr_txt/` - OCR 提取的文字
- `chunks/` - 文字分塊結果