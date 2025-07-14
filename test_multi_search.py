#!/usr/bin/env python3
"""
多維度搜尋與過濾功能測試腳本
"""

import requests
import json
import sys
from datetime import datetime, timedelta

API_BASE_URL = "http://127.0.0.1:8000"

def test_search_filters():
    """測試搜尋過濾器API"""
    print("\n🔍 測試搜尋過濾器API")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/search/filters")
        
        if response.status_code == 200:
            filters = response.json()
            
            print("✅ 過濾器API正常")
            print(f"   分類數量: {len(filters.get('categories', []))}")
            print(f"   標籤數量: {len(filters.get('tags', []))}")
            print(f"   家庭成員數量: {len(filters.get('family_members', []))}")
            print(f"   金額範圍: {len(filters.get('amount_ranges', []))}")
            print(f"   日期範圍: {len(filters.get('date_ranges', []))}")
            
            # 顯示部分內容
            if filters.get('categories'):
                print("\n   可用分類:")
                for cat in filters['categories'][:3]:
                    print(f"     {cat.get('icon', '')} {cat.get('name', '')}")
            
            return True
        else:
            print(f"❌ 過濾器API失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 過濾器API測試錯誤: {e}")
        return False

def test_basic_search():
    """測試基本多維度搜尋"""
    print("\n🔍 測試基本多維度搜尋")
    print("-" * 40)
    
    test_queries = [
        {
            "name": "純語義搜尋",
            "params": {
                "query": "帳單",
                "search_mode": "semantic"
            }
        },
        {
            "name": "分類過濾搜尋",
            "params": {
                "query": "費用",
                "category": "帳單",
                "search_mode": "hybrid"
            }
        },
        {
            "name": "日期範圍搜尋",
            "params": {
                "query": "支付",
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "search_mode": "filter"
            }
        }
    ]
    
    success_count = 0
    
    for test in test_queries:
        print(f"\n   📝 測試: {test['name']}")
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/query", json=test['params'])
            
            if response.status_code == 200:
                data = response.json()
                sources_count = len(data.get('sources', []))
                answer_length = len(data.get('answer', ''))
                
                print(f"      ✅ 成功")
                print(f"      來源數量: {sources_count}")
                print(f"      回答長度: {answer_length} 字")
                
                # 檢查回答中是否包含搜尋統計
                if "搜尋結果統計" in data.get('answer', ''):
                    print(f"      ✅ 包含搜尋統計資訊")
                
                success_count += 1
            else:
                print(f"      ❌ 失敗: {response.status_code}")
                print(f"      錯誤: {response.text}")
                
        except Exception as e:
            print(f"      ❌ 錯誤: {e}")
    
    print(f"\n   📊 基本搜尋成功率: {success_count}/{len(test_queries)} ({success_count/len(test_queries)*100:.1f}%)")
    return success_count == len(test_queries)

