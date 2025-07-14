#!/usr/bin/env python3
"""
分類器基本功能驗證
"""

import os
import sys
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def main():
    print("🔍 分類器基本功能驗證")
    print("=" * 40)
    
    # 1. 檢查環境變數
    print("\n1. 環境變數檢查:")
    env_vars = ['OPENAI_API_KEY', 'TIDB_HOST', 'TIDB_USER', 'TIDB_PASSWORD']
    for var in env_vars:
        value = os.getenv(var)
        print(f"   {var}: {'✅' if value else '❌'}")
    
    # 2. 測試資料庫連線
    print("\n2. 資料庫連線測試:")
    try:
        import mysql.connector
        config = {
            'host': os.getenv("TIDB_HOST"),
            'user': os.getenv("TIDB_USER"),
            'password': os.getenv("TIDB_PASSWORD"),
            'database': 'rag',
            'ssl_disabled': False,
            'use_unicode': True
        }
        
        conn = mysql.connector.connect(**config)
        print("   ✅ 連線成功")
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        print(f"   ✅ 分類數量: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ 連線失敗: {e}")
    
    # 3. 測試 OpenAI
    print("\n3. OpenAI API 測試:")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "簡單回覆'測試成功'"}],
            max_tokens=5
        )
        
        result = response.choices[0].message.content.strip()
        print(f"   ✅ API 回應: {result}")
        
    except Exception as e:
        print(f"   ❌ API 失敗: {e}")
    
    # 4. 測試分類器導入
    print("\n4. 分類器模組測試:")
    try:
        sys.path.append('/home/hom/services/rag-store')
        from rag_store.classification_system import DocumentClassifier
        
        classifier = DocumentClassifier()
        print("   ✅ 分類器初始化成功")
        
        # 測試文字處理
        test_amounts = classifier.extract_amounts("金額 NT$ 1,250 元")
        print(f"   ✅ 金額提取: {test_amounts}")
        
        test_dates = classifier.extract_dates("2025年1月15日")
        print(f"   ✅ 日期提取: {test_dates}")
        
    except Exception as e:
        print(f"   ❌ 分類器模組失敗: {e}")
    
    print("\n" + "=" * 40)
    print("基本功能驗證完成")

if __name__ == "__main__":
    main()
