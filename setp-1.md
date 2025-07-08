 **「從 0 到 可用」的完整執行藍圖**——拆成 ❶\~❼ 七大階段、共 30 個具體工作項 (Work Item)。
每一項都說明 **目的 (為什麼要做)** 與 **完成標準 (Done criteria)**，照表跟進即可最終達成：

> ✅ **家人可用網頁查詢**＋✅ **你在本機有 CLI**＋✅ **所有檔案都能全文／向量檢索**

---

## 方案總覽

| 元件                                         | 選型理由                                                  |
| ------------------------------------------ | ----------------------------------------------------- |
| **向量&全文**：TiDB Cloud Serverless (HNSW索引內建) | 免維運、MySQL 協定、用 `OpenAI text-embedding-3-small` 就能上傳向量 |
| **結構化/交易**：本機 TiDB                         | 你已安裝；收「收支明細、身高體重 CSV…」                                |
| **檔案解析**：`unstructured` + `pytesseract`    | PDF/Email/圖檔一次搞定（支援繁中）                                |
| **ETL 腳本**：Python (Poetry)                 | 與 LangChain / OpenAI SDK 最相容                          |
| **Web API**：FastAPI                        | 一個程式包服務 CLI + 前端                                      |
| **前端**：Next.js + Tailwind                  | 家人手機/桌機皆可用；可隨時擴充                                      |
| **CLI**：Typer                              | 同一套服務，執行 `python -m rag query "...?"`                 |

---

## ❶ 目錄 + Git 版本庫

| # | 工作                                                                           | 目的         | Done               |
| - | ---------------------------------------------------------------------------- | ---------- | ------------------ |
| 1 | `mkdir -p ~/services/rag-store/{raw,ocr_txt,chunks,scripts,frontend}`<br/>`git init` | 統一檔案入口；版本控 | 結構建立、Git 提交        |
| 2 | `.env` 放 **TiDB Cloud** host/user/pw, **OpenAI\_API\_KEY**                   | 不把憑證寫死     | `.env` 可以 `source` |

---

## ❷ 建資料表 & 索引（雲端 / 本機）

| # | 工作                                                    | 目的            | Done                       |
| - | ----------------------------------------------------- | ------------- | -------------------------- |
| 3 | TiDB Cloud 建 db `rag`、表 `embeddings`（見下 SQL）          | 向量 / chunk 存放 | `SHOW INDEX` 出現 `vec_hnsw` |
| 4 | TiDB 本機建表 `fin_bill`, `health_metrics`, `report_meta` (docker 上已建立 tidb 資料庫)| 收結構化欄位        | `DESCRIBE` 正確              |

```sql
-- 雲端向量表
CREATE TABLE rag.embeddings(
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  doc_id VARCHAR(128),
  chunk  TEXT,
  vec    VECTOR(1536)
);
ALTER TABLE rag.embeddings
ADD VECTOR INDEX vec_hnsw ((VEC_COSINE_DISTANCE(vec)))
USING HNSW ADD_COLUMNAR_REPLICA_ON_DEMAND;
```

---

## ❸ Python 環境 & 基礎腳本

| # | 工作                                                                                                                                   | 目的      | Done                            |
| - | ------------------------------------------------------------------------------------------------------------------------------------ | ------- | ------------------------------- |
| 5 | `poetry init`；安裝<br/>`openai`, `mysql-connector-python`,<br/>`langchain`, `unstructured`,<br/>`pytesseract`, `typer`, `fastapi[all]` | 統一依賴    | `poetry run python -m pip list` |
| 6 | `scripts/ocr_extract.py`：<br/>PDF/圖檔 → TXT → 存 `ocr_txt/`                                                                            | 文件純文字化  | 任選 PDF 成功輸出                     |
| 7 | `scripts/embed_upload.py`：<br/>TXT → chunk (512 tokens) → OpenAI embed → `INSERT` 向量                                                 | 上傳向量    | `SELECT COUNT(*)` > 0           |
| 8 | `scripts/update_struct.py`：<br/>抓發票 CSV / 量測紀錄 → INSERT 本機 TiDB                                                                      | 結構化資料同步 | 本機查到資料                          |