def test_advanced_search():
    """測試進階搜尋API"""
    print("\n🔍 測試進階搜尋API")
    print("-" * 40)
    
    test_cases = [
        {
            "name": "複合條件搜尋",
            "params": {
                "query": "電費",
                "category": "帳單",
                "tags": ["重要"],
                "search_mode": "hybrid"
            }
        },
        {
            "name": "金額範圍搜尋",
            "params": {
                "query": "費用",
                "amount_min": 100,
                "amount_max": 5000,
                "search_mode": "filter"
            }
        },
        {
            "name": "家庭成員搜尋",
            "params": {
                "query": "醫療",
                "family_member": "父親",
                "search_mode": "hybrid"
            }
        }
    ]
    
    success_count = 0
    
    for test in test_cases:
        print(f"\n   📝 測試: {test['name']}")
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/search/advanced", json=test['params'])
            
            if response.status_code == 200:
                data = response.json()
                results_count = len(data.get('results', []))
                stats = data.get('statistics', {})
                
                print(f"      ✅ 成功")
                print(f"      結果數量: {results_count}")
                print(f"      總結果數: {stats.get('total_results', 0)}")
                print(f"      分類數量: {stats.get('categories_found', 0)}")
                
                # 檢查結果結構
                if results_count > 0:
                    first_result = data['results'][0]
                    required_fields = ['doc_id', 'chunk', 'filename', 'category']
                    missing_fields = [field for field in required_fields if field not in first_result]
                    
                    if not missing_fields:
                        print(f"      ✅ 結果結構完整")
                    else:
                        print(f"      ⚠️  缺少欄位: {missing_fields}")
                
                success_count += 1
            else:
                print(f"      ❌ 失敗: {response.status_code}")
                print(f"      錯誤: {response.text}")
                
        except Exception as e:
            print(f"      ❌ 錯誤: {e}")
    
    print(f"\n   📊 進階搜尋成功率: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    return success_count == len(test_cases)

def test_search_suggestions():
    """測試搜尋建議API"""
    print("\n🔍 測試搜尋建議API")
    print("-" * 40)
    
    test_queries = ["電費", "健康", "成績", "保險"]
    
    success_count = 0
    
    for query in test_queries:
        print(f"\n   📝 測試查詢: '{query}'")
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/search/suggestions?q={query}")
            
            if response.status_code == 200:
                suggestions = response.json()
                
                categories_count = len(suggestions.get('categories', []))
                tags_count = len(suggestions.get('tags', []))
                members_count = len(suggestions.get('family_members', []))
                
                print(f"      ✅ 成功")
                print(f"      建議分類: {categories_count}")
                print(f"      建議標籤: {tags_count}")
                print(f"      建議成員: {members_count}")
                
                success_count += 1
            else:
                print(f"      ❌ 失敗: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ 錯誤: {e}")
    
    print(f"\n   📊 建議API成功率: {success_count}/{len(test_queries)} ({success_count/len(test_queries)*100:.1f}%)")
    return success_count == len(test_queries)

def test_performance():
    """測試搜尋效能"""
    print("\n⚡ 測試搜尋效能")
    print("-" * 40)
    
    import time
    
    # 測試不同搜尋模式的效能
    search_modes = ["semantic", "filter", "hybrid"]
    
    for mode in search_modes:
        print(f"\n   📝 測試模式: {mode}")
        
        start_time = time.time()
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/query", json={
                "query": "帳單費用",
                "search_mode": mode
            })
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                sources_count = len(data.get('sources', []))
                
                print(f"      ✅ 成功")
                print(f"      響應時間: {duration:.2f} 秒")
                print(f"      結果數量: {sources_count}")
                
                # 效能評估
                if duration < 2.0:
                    print(f"      🚀 效能優秀")
                elif duration < 5.0:
                    print(f"      ✅ 效能良好")
                else:
                    print(f"      ⚠️  效能需要改善")
            else:
                print(f"      ❌ 失敗: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ 錯誤: {e}")

def main():
    """主測試函數"""
    print("🧪 多維度搜尋與過濾功能測試")
    print("=" * 50)
    
    # 檢查服務器是否運行
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 服務器未運行，請先啟動後端服務")
            sys.exit(1)
    except Exception:
        print("❌ 無法連接到服務器，請檢查服務是否正在運行")
        sys.exit(1)
    
    print("✅ 服務器連接正常")
    
    # 執行各項測試
    results = []
    
    results.append(("搜尋過濾器API", test_search_filters()))
    results.append(("基本多維度搜尋", test_basic_search()))
    results.append(("進階搜尋API", test_advanced_search()))
    results.append(("搜尋建議API", test_search_suggestions()))
    
    # 效能測試
    test_performance()
    
    # 測試總結
    print("\n" + "=" * 50)
    print("📋 測試結果總結")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 總體通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有測試通過！多維度搜尋功能正常運作")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查系統配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
