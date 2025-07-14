# 時間序列追蹤系統使用指南

**建立日期：** 2025-07-14  
**版本：** 1.0  
**適用範圍：** 家庭資料管理 RAG 系統  

## 概述

時間序列追蹤系統是家庭資料管理系統的核心功能之一，用於追蹤和分析隨時間變化的數據，如體重變化、支出趨勢、學習成績等。

## 核心功能

### 1. 數據自動提取
系統會自動從上傳的文件中提取時間序列數據：

**支援的數據類型：**
- **健康指標**：體重、身高、BMI、血壓、體脂率
- **財務數據**：月支出、月收入、各類費用
- **學習成績**：各科成績、GPA、總平均
- **生活記錄**：運動時數、睡眠時數、閱讀時數

**提取範例：**
```
輸入文字：「體重: 65.5 kg, 身高: 170 cm, 血壓: 120/80」
提取結果：
- 體重: 65.5 kg
- 身高: 170 cm  
- 血壓收縮壓: 120 mmHg
- 血壓舒張壓: 80 mmHg
```

### 2. 趨勢分析

**分析功能：**
- **趨勢類型識別**：上升、下降、穩定
- **變化百分比計算**：計算期間內的變化幅度
- **信心度評估**：基於統計相關性的信心度
- **線性回歸分析**：計算趨勢斜率

**分析結果解讀：**
- `increasing`：數據呈上升趨勢
- `decreasing`：數據呈下降趨勢  
- `stable`：數據相對穩定
- 信心度 > 0.7：趨勢較為可靠
- 信心度 < 0.3：趨勢不明顯

### 3. 警報系統

**警報類型：**
- **閾值警報**：數值超過/低於設定閾值
- **快速變化警報**：短期內變化幅度過大
- **趨勢警報**：檢測到明顯的趨勢變化

**預設警報規則：**
- 體重30天內變化超過5%
- 體重超過80kg
- 月支出30天內增加超過20%
- 月支出超過5萬元
- 數學成績低於70分

## 使用方式

### 1. 透過檔案上傳自動提取

1. **上傳包含數值的文件**（如健康檢查報告、帳單等）
2. **系統自動執行 OCR 提取文字**
3. **智能識別並提取時間序列數據**
4. **自動儲存到對應的數據類型**

### 2. 查看時間序列圖表

**訪問方式：**
```
http://localhost:8888/timeseries
```

**操作步驟：**
1. 選擇要查看的指標類型
2. 設定時間範圍（30/90/180/365天）
3. 選擇家庭成員（可選）
4. 查看趨勢圖表和統計摘要

### 3. 儀表板概覽

**功能說明：**
- **分類概覽**：各類別數據的最新狀況
- **警報通知**：未讀警報數量和詳情
- **趨勢摘要**：快速了解各指標變化

## API 接口說明

### 1. 取得時間序列類型
```http
GET /api/timeseries/types
```

**回應範例：**
```json
{
  "time_series_types": [
    {
      "id": 1,
      "name": "體重",
      "description": "體重記錄",
      "unit": "kg",
      "category": "健康",
      "data_type": "numeric",
      "color": "#FF6B6B",
      "icon": "⚖️"
    }
  ]
}
```

### 2. 取得時間序列數據
```http
POST /api/timeseries/data
Content-Type: application/json

{
  "series_type": "體重",
  "family_member_id": null,
  "start_date": "2024-10-01",
  "end_date": "2024-12-31",
  "period_days": 90
}
```

**回應範例：**
```json
{
  "series_name": "體重",
  "data_points": [
    {
      "date": "2024-10-01",
      "value": 65.0,
      "family_member": null,
      "confidence": 0.95,
      "notes": null
    }
  ],
  "statistics": {
    "latest_value": 65.5,
    "average_value": 65.2,
    "min_value": 64.8,
    "max_value": 65.8,
    "data_count": 15
  },
  "trend_analysis": {
    "trend_type": "increasing",
    "slope": 0.02,
    "correlation": 0.85,
    "confidence": 0.72,
    "change_percentage": 1.2
  }
}
```

### 3. 趨勢分析
```http
POST /api/timeseries/analysis
Content-Type: application/json

{
  "series_type": "體重",
  "family_member_id": null,
  "period_days": 30
}
```

