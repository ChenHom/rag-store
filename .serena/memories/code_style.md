# 程式碼風格和慣例

## Python 程式碼風格
- **函數命名**: snake_case  
- **類別命名**: PascalCase
- **常數**: UPPER_CASE
- **類型提示**: 使用 Python 3.10+ 類型提示
- **文檔字串**: 簡潔的 docstring 說明函數目的

### 範例
```python
from typing import List, Dict, Optional

async def process_document(
    file_path: str, 
    chunk_size: int = 512
) -> List[Dict[str, str]]:
    """處理文檔並返回分塊結果"""
    pass
```

## TypeScript/React 風格
- **組件命名**: PascalCase (React components)
- **函數命名**: camelCase
- **檔案命名**: kebab-case 或 camelCase
- **型別定義**: 使用 TypeScript 介面和型別

### 範例
```typescript
interface UploadResponse {
  message: string;
  filename: string;
  file_path: string;
}

const handleSubmit = async (data: FormData): Promise<UploadResponse> => {
  // ...
}
```

## API 設計慣例
- **REST 端點**: `/upload`, `/query`, `/health`
- **回應格式**: JSON
- **錯誤處理**: 標準 HTTP 狀態碼
- **CORS**: 支援跨域請求

## 專案結構慣例
- 設定檔在專案根目錄
- 腳本放在 `scripts/` 目錄
- 前後端分離在不同目錄
- 資料處理管道清楚分層