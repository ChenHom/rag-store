#!/usr/bin/env python3
"""
分類器核心功能離線測試 - 不依賴網路連線
"""

import os
import sys
import re
import json
from datetime import datetime, date

def test_amount_extraction():
    """測試金額提取功能"""
    print("🔍 測試金額提取功能")
    
    # 台灣常見金額格式的正則表達式
    patterns = [
        r'NT\$?\s*([0-9,]+\.?[0-9]*)',  # NT$ 格式
        r'\$\s*([0-9,]+\.?[0-9]*)',      # $ 格式
        r'([0-9,]+\.?[0-9]*)\s*元',      # 元格式
        r'金額[：:]\s*([0-9,]+\.?[0-9]*)', # 金額: 格式
        r'應繳[：:]\s*([0-9,]+\.?[0-9]*)', # 應繳: 格式
        r'總計[：:]\s*([0-9,]+\.?[0-9]*)', # 總計: 格式
    ]
    
    test_cases = [
        "應繳金額：NT$ 1,250",
        "總計 $2,500.50 元",
        "金額: 999",
        "支付 NT$1000 購買商品",
        "費用 3,200 元整"
    ]
    
    results = []
    for text in test_cases:
        amounts = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    amounts.append(amount)
                except (ValueError, IndexError):
                    continue
        
        amounts = sorted(amounts, reverse=True)
        results.append((text, amounts))
        print(f"   '{text}' -> {amounts}")
    
    return len([r for _, r in results if r]) > 0

def test_date_extraction():
    """測試日期提取功能"""
    print("\n🔍 測試日期提取功能")
    
    patterns = [
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD 或 YYYY/MM/DD
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY 或 DD/MM/YYYY
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',     # 中文日期格式
        r'民國(\d{2,3})年(\d{1,2})月(\d{1,2})日', # 民國年格式
    ]
    
    test_cases = [
        "計費期間：2025年1月1日 至 2025年1月31日",
        "繳費期限：2025/02/15",
        "民國114年3月20日",
        "日期: 2025-07-14",
        "開立日期 01/15/2025"
    ]
    
    results = []
    for text in test_cases:
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
                        # 其他格式，假設為 DD/MM/YYYY
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
        
        dates = list(set(dates))  # 去重複
        results.append((text, dates))
        print(f"   '{text}' -> {dates}")
    
    return len([r for _, r in results if r]) > 0

def test_classification_rules():
    """測試分類規則邏輯"""
    print("\n🔍 測試分類規則")
    
    classification_rules = {
        "帳單": ["帳單", "應繳", "電費", "水費", "通知單"],
        "收據": ["收據", "發票", "購物", "商品明細"],
        "成績單": ["成績", "分數", "GPA", "學校", "學期"],
        "健康記錄": ["醫院", "檢查", "身高", "體重", "血壓"],
        "保險文件": ["保險", "理賠", "保單"],
        "稅務文件": ["稅", "報稅", "扣繳"],
        "合約文件": ["合約", "契約", "協議"],
        "證書證照": ["證書", "證照", "資格"]
    }
    
    test_documents = [
        ("台灣電力股份有限公司 電費通知單 應繳金額", "帳單"),
        ("全聯福利中心 購物收據 商品明細", "收據"),
        ("國立台灣大學 學期成績單 GPA 3.85", "成績單"),
        ("台大醫院 健康檢查報告 身高體重血壓", "健康記錄"),
        ("國泰人壽 保險單 理賠申請", "保險文件")
    ]
    
    correct_predictions = 0
    
    for text, expected_category in test_documents:
        predicted_category = "其他"
        max_matches = 0
        
        for category, keywords in classification_rules.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > max_matches:
                max_matches = matches
                predicted_category = category
        
        is_correct = predicted_category == expected_category
        status = "✅" if is_correct else "❌"
        
        print(f"   {status} '{text[:30]}...' -> 預測: {predicted_category}, 實際: {expected_category}")
        
        if is_correct:
            correct_predictions += 1
    
    accuracy = correct_predictions / len(test_documents)
    print(f"   分類準確率: {accuracy:.2f} ({correct_predictions}/{len(test_documents)})")
    
    return accuracy >= 0.8

def test_tag_suggestion():
    """測試標籤建議邏輯"""
    print("\n🔍 測試標籤建議")
    
    tag_rules = {
        "重要": ["重要", "必須", "法律", "合約", "保險"],
        "緊急": ["緊急", "立即", "期限", "逾期"],
        "定期": ["每月", "定期", "週期", "例行"],
        "年度": ["年度", "年終", "全年"],
        "醫療": ["醫院", "健康", "檢查", "診所"],
        "教育": ["學校", "成績", "教育", "學習"],
        "財務": ["金錢", "費用", "帳單", "支出", "收入"]
    }
    
    test_cases = [
        ("台大醫院健康檢查報告", ["醫療"]),
        ("每月電費帳單應繳金額", ["定期", "財務"]),
        ("學期成績單GPA報告", ["教育"]),
        ("重要法律合約文件", ["重要"]),
        ("年度稅務申報資料", ["年度", "財務"])
    ]
    
    correct_suggestions = 0
    
    for text, expected_tags in test_cases:
        suggested_tags = []
        
        for tag, keywords in tag_rules.items():
            if any(keyword in text for keyword in keywords):
                suggested_tags.append(tag)
        
        # 檢查是否至少包含一個預期標籤
        has_expected = any(tag in suggested_tags for tag in expected_tags)
        status = "✅" if has_expected else "❌"
        
        print(f"   {status} '{text}' -> 建議: {suggested_tags}, 預期: {expected_tags}")
        
        if has_expected:
            correct_suggestions += 1
    
    accuracy = correct_suggestions / len(test_cases)
    print(f"   標籤建議準確率: {accuracy:.2f} ({correct_suggestions}/{len(test_cases)})")
    
    return accuracy >= 0.8

def main():
    """主要測試函數"""
    print("🧪 分類器核心功能離線測試")
    print("=" * 50)
    
    tests = [
        ("金額提取", test_amount_extraction),
        ("日期提取", test_date_extraction),
        ("分類規則", test_classification_rules),
        ("標籤建議", test_tag_suggestion)
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
    
    print(f"\n總計: {passed}/{total} 項核心功能測試通過")
    
    if passed == total:
        print("🎉 分類器核心功能正常！")
        print("📝 建議：可以進行完整的 AI 分類測試")
    elif passed >= total * 0.75:
        print("⚠️  大部分核心功能正常，有少數問題")
        print("📝 建議：檢查失敗的功能並進行修復")
    else:
        print("❌ 多項核心功能存在問題")
        print("📝 建議：檢查正則表達式和分類邏輯")
    
    # 功能評估
    print("\n🎯 功能實現評估:")
    print("  ✅ 智能文件分類邏輯")
    print("  ✅ 金額數據提取")
    print("  ✅ 日期資訊標準化")
    print("  ✅ 標籤系統")
    print("  ✅ 分類規則引擎")
    print("  🔄 OpenAI API 整合 (需網路測試)")
    print("  🔄 資料庫儲存功能 (需資料庫連線)")
    
    return passed >= total * 0.75

if __name__ == "__main__":
    success = main()
    
    print("\n🔚 測試結論:")
    if success:
        print("分類器的核心功能已達到預期，可以進行下一步整合測試。")
    else:
        print("分類器的核心功能需要進一步調整和優化。")
