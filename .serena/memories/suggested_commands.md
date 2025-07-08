# 重要開發指令

## Python 後端命令

### 依賴管理
```bash
poetry install          # 安裝依賴項
poetry add <package>     # 新增套件
poetry shell            # 啟動虛擬環境
```

### 執行服務
```bash
# 啟動 FastAPI 伺服器
python -m rag_store serve
python -m rag_store serve --reload  # 開發模式

# CLI 工具
python -m rag_store query "問題"
python -m rag_store ingest file.pdf
```

### 腳本
```bash
python scripts/ocr_extract.py     # PDF OCR 提取
python scripts/embed_upload.py    # 向量化和上傳
python scripts/update_struct.py   # 結構化資料匯入
```

## 前端命令

### 開發
```bash
cd frontend
npm install       # 安裝依賴項
npm run dev       # 開發伺服器 (port 3000)
npm run build     # 生產環境建置
npm run start     # 生產環境執行
npm run lint      # ESLint 檢查
```

## 資料庫
```bash
# TiDB Cloud schema
mysql -h <host> -u <user> -p < scripts/tidb_cloud_schema.sql
# 本機 TiDB
mysql -h 127.0.0.1 -P 4000 -u root < scripts/local_tidb_schema.sql
```

## 系統工具 (Linux)
```bash
lsof -i :8000     # 檢查 8000 端口
lsof -i :3000     # 檢查 3000 端口  
ps aux | grep python  # 查看 Python 進程
pkill -f "uvicorn"    # 停止 uvicorn 伺服器
```