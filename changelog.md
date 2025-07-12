# 變更日誌 (Changelog)

本檔案記錄專案的重要變更內容。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
並遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/) 版本規範。

## [Unreleased]

### Added
- 新增家庭資料管理需求分析文件 (`docs/analysis/family-data-management-requirements.md`)
  - 完整評估現有 RAG Store 系統功能
  - 識別家庭資料管理場景的關鍵缺失功能
  - 提供分階段實作建議與優先順序
  - 包含技術架構建議與風險評估
- 新增 nginx 配置檔案 (`nginx.conf`)
  - 反向代理設定
  - 前後端請求路由
  - 安全標頭配置
  - 靜態檔案快取設定
- 新增內網部署腳本 (`deploy_internal.sh`)
  - 自動化部署流程
  - 服務狀態監控
  - 日誌管理
  - 系統需求檢查
- 新增內網環境配置 (`.env.internal`)
  - 移除 ngrok 相關設定
  - 內網專用配置
  - 安全性增強
- 新增 ngrok 清理腳本 (`cleanup_ngrok.sh`)
  - 自動清理舊檔案
  - 安全確認機制
- 新增內網部署指引 (`docs/deployment/internal-deployment-guide.md`)
  - 完整部署步驟
  - 故障排除指南
  - 效能優化建議

### Changed
- 更新 `.env.example` 
  - 移除 ngrok 相關配置
  - 新增內網部署設定
  - 增加新的環境變數
- 更新 `.gitignore`
  - 標記 ngrok 檔案為已移除
  - 新增 nginx 相關忽略項目
  - 新增上傳檔案目錄
- 更新需求分析文件
  - 新增系統架構變更說明
  - 記錄部署方式改變的優勢

### Removed
- 移除 ngrok 外部存取依賴
- 移除 ngrok 相關檔案和腳本：
  - ngrok 執行檔案和配置
  - deploy_with_ngrok.sh
  - ngrok_manager.sh
  - quick_ngrok.sh
  - start_external.sh / stop_external.sh
  - test_external.sh
- 移除外部 IP 配置相關代碼

### Fixed
- 修正 nginx 配置檔案語法和權限問題
- 修正部署腳本中的 nginx 啟動邏輯
- 修正前後端 API 代理路由配置
- 使用非特權端口 8080 避免權限問題

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
