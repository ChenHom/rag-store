---
description: Guidelines for using Copilot in the project
applyTo: **
---


# 專案開發指引（Instruction）

## Operator Interaction

- 修正程式碼前，請先說明發現的問題。
- 產生測試前，請先說明將建立哪些測試。
- 若有多項變更，請先提供逐步概述。

## Security

- 產生程式碼後請檢查潛在安全性問題。
- 避免硬編碼敏感資訊（如帳號、API 金鑰等）。
- 採用安全的程式設計慣例，並驗證所有輸入。

## Environment Variables

- 若有 `.env` 檔，請用於本地環境變數管理。
- 新增環境變數時，請於 `README.md` 文件說明。
- 請於 `.env.example` 提供範例值。

## Version Control

- 每次 commit 請聚焦單一變更，保持原子性。
- commit message 請遵循 conventional commit 格式。
- 新增建置產物或相依套件時，請更新 `.gitignore`。

## Code Style

- 請遵循專案現有程式風格與慣例。
- 新增函式請加上型別註記與 docstring。
- 複雜邏輯請加上註解。

## Change Logging

- 每次產生程式碼請於 `changelog.md` 記錄。
- 遵循 semantic versioning 版本規則。
- 記錄日期與變更說明。

## Testing Requirements

- 新增功能請包含單元測試。
- 維持至少 80% 的程式覆蓋率。
- API 端點請加上整合測試。

## Documents

- 產生的說明文件存放在 `docs` 路徑，`docs` 不存在時主動建立
- `docs` 內的文件請依照類型分子資料放