---

## ❹ 後端 API (FastAPI)

| #  | 工作                                                                                                                                             | 目的     | Done                                |
| -- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------- |
| 9  | 建 `app/main.py`：兩組 DB 連線池 (local, cloud)                                                                                                       | 單一後端   | `uvicorn app.main:app --reload` 起得來 |
| 10 | `/query` POST：<br/>**入**：自然語句<br/>**流程**：<br/>　① LangChain 用 Cloud Vec 檢索 4 筆<br/>　② 若需要結構欄位→再查 local TiDB<br/>　③ GPT-4o 組答案<br/>**出**：答案 + 來源 | 主要檢索   | curl 得到 JSON                        |
| 11 | `/upload` POST：上傳新檔 → 存 raw → call OCR\&embed task                                                                                             | 家人直接丟檔 | swagger 能呼叫                         |

---

## ❺ CLI (Typer)

| #  | 工作                                      | 目的           | Done                |
| -- | --------------------------------------- | ------------ | ------------------- |
| 12 | `python -m rag query "去年 5 月電費多少？"`     | 本機 shell 即時查 | CLI 回覆含答案           |
| 13 | `python -m rag ingest path/to/file.pdf` | 批量匯入         | CLI Progress 0-100% |

---

## ❻ 前端 (Next.js)

| #  | 工作                                            | 目的          | Done             |
| -- | --------------------------------------------- | ----------- | ---------------- |
| 14 | `frontend/` 用 `create-next-app`               | 快速 scaffold | Yarn dev 正常      |
| 15 | 頁面：`/chat` (Chat UI)、`/upload` (拖拽上傳)         | 家人使用        | Chrome/Mobile OK |
| 16 | 呼叫後端 `/query`、`/upload`；加 Login (Auth0 或簡易密碼) | 安全管控        | 可以登入、登出          |

---

## ❼ 自動排程 & 監控

| #  | 工作                                                                   | 目的        | Done                       |
| -- | -------------------------------------------------------------------- | --------- | -------------------------- |
| 17 | Systemd timer 或 crontab：<br/>每晚 02:00 跑 `embed_upload.py` 把新 OCR 檔上雲 | 日常同步      | `/var/log/rag/cron.log` 無錯 |
| 18 | Prometheus + Node exporter (選)                                       | 監控本機 TiDB | Grafana 面板看到 QPS           |
| 19 | Logrotate for `logs/`                                                | 控制磁碟      | `logrotate -d` 無錯誤         |

---

## ❽ 文件 & 教學

| #  | 工作                                          | 目的      | Done         |
| -- | ------------------------------------------- | ------- | ------------ |
| 20 | `README.zh-TW.md`：安裝、環境變數、指令                | 自己＋家人維運 | commit 到 Git |
| 21 | `docs/user_guide.md`：家人如何上傳/查詢（截圖）          | 使用說明    | 家人可照做        |
| 22 | `docs/admin_guide.md`：備份、復原、升級 OpenAI model | 維護長遠    | 完成並 version  |

---

## ❾ 進階（未來選做）

| #  | 工作                                  | 目的           |
| -- | ----------------------------------- | ------------ |
| 23 | 壓縮嵌入向量 (bge-small) 減成本              | 降 token & \$ |
| 24 | 加 Vision Embedding（衣服照片搜尋）          | 多模態          |
| 25 | Serena Tool：`update_invoice_status` | 讓 LLM 可改資料   |

---

### 這張藍圖的「最小可用 (MVP)」是前三大階段 (❶\~❸)

只要到 #8，就能用 CLI 問答；#10 起 Web API；到 #16 家人 UI 完成。
照順序完成，每一步都能跑，建立可測試的專案

