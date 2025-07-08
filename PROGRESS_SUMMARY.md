# 進度總結

## 已完成的工作：
*   調查了前端的上傳 API 路由和後端的 FastAPI 應用程式，以了解 PDF 上傳流程。
*   安裝了缺少的 Python 套件管理器 Poetry。
*   將 `pyproject.toml` 中的 `langchain` 依賴項更新到較新的版本 (`^0.2.0`)。
*   將 `.env` 檔案中的 `LOCAL_TIDB_HOST` 更正為 `127.0.0.1`。
*   更新了 `rag_store/app/main.py` 中 `TiDBVectorStore` 的導入語句，使其從 `langchain_community.vectorstores` 導入。
*   在 `pyproject.toml` 中添加了 `langchain-community` 作為依賴項，並修復了修改時引入的語法錯誤。
*   從 `rag_store/app/main.py` 中移除了調試用的 print 語句。

## 遇到的問題：
*   **PDF 上傳錯誤：** 主要問題是前端在嘗試上傳 PDF 時，從後端接收到的是 HTML 錯誤頁面（而不是 JSON），導致 `SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON` 錯誤。這表示後端伺服器沒有按預期響應。
*   **後端伺服器啟動失敗：** FastAPI 後端伺服器多次未能啟動或保持在 8000 端口運行。
    *   最初的失敗是因為找不到 `poetry`。
    *   隨後的失敗是由於 `TiDBVectorStore` 的 `ImportError`（因為 `langchain` 過時且缺少 `langchain-community`）。
    *   儘管在 `.env` 中將 `LOCAL_TIDB_HOST` 更改為 "127.0.0.1"，但伺服器日誌中仍然顯示 "tidb"，這表明環境變量加載或緩存存在問題。
    *   `pyproject.toml` 中的 TOML 語法錯誤曾暫時阻止了依賴項的更新。
*   伺服器目前仍未運行，`lsof -i :8000` 顯示沒有進程，並且用戶取消了上次在前台運行伺服器的嘗試。