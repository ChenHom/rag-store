#!/usr/bin/env python3
"""
測試家庭資料管理分類系統功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_store.classification_system import DocumentClassifier
import json

def test_classification_system():
    """測試分類系統的各項功能"""
    
    print("🧪 測試家庭資料管理分類系統")
    print("=" * 50)
    
    # 初始化分類器
    classifier = DocumentClassifier()
    
    # 測試文件分類
    test_documents = [
        {
            "name": "電費帳單",
            "content": """
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
        },
        {
            "name": "購物收據",
            "content": """
            全聯福利中心
            ================
            2025/01/15 14:30
            店鋪：台北信義店
            
            商品明細：
            牛奶 2瓶          120
            麵包 1條           45
            雞蛋 1盒           80
            蘋果 1袋          150
            
            小計：            395
            現金：            400
            找零：              5
            
            謝謝光臨！
            """
        },
        {
            "name": "健康檢查報告",
            "content": """
            台大醫院健康檢查報告
            
            受檢者：李小華
            性別：女
            年齡：35歲
            檢查日期：2025年1月10日
            
            基本資料：
            身高：165 cm
            體重：58 kg
            BMI：21.3
            血壓：120/80 mmHg
            
            血液檢查：
            膽固醇：180 mg/dL (正常)
            血糖：95 mg/dL (正常)
            白血球：6800 /μL (正常)
            
            總評：各項指標正常，建議持續保持健康生活習慣。
            """
        },
        {
            "name": "成績單",
            "content": """
            國立台灣大學
            學期成績單
            
            學生：陳小明
            學號：B11234567
            學期：113學年度第1學期
            
            科目成績：
            微積分(一)         90分  A-
            普通物理學(一)     85分  B+
            普通化學(一)       88分  B+
            英文(一)          92分  A-
            體育               95分  A
            
            學期平均：90.0
            班級排名：5/45
            累計GPA：3.85
            """
        }
    ]
    
    print("\n🔍 測試文件分類功能")
    print("-" * 30)
    
    for i, doc in enumerate(test_documents, 1):
        print(f"\n📄 測試文件 {i}: {doc['name']}")
        
        try:
            result = classifier.classify_document(doc['content'])
            print(f"  分類結果: {result['category']}")
            print(f"  信心度: {result['confidence']:.2f}")
            
            # 顯示提取的數據
            if result['extracted_data']:
                print("  提取數據:")
                for key, value in result['extracted_data'].items():
                    if value:
                        print(f"    {key}: {value}")
            
            # 顯示建議標籤
            if result['suggested_tags']:
                print(f"  建議標籤: {', '.join(result['suggested_tags'])}")
            
            print(f"  分析原因: {result['reasoning'][:100]}...")
            
        except Exception as e:
            print(f"  ❌ 分類失敗: {e}")
    
    # 測試統計功能
    print("\n📊 測試統計功能")
    print("-" * 30)
    
    try:
        stats = classifier.get_statistics()
        print(f"總文件數: {stats.get('total_documents', 0)}")
        print(f"平均信心度: {stats.get('avg_confidence', 0):.2f}")
        
        print("\n分類統計:")
        for category in stats.get('by_category', []):
            print(f"  {category['icon']} {category['name']}: {category['count']} 文件")
        
        print("\n熱門標籤:")
        for tag in stats.get('by_tags', [])[:5]:
            print(f"  #{tag['name']}: {tag['count']} 次使用")
            
    except Exception as e:
        print(f"❌ 統計功能測試失敗: {e}")
    
    # 測試資料庫連接
    print("\n🔌 測試資料庫連接")
    print("-" * 30)
    
    try:
        conn = classifier.get_db_connection()
        if conn:
            print("✅ 資料庫連接成功")
            cursor = conn.cursor()
            
            # 檢查表是否存在
            tables_to_check = ['categories', 'tags', 'documents', 'family_members', 'document_tags']
            
            for table in tables_to_check:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                result = cursor.fetchone()
                if result:
                    print(f"  ✅ 表 '{table}' 存在")
                else:
                    print(f"  ❌ 表 '{table}' 不存在")
            
            conn.close()
        else:
            print("❌ 資料庫連接失敗")
            
    except Exception as e:
        print(f"❌ 資料庫測試失敗: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 分類系統測試完成！")

if __name__ == "__main__":
    test_classification_system()