### 4. 取得警報
```http
GET /api/timeseries/alerts
```

### 5. 標記警報已讀
```http
POST /api/timeseries/alerts/{alert_id}/read
```

### 6. 儀表板數據
```http
GET /api/timeseries/dashboard
```

## 資料庫架構

### 核心資料表

1. **time_series_types**：時間序列類型定義
2. **time_series_data**：實際時間序列數據
3. **time_series_analysis**：分析結果儲存
4. **time_series_alerts**：警報規則設定
5. **time_series_alert_logs**：警報觸發記錄

### 數據流程

```
文件上傳 → OCR提取 → 數據識別 → 時間序列儲存 → 趨勢分析 → 警報檢查
```

## 配置與自定義

### 1. 新增時間序列類型

**資料庫操作：**
```sql
INSERT INTO time_series_types 
(name, description, unit, category, data_type, color, icon) 
VALUES ('新指標', '新指標描述', '單位', '類別', 'numeric', '#FFFFFF', '📊');
```

### 2. 設定警報規則

**閾值警報：**
```sql
INSERT INTO time_series_alerts 
(series_type_id, alert_name, condition_type, threshold_value) 
VALUES (1, '警報名稱', 'threshold_high', 100.0);
```

**快速變化警報：**
```sql
INSERT INTO time_series_alerts 
(series_type_id, alert_name, condition_type, change_percentage, period_days) 
VALUES (1, '快速變化警報', 'rapid_change', 10.0, 7);
```

### 3. 自定義數據提取規則

修改 `TimeSeriesAnalyzer.extract_numeric_values()` 方法：

```python
def extract_numeric_values(self, text: str) -> List[Dict[str, Any]]:
    # 新增自定義提取規則
    custom_patterns = [
        r'新指標[：:\s]*(\d+(?:\.\d+)?)\s*(?:單位)',
    ]
    
    for pattern in custom_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = float(match.group(1))
            extracted_data.append({
                'type': '新指標',
                'value': value,
                'unit': '單位',
                'confidence': 0.9
            })
```

## 最佳實踐

### 1. 數據品質
- **定期上傳文件**：保持數據的時效性
- **檢查數據準確性**：注意 OCR 提取的準確性
- **統一格式**：盡量使用標準化的文件格式

### 2. 警報管理
- **合理設定閾值**：避免過於敏感的警報
- **定期檢視警報**：及時處理觸發的警報
- **調整警報規則**：根據實際需求調整

### 3. 趨勢分析
- **足夠的數據點**：至少需要5個以上數據點
- **合適的時間範圍**：根據數據特性選擇分析週期
- **考慮外部因素**：分析時考慮可能影響的外部因素

## 故障排除

### 常見問題

**1. 數據提取失敗**
- 檢查文件格式是否支援
- 確認數值格式是否符合提取規則
- 查看 OCR 提取的文字品質

**2. 趨勢分析不準確**
- 確認數據點數量是否足夠
- 檢查數據是否存在異常值
- 考慮調整分析週期

**3. 警報未觸發**
- 檢查警報規則設定
- 確認警報是否為啟用狀態
- 檢查數據是否正確儲存

**4. 圖表顯示異常**
- 檢查前端 recharts 套件安裝
- 確認 API 端點正常回應
- 檢查瀏覽器控制台錯誤訊息

### 日誌檢查

**後端日誌：**
```bash
tail -f fastapi.log
```

**時間序列專用日誌：**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('rag_store.time_series_analyzer')
```

## 擴展功能

### 1. 預測模型
未來可以整合機器學習模型進行數據預測：
- 線性回歸預測
- 時間序列預測（ARIMA）
- 機器學習預測

### 2. 多維度分析
支援多個指標的相關性分析：
- 體重與運動時數的關係
- 支出與收入的比例分析
- 成績與學習時間的相關性

### 3. 資料匯出
支援將時間序列數據匯出為多種格式：
- CSV 檔案
- Excel 檔案
- PDF 報表

---

**文件維護：** 此文件應隨著系統功能更新而更新  
**相關文件：**
- [多維度搜尋使用指南](multi-dimensional-search-guide.md)
- [分類系統使用指南](classification-system-guide.md)
- [API 文件](../api/)
