#!/usr/bin/env python3
"""
測試 OpenAI API 整合功能
"""

import os
import sys
import json
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def test_openai_classification():
    """測試 OpenAI 文件分類功能"""
    print("🤖 測試 OpenAI 文件分類功能")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 測試文件
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
        
        prompt = f"""
請分析以下文件內容，並提供詳細的分類資訊。請以JSON格式回答：

文件內容：
{test_text}

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
        
        print("   🔍 向 OpenAI 發送分析請求...")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是專業的文件分類助手，擅長分析家庭文件並提取關鍵資訊。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        # 解析回應
        result_text = response.choices[0].message.content.strip()
        print(f"   📝 AI 原始回應: {result_text[:200]}...")
        
        # 嘗試提取 JSON
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = result_text[json_start:json_end]
            result = json.loads(json_text)
            
            print("   ✅ AI 分析結果:")
            print(f"      分類: {result.get('category', '無')}")
            print(f"      信心度: {result.get('confidence', 0):.2f}")
            
            extracted_data = result.get('extracted_data', {})
            if extracted_data:
                print("      提取數據:")
                for key, value in extracted_data.items():
                    if value:
                        print(f"        {key}: {value}")
            
            suggested_tags = result.get('suggested_tags', [])
            if suggested_tags:
                print(f"      建議標籤: {', '.join(suggested_tags)}")
            
            reasoning = result.get('reasoning', '')
            if reasoning:
                print(f"      分析依據: {reasoning[:100]}...")
            
            # 驗證結果
            expected_category = "帳單"
            is_correct = result.get('category') == expected_category
            confidence = result.get('confidence', 0)
            has_amount = extracted_data.get('amount') is not None
            has_date = extracted_data.get('date') is not None
            
            print(f"   📊 結果評估:")
            print(f"      分類正確性: {'✅' if is_correct else '❌'} (預期: {expected_category})")
            print(f"      信心度合理: {'✅' if confidence >= 0.8 else '❌'} ({confidence:.2f})")
            print(f"      金額提取: {'✅' if has_amount else '❌'}")
            print(f"      日期提取: {'✅' if has_date else '❌'}")
            print(f"      標籤建議: {'✅' if suggested_tags else '❌'}")
            
            score = sum([is_correct, confidence >= 0.8, has_amount, has_date, bool(suggested_tags)])
            total = 5
            
            print(f"   🎯 總體評分: {score}/{total} ({score/total*100:.1f}%)")
            
            return score >= 4  # 80% 以上算通過
            
        else:
            print("   ❌ 無法解析 AI 回應中的 JSON")
            return False
            
    except Exception as e:
        print(f"   ❌ OpenAI API 測試失敗: {e}")
        return False

def test_multiple_documents():
    """測試多個文件的分類"""
    print("\n🔍 測試多種文件類型分類")
    
    test_documents = [
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
            """,
            "expected": "收據"
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
            """,
            "expected": "成績單"
        }
    ]
    
    try:
        sys.path.append('/home/hom/services/rag-store')
        from rag_store.classification_system import DocumentClassifier
        
        classifier = DocumentClassifier()
        
        correct_count = 0
        
        for doc in test_documents:
            print(f"\n   📄 測試: {doc['name']}")
            
            try:
                result = classifier.classify_document(doc['content'])
                
                predicted = result.get('category', '其他')
                expected = doc['expected']
                confidence = result.get('confidence', 0)
                
                is_correct = predicted == expected
                status = "✅" if is_correct else "❌"
                
                print(f"      {status} 分類: {predicted} (預期: {expected})")
                print(f"      信心度: {confidence:.2f}")
                
                if result.get('extracted_data'):
                    print(f"      提取數據: {len(result['extracted_data'])} 項")
                
                if result.get('suggested_tags'):
                    print(f"      建議標籤: {len(result['suggested_tags'])} 個")
                
                if is_correct:
                    correct_count += 1
                    
            except Exception as e:
                print(f"      ❌ 分類失敗: {e}")
        
        accuracy = correct_count / len(test_documents)
        print(f"\n   📊 分類準確率: {accuracy:.2f} ({correct_count}/{len(test_documents)})")
        
        return accuracy >= 0.8
        
    except Exception as e:
        print(f"   ❌ 多文件測試失敗: {e}")
        return False

def main():
    """主要測試函數"""
    print("🤖 OpenAI 整合功能測試")
    print("=" * 50)
    
    # 檢查環境變數
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY 環境變數未設置")
        return False
    
    print(f"✅ OpenAI API Key: {api_key[:8]}...{api_key[-8:]}")
    
    tests = [
        ("單一文件分類", test_openai_classification),
        ("多種文件分類", test_multiple_documents)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 測試出現異常: {e}")
            results[test_name] = False
    
    # 總結報告
    print("\n" + "=" * 50)
    print("📊 OpenAI 整合測試結果")
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
        print("🎉 OpenAI 整合功能正常！分類器 AI 功能達到預期。")
        return True
    elif passed >= total * 0.5:
        print("⚠️  部分 OpenAI 功能正常，需要調整。")
        return False
    else:
        print("❌ OpenAI 整合功能存在嚴重問題。")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎯 結論: 分類器的 AI 智能分類功能已達到預期水準！")
    else:
        print("\n⚠️  結論: 分類器的 AI 功能需要進一步優化。")
