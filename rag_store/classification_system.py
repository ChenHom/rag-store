#!/usr/bin/env python3
"""
文件分類與標記系統
提供智能文件分類、標籤管理和元資料提取功能

使用方式：
python classification_system.py --file /path/to/document.pdf
"""

import os
import re
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import mysql.connector
from openai import OpenAI
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class DocumentClassifier:
    """文件分類器"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db_config = {
            'host': os.getenv("TIDB_HOST"),
            'user': os.getenv("TIDB_USER"),
            'password': os.getenv("TIDB_PASSWORD"),
            'database': 'rag',
            'ssl_disabled': False,
            'use_unicode': True
        }
    
    def get_db_connection(self):
        """建立資料庫連線"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            print(f"資料庫連線錯誤: {e}")
            return None
    
    def classify_document(self, text: str) -> Dict[str, Any]:
        """
        使用 OpenAI API 智能分類文件
        
        Args:
            text: 文件內容文字
            
        Returns:
            Dict: 包含分類結果、信心度和提取資訊
        """
        try:
            prompt = f"""
請分析以下文件內容，並提供詳細的分類資訊。請以JSON格式回答：

文件內容：
{text[:2000]}  # 限制輸入長度避免 token 超限

請根據以下分類標準進行判斷：
1. 帳單：水電費、電話費、信用卡帳單
2. 收據：購物收據、醫療收據、教育支出
3. 成績單：學校成績、考試結果、學習進度
4. 健康記錄：身高體重、健康檢查報告、疫苗記錄
5. 保險文件：保險單、理賠申請、保險證明
6. 稅務文件：報稅資料、稅單、扣繳憑單
7. 合約文件：租約、購屋合約、服務合約
8. 證書證照：畢業證書、專業證照、資格證明
9. 其他：未分類或其他類型文件

請提供以下資訊：
{{
    "category": "分類名稱",
    "confidence": 0.95,
    "extracted_data": {{
        "amount": 1250.50,
        "date": "2025-01-15",
        "person_name": "王小明",
        "company": "台灣電力公司",
        "keywords": ["電費", "1月份", "住宅用電"]
    }},
    "suggested_tags": ["重要", "定期", "財務"],
    "reasoning": "判斷依據說明"
}}

注意：
- 金額請提取主要金額（如總金額、應繳金額）
- 日期優先提取帳單日期或文件日期
- 人名嘗試識別文件所有者或相關人員
- 關鍵字提取3-5個重要詞彙
- 信心度範圍 0.0-1.0
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是專業的文件分類助手，擅長分析家庭文件並提取關鍵資訊。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # 降低隨機性，提高分類一致性
            )
            
            # 解析 JSON 回應
            result_text = response.choices[0].message.content.strip()
            
            # 嘗試提取 JSON 內容
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = result_text[json_start:json_end]
                result = json.loads(json_text)
                return result
            else:
                raise ValueError("無法解析 AI 回應中的 JSON")
                
        except Exception as e:
            print(f"文件分類錯誤: {e}")
            return {
                "category": "其他",
                "confidence": 0.5,
                "extracted_data": {},
                "suggested_tags": [],
                "reasoning": f"分類失敗: {str(e)}"
            }
    
    def extract_amounts(self, text: str) -> List[float]:
        """提取文字中的金額"""
        # 台灣常見金額格式的正則表達式
        patterns = [
            r'NT\$?\s*([0-9,]+\.?[0-9]*)',  # NT$ 格式
            r'\$\s*([0-9,]+\.?[0-9]*)',      # $ 格式
            r'([0-9,]+\.?[0-9]*)\s*元',      # 元格式
            r'金額[：:]\s*([0-9,]+\.?[0-9]*)', # 金額: 格式
            r'應繳[：:]\s*([0-9,]+\.?[0-9]*)', # 應繳: 格式
            r'總計[：:]\s*([0-9,]+\.?[0-9]*)', # 總計: 格式
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    amounts.append(amount)
                except ValueError:
                    continue
        
        return sorted(amounts, reverse=True)  # 返回由大到小排序
    
    def extract_dates(self, text: str) -> List[str]:
        """提取文字中的日期"""
        patterns = [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD 或 YYYY/MM/DD
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY 或 DD/MM/YYYY
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',     # 中文日期格式
            r'民國(\d{2,3})年(\d{1,2})月(\d{1,2})日', # 民國年格式
        ]
        
        dates = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    groups = match.groups()
                    if '民國' in pattern:
                        # 民國年轉西元年
                        year = int(groups[0]) + 1911
                        month = int(groups[1])
                        day = int(groups[2])
                    elif pattern.startswith(r'(\d{4})'):
                        # YYYY-MM-DD 格式
                        year = int(groups[0])
                        month = int(groups[1])
                        day = int(groups[2])
                    else:
                        # 其他格式，假設為 YYYY-MM-DD
                        if len(groups[2]) == 4:  # 年份在最後
                            year = int(groups[2])
                            month = int(groups[0])
                            day = int(groups[1])
                        else:
                            year = int(groups[0])
                            month = int(groups[1])
                            day = int(groups[2])
                    
                    # 驗證日期有效性
                    date_obj = date(year, month, day)
                    dates.append(date_obj.isoformat())
                except (ValueError, IndexError):
                    continue
        
        return list(set(dates))  # 去重複
    
    def get_category_id(self, category_name: str) -> Optional[int]:
        """根據分類名稱獲取分類 ID"""
        conn = self.get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"查詢分類 ID 錯誤: {e}")
            return None
        finally:
            conn.close()
    
    def get_or_create_tags(self, tag_names: List[str]) -> List[int]:
        """獲取或建立標籤，返回標籤 ID 列表"""
        conn = self.get_db_connection()
        if not conn:
            return []
            
        tag_ids = []
        try:
            cursor = conn.cursor()
            
            for tag_name in tag_names:
                # 檢查標籤是否存在
                cursor.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
                result = cursor.fetchone()
                
                if result:
                    tag_ids.append(result[0])
                else:
                    # 建立新標籤
                    cursor.execute(
                        "INSERT INTO tags (name, color, description) VALUES (%s, %s, %s)",
                        (tag_name, '#808080', f'自動建立的標籤: {tag_name}')
                    )
                    tag_ids.append(cursor.lastrowid)
            
            conn.commit()
            return tag_ids
            
        except Exception as e:
            print(f"處理標籤錯誤: {e}")
            conn.rollback()
            return []
        finally:
            conn.close()
    
    def save_document_metadata(self, 
                             filename: str, 
                             file_path: str, 
                             classification_result: Dict[str, Any],
                             ocr_text: str = "",
                             file_size: int = 0,
                             mime_type: str = "") -> Optional[int]:
        """
        儲存文件元資料到資料庫
        
        Returns:
            int: 文件 ID，失敗時返回 None
        """
        conn = self.get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            
            # 獲取分類 ID
            category_id = self.get_category_id(classification_result.get('category', '其他'))
            
            # 提取資料
            extracted = classification_result.get('extracted_data', {})
            amount = extracted.get('amount')
            extracted_date = extracted.get('date')
            
            # 插入文件記錄
            insert_sql = """
            INSERT INTO documents (
                filename, original_filename, file_path, file_size, mime_type,
                category_id, document_date, extracted_amount, extracted_date,
                ocr_text, processing_status, confidence_score
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                filename,
                filename,
                file_path,
                file_size,
                mime_type,
                category_id,
                extracted_date,
                amount,
                extracted_date,
                ocr_text,
                'completed',
                classification_result.get('confidence', 0.5)
            )
            
            cursor.execute(insert_sql, values)
            document_id = cursor.lastrowid
            
            # 處理標籤
            suggested_tags = classification_result.get('suggested_tags', [])
            if suggested_tags:
                tag_ids = self.get_or_create_tags(suggested_tags)
                
                # 建立文件-標籤關聯
                for tag_id in tag_ids:
                    cursor.execute(
                        "INSERT INTO document_tags (document_id, tag_id) VALUES (%s, %s)",
                        (document_id, tag_id)
                    )
            
            conn.commit()
            print(f"✅ 文件元資料已儲存，文件 ID: {document_id}")
            return document_id
            
        except Exception as e:
            print(f"儲存文件元資料錯誤: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_documents_by_category(self, category_name: str) -> List[Dict[str, Any]]:
        """根據分類查詢文件"""
        conn = self.get_db_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
            SELECT d.*, c.name as category_name, c.icon, c.color
            FROM documents d
            JOIN categories c ON d.category_id = c.id
            WHERE c.name = %s
            ORDER BY d.created_at DESC
            """
            cursor.execute(sql, (category_name,))
            return cursor.fetchall()
            
        except Exception as e:
            print(f"查詢文件錯誤: {e}")
            return []
        finally:
            conn.close()
    
    def get_documents_by_tags(self, tag_names: List[str]) -> List[Dict[str, Any]]:
        """根據標籤查詢文件"""
        conn = self.get_db_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor(dictionary=True)
            placeholders = ','.join(['%s'] * len(tag_names))
            sql = f"""
            SELECT DISTINCT d.*, c.name as category_name
            FROM documents d
            JOIN document_tags dt ON d.id = dt.document_id
            JOIN tags t ON dt.tag_id = t.id
            LEFT JOIN categories c ON d.category_id = c.id
            WHERE t.name IN ({placeholders})
            ORDER BY d.created_at DESC
            """
            cursor.execute(sql, tag_names)
            return cursor.fetchall()
            
        except Exception as e:
            print(f"根據標籤查詢文件錯誤: {e}")
            return []
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取分類統計資訊"""
        conn = self.get_db_connection()
        if not conn:
            return {}
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            stats = {}
            
            # 按分類統計
            cursor.execute("""
                SELECT c.name, c.icon, c.color, COUNT(d.id) as count
                FROM categories c
                LEFT JOIN documents d ON c.id = d.category_id
                GROUP BY c.id, c.name, c.icon, c.color
                ORDER BY count DESC
            """)
            stats['by_category'] = cursor.fetchall()
            
            # 按標籤統計
            cursor.execute("""
                SELECT t.name, t.color, COUNT(dt.document_id) as count
                FROM tags t
                LEFT JOIN document_tags dt ON t.id = dt.tag_id
                GROUP BY t.id, t.name, t.color
                ORDER BY count DESC
                LIMIT 10
            """)
            stats['by_tags'] = cursor.fetchall()
            
            # 總體統計
            cursor.execute("SELECT COUNT(*) as total_documents FROM documents")
            stats['total_documents'] = cursor.fetchone()['total_documents']
            
            cursor.execute("SELECT AVG(confidence_score) as avg_confidence FROM documents")
            result = cursor.fetchone()
            stats['avg_confidence'] = float(result['avg_confidence'] or 0)
            
            return stats
            
        except Exception as e:
            print(f"獲取統計資訊錯誤: {e}")
            return {}
        finally:
            conn.close()


def main():
    """測試函數"""
    classifier = DocumentClassifier()
    
    # 測試文字分類
    test_text = """
    台灣電力股份有限公司
    電費通知單
    
    用戶名稱：王小明
    地址：台北市中正區信義路一段100號
    電表號碼：12345678
    
    計費期間：2025年1月1日 至 2025年1月31日
    本期用電度數：150度
    電費金額：NT$ 1,250
    
    應繳金額：NT$ 1,250
    繳費期限：2025年2月15日
    """
    
    print("🔍 測試文件分類...")
    result = classifier.classify_document(test_text)
    print(f"分類結果：{json.dumps(result, ensure_ascii=False, indent=2)}")
    
    print("\n📊 獲取統計資訊...")
    stats = classifier.get_statistics()
    print(f"統計結果：{json.dumps(stats, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()
