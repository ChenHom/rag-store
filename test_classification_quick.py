#!/usr/bin/env python3
"""
分類器功能測試 - 檢查各個組件是否正常工作
"""

import sys
import os
import json
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 測試基本組件
def test_basic_components():
    """測試基本組件導入和設置"""
    print("🔧 測試基本組件...")
    
    # 測試環境變數
    print(f"  OPENAI_API_KEY: {'✅ 已設置' if os.getenv('OPENAI_API_KEY') else '❌ 未設置'}")
    print(f"  TIDB_HOST: {'✅ 已設置' if os.getenv('TIDB_HOST') else '❌ 未設置'}")
    print(f"  TIDB_USER: {'✅ 已設置' if os.getenv('TIDB_USER') else '❌ 未設置'}")
    print(f"  TIDB_PASSWORD: {'✅ 已設置' if os.getenv('TIDB_PASSWORD') else '❌ 未設置'}")
    
    # 測試模組導入
    try:
        import mysql.connector
        print("  mysql.connector: ✅ 已安裝")
    except ImportError:
        print("  mysql.connector: ❌ 未安裝")
    
    try:
        from openai import OpenAI
        print("  openai: ✅ 已安裝")
    except ImportError:
        print("  openai: ❌ 未安裝")

def test_database_connection():
    """測試資料庫連線"""
    print("\n🔌 測試資料庫連線...")
    
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
        print("  ✅ 資料庫連線成功")
        
        cursor = conn.cursor()
        
        # 檢查表格
        tables_to_check = ['categories', 'tags', 'documents', 'family_members', 'document_tags']
        
        for table in tables_to_check:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            result = cursor.fetchone()
            print(f"  表 '{table}': {'✅ 存在' if result else '❌ 不存在'}")
        
        # 檢查預設資料
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        print(f"  預設分類數量: {category_count}")
        
        cursor.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]
        print(f"  預設標籤數量: {tag_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ 資料庫連線失敗: {e}")
        return False

def test_openai_connection():
    """測試 OpenAI API 連線"""
    print("\n🤖 測試 OpenAI API 連線...")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 簡單測試
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "回覆 'API測試成功'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"  ✅ OpenAI API 連線成功，回應: {result}")
        return True
        
    except Exception as e:
        print(f"  ❌ OpenAI API 連線失敗: {e}")
        return False

def test_text_processing():
    """測試文字處理功能"""
    print("\n📝 測試文字處理功能...")
    
    # 載入分類器
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from rag_store.classification_system import DocumentClassifier
        classifier = DocumentClassifier()
        
        # 測試金額提取
        test_text = "應繳金額：NT$ 1,250 元，總計 $2,500"
        amounts = classifier.extract_amounts(test_text)
        print(f"  金額提取測試: 找到 {len(amounts)} 個金額")
        if amounts:
            print(f"    最大金額: {max(amounts)}")
        
        # 測試日期提取
        date_text = "2025年1月15日 繳費期限：2025/02/15"
        dates = classifier.extract_dates(date_text)
        print(f"  日期提取測試: 找到 {len(dates)} 個日期")
        for date in dates:
            print(f"    日期: {date}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 文字處理功能測試失敗: {e}")
        return False

def test_document_classification():
    """測試文件分類功能"""
    print("\n🎯 測試文件分類功能...")
    
    try:
        from rag_store.classification_system import DocumentClassifier
        classifier = DocumentClassifier()
        
        # 簡單的測試文件
        test_text = """
        台灣電力股份有限公司
        電費通知單
        用戶名稱：王小明
        應繳金額：NT$ 1,250
        繳費期限：2025年2月15日
        """
        
        print("  🔍 開始分類測試文件...")
        result = classifier.classify_document(test_text)
        
        print(f"  分類結果: {result.get('category', '無')}")
        print(f"  信心度: {result.get('confidence', 0):.2f}")
        
        if result.get('extracted_data'):
            print("  提取資料:")
            for key, value in result['extracted_data'].items():
                if value:
                    print(f"    {key}: {value}")
        
        if result.get('suggested_tags'):
            print(f"  建議標籤: {', '.join(result['suggested_tags'])}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 文件分類功能測試失敗: {e}")
        return False

def main():
    """主要測試函數"""
    print("🧪 分類器功能快速檢測")
    print("=" * 50)
    
    # 各項測試
    tests = [
        ("基本組件", test_basic_components),
        ("資料庫連線", test_database_connection),
        ("OpenAI API", test_openai_connection),
        ("文字處理", test_text_processing),
        ("文件分類", test_document_classification),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 測試出現異常: {e}")
            results[test_name] = False
    
    # 總結報告
    print("\n" + "=" * 50)
    print("📊 測試結果總結")
    print("-" * 30)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("🎉 所有功能測試正常！分類器已達到預期功能。")
    elif passed >= total * 0.8:
        print("⚠️  大部分功能正常，有少數問題需要修復。")
    else:
        print("❌ 多項功能存在問題，需要進一步檢查。")
    
    return passed == total

if __name__ == "__main__":
    main()
