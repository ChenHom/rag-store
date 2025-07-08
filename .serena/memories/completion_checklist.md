# 任務完成檢查清單

## 程式碼品質檢查
1. **後端 (Python)**
   - 執行 `python -m rag_store serve` 確認伺服器啟動
   - 測試 CLI 指令: `python -m rag_store query "test"`
   - 檢查 API 端點回應: `curl http://127.0.0.1:8000/health`

2. **前端 (TypeScript)**
   - 執行 `npm run lint` 檢查 ESLint 錯誤
   - 執行 `npm run build` 確認建置成功
   - 測試開發伺服器: `npm run dev`

## 整合測試
1. **前後端通信**
   - 後端伺服器運行在 port 8000
   - 前端開發伺服器運行在 port 3000
   - 測試檔案上傳功能
   - 測試聊天/查詢功能

2. **資料庫連接**
   - 驗證 TiDB Cloud 連接
   - 測試向量檢索查詢
   - 確認資料正確儲存

## 部署檢查
1. **環境變數**
   - OpenAI API 金鑰設定
   - TiDB Cloud 連接參數
   - CORS 設定正確

2. **依賴項**
   - Python: `poetry install` 成功
   - Node.js: `npm install` 成功
   - 所有套件版本相容

## 文檔更新
- 更新 README.md 使用說明
- 記錄 API 端點文檔
- 更新部署指南