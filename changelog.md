# 變更日誌 (Changelog)

本檔案記錄專案的重要變更內容。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
並遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/) 版本規範。

## [Unreleased]

### Fixed - 2025-07-14
- 修正 React Hook useEffect 依賴缺失問題，使用 useCallback 包裝函數
- 替換 TypeScript any 型別為具體型別定義，提升型別安全性
- 移除未使用的 PieChart, BarChart, Bar, Cell 組件引入
- 移除未使用的 COLORS 常數定義
- 修正 AdvancedSearchResponse 介面中 search_parameters 型別定義
- 新增 DashboardData 介面以替代 any 型別
- 修正建置錯誤，所有 TypeScript 和 ESLint 問題已解決

### Added - 2025-07-14
- 🎯 **重大功能**: 實作家庭資料管理分類與標記系統
  - 智能文件分類：自動識別帳單、收據、成績單、健康記錄等 9 大類別
  - 標籤管理系統：支援自動標籤建議和手動標籤管理
  - 結構化資料提取：自動提取金額、日期、人名、公司等關鍵資訊
  - 多維度搜尋：支援分類、標籤、日期範圍等組合查詢
  - 統計分析功能：提供文件分類統計和標籤使用分析

- 🗄️ **資料庫架構擴展**
  - 新增 `categories` 表：文件分類定義
  - 新增 `tags` 表：標籤管理
  - 新增 `documents` 表：文件元資料
  - 新增 `family_members` 表：家庭成員資訊
  - 新增 `document_tags` 表：文件標籤關聯
  - 擴展 `embeddings` 表：新增 document_id 關聯

- 🧠 **AI 分類引擎** (`rag_store/classification_system.py`)
  - 使用 OpenAI GPT-3.5-turbo 進行智能文件分類
  - 支援台灣常見文件格式和內容識別
  - 金額和日期的正則表達式提取
  - 分類信心度評估機制

- 🌐 **前端功能**
  - 新增 `/classification` 分類管理頁面
  - 更新 `/upload` 頁面顯示分類結果
  - 新增導航選單項目
  - 響應式設計支援

- 📡 **API 端點擴展**
  - `GET /api/categories` - 取得分類列表及統計
  - `GET /api/tags` - 取得標籤列表及使用統計
  - `GET /api/documents` - 支援多條件文件查詢
  - `GET /api/statistics` - 取得完整統計資訊
  - 更新 `POST /api/upload` - 回傳分類結果

- 🔍 **多維度搜尋系統** ✅ **已完全實現**
  - 三種搜尋模式：語義搜尋、條件過濾、混合模式
  - 支援分類、標籤、家庭成員、日期範圍、金額範圍等多維度過濾
  - 智能搜尋建議和自動完成功能
  - 進階搜尋頁面 (`/search`) 提供複雜查詢介面

- 🎯 **新增 API 端點**
  - `POST /api/search/advanced` - 進階搜尋，返回詳細結果和統計
  - `GET /api/search/filters` - 取得所有可用過濾器選項
  - `GET /api/search/suggestions` - 智能搜尋建議
  - 更新 `POST /api/query` - 支援多維度搜尋參數

- 🎨 **前端功能增強**
  - 全新進階搜尋頁面，支援視覺化過濾器設定
  - 導航選單新增進階搜尋入口
  - 搜尋結果包含豐富的元資料顯示
  - 即時搜尋統計和結果分析

- ⚡ **搜尋效能優化**
  - 資料庫查詢優化，支援複合條件查詢
  - 向量搜尋與條件過濾的智能結合
  - 搜尋結果快取和分頁支援

- 🧪 **測試與驗證**
  - 新增 `test_multi_search.py` 完整功能測試腳本
  - 涵蓋所有搜尋模式和過濾條件的測試案例
  - 效能測試和使用者體驗驗證

- 📚 **文件更新**
  - 新增多維度搜尋使用指南 (`docs/guide/multi-dimensional-search-guide.md`)
  - 更新 README.md 功能說明
  - API 文件和使用範例

- 📈 **重大功能**: 實作時間序列追蹤系統  
  - 數據自動提取：從文件中智能識別時間序列數據（體重、支出、成績等）
  - 趨勢分析引擎：支援線性回歸、變化百分比、信心度評估
  - 警報系統：支援閾值警報、快速變化警報、趨勢警報
  - 視覺化儀表板：完整的前端時間序列圖表和統計摘要
  - 多維度分析：支援20種預設數據類型（健康、財務、學習、生活）

- 🗄️ **時間序列資料庫架構** (`scripts/time_series_schema.sql`)
  - 新增 `time_series_types` 表：時間序列類型定義
  - 新增 `time_series_data` 表：時間序列數據點儲存
  - 新增 `time_series_analysis` 表：趨勢分析結果儲存
  - 新增 `time_series_alerts` 表：警報規則設定
  - 新增 `time_series_alert_logs` 表：警報觸發記錄

- 🧮 **時間序列分析器** (`rag_store/time_series_analyzer.py`)
  - 智能數值提取：支援多種台灣常見格式（NT$、公斤、分數等）
  - 趨勢分析算法：線性回歸、相關性分析、變化率計算
  - 警報檢查邏輯：閾值檢查、快速變化檢測
  - 統計計算：平均值、最大最小值、標準差等

- 🌐 **時間序列 API 端點** (`rag_store/app/main.py`)
  - `GET /api/timeseries/types`：取得時間序列類型
  - `POST /api/timeseries/data`：查詢時間序列數據
  - `POST /api/timeseries/analysis`：執行趨勢分析
  - `GET /api/timeseries/alerts`：取得警報列表
  - `POST /api/timeseries/alerts/{id}/read`：標記警報已讀
  - `GET /api/timeseries/dashboard`：儀表板數據

- 💻 **時間序列前端頁面** (`frontend/src/app/timeseries/page.tsx`)
  - 趨勢圖表：使用 Recharts 的互動式時間序列圖表
  - 統計摘要：即時統計數據展示
  - 警報管理：警報查看和標記功能
  - 多維篩選：類別、時間範圍、家庭成員篩選
  - 儀表板概覽：分類別的數據概況

- 🔧 **UI 組件庫擴展** (`frontend/src/components/ui/`)
  - 新增 Card、Badge、Button、Select、Tabs 組件
  - 支援時間序列頁面的完整UI需求
  - 整合 lucide-react 圖標庫

- 📚 **文檔與測試**
  - 完整使用指南：`docs/guide/time-series-tracking-guide.md`
  - 功能測試腳本：`test_time_series.py`
  - 架構設定腳本：`setup_time_series_schema.py`

- 📦 **依賴套件更新**
  - 後端：pandas、numpy、scipy、scikit-learn、langchain
  - 前端：recharts、lucide-react、@radix-ui 組件、clsx、tailwind-merge

### Changed - 2025-07-14
- 🔄 **檔案處理流程重構**
  - `process_uploaded_file` 函數整合分類功能
  - 上傳流程包含 OCR → 分類 → 資料提取 → 向量化 → 儲存
  - API 回應模型擴展支援分類結果

- 🎨 **使用者介面改進**
  - 上傳頁面展示詳細分析結果
  - 分類管理頁面提供完整篩選功能
  - 導航選單新增圖示和中文標籤

### Technical Details
- **後端技術棧**: FastAPI + OpenAI API + MySQL/TiDB Cloud
- **前端技術棧**: Next.js + TypeScript + Tailwind CSS
- **新增依賴**: `openai`, `mysql-connector-python`, `python-dotenv`
- **資料庫變更**: 5 個新表格，多個索引優化
- **API 版本**: 向後相容，新增可選欄位

### Breaking Changes
- 無重大變更，完全向後相容
- 現有 `embeddings` 表新增 `document_id` 欄位（可為空）

---

## [0.1.0] - 2025-07-12

### Added
- 初始 RAG Store 系統架構
- FastAPI 後端 API
- Next.js 前端介面
- OCR 文字提取功能
- 向量化儲存與檢索
- 基本問答功能
- 文件上傳系統
