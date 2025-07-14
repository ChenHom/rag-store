#!/usr/bin/env python3
"""
時間序列追蹤功能完整測試腳本
測試數據提取、分析、警報等所有功能
"""

import os
import sys
import json
import mysql.connector
from datetime import date, datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from rag_store.time_series_analyzer import TimeSeriesAnalyzer, process_document_for_time_series

def get_test_connection():
    """建立測試資料庫連接"""
    try:
        # 嘗試連接 TiDB Cloud
        tidb_host = os.getenv("TIDB_HOST")
        tidb_user = os.getenv("TIDB_USER")
        tidb_password = os.getenv("TIDB_PASSWORD")
        tidb_db = os.getenv("TIDB_DB", "rag")
        
        if all([tidb_host, tidb_user, tidb_password]):
            conn = mysql.connector.connect(
                host=tidb_host,
                user=tidb_user,
                password=tidb_password,
                database=tidb_db,
                ssl_disabled=False,
                use_unicode=True
            )
            print(f"✅ 成功連接到 TiDB Cloud: {tidb_host}")
            return conn
        else:
            print("❌ TiDB Cloud 環境變數未設定")
            return None
            
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")
        return None

def setup_test_database():
    """設定測試資料庫架構"""
    print("🔧 設定測試資料庫架構...")
    
    conn = get_test_connection()
    if not conn:
        print("❌ 無法連接資料庫")
        return False
    
    try:
        cursor = conn.cursor()
        
        # 執行時間序列架構 SQL
        schema_file = project_root / "scripts" / "time_series_schema.sql"
        if schema_file.exists():
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_commands = f.read()
                
            # 分割並執行 SQL 命令
            for command in sql_commands.split(';'):
                command = command.strip()
                if command and not command.startswith('--'):
                    try:
                        cursor.execute(command)
                    except mysql.connector.Error as e:
                        if "already exists" not in str(e):
                            print(f"SQL 執行警告: {e}")
            
            conn.commit()
            print("✅ 資料庫架構設定完成")
            return True
        else:
            print(f"❌ 找不到架構檔案: {schema_file}")
            return False
            
    except Exception as e:
        print(f"❌ 資料庫架構設定失敗: {e}")
        return False
    finally:
        conn.close()

def test_data_extraction():
    """測試數據提取功能"""
    print("\n📊 測試數據提取功能...")
    
    conn = get_test_connection()
    if not conn:
        return False
    
    analyzer = TimeSeriesAnalyzer(conn)
    
    # 測試用文字範例
    test_texts = [
        "體重: 65.5 kg, 身高: 170 cm, 血壓: 120/80",
        "數學成績: 85分, 英文成績: 78分, 國文: 82分",
        "本月支出: NT$ 25,000元, 收入: 50,000元",
        "BMI: 22.5, 體脂率: 15.2%",
        "本次健康檢查結果：體重 68.2公斤，身高 175公分，血壓 125/82"
    ]
    
    success_count = 0
    for i, text in enumerate(test_texts):
        print(f"  測試文字 {i+1}: {text[:50]}...")
        
        # 提取數據
        extracted_data = analyzer.extract_numeric_values(text)
        print(f"    提取到 {len(extracted_data)} 個數據點")
        
        # 儲存到資料庫
        test_date = date.today() - timedelta(days=i)
        for data in extracted_data:
            if analyzer.store_time_series_data(
                data['type'], data['value'], test_date, 
                None, None, data['confidence']
            ):
                success_count += 1
    
    conn.close()
    print(f"✅ 成功提取並儲存 {success_count} 個數據點")
    return success_count > 0

def test_trend_analysis():
    """測試趨勢分析功能"""
    print("\n📈 測試趨勢分析功能...")
    
    conn = get_test_connection()
    if not conn:
        return False
    
    analyzer = TimeSeriesAnalyzer(conn)
    
    # 測試不同的時間序列
    test_series = ['體重', '數學成績', '月支出']
    
    for series_name in test_series:
        print(f"  分析 {series_name} 趨勢...")
        
        # 取得數據
        data_points = analyzer.get_time_series_data(
            series_name, 
            start_date=date.today() - timedelta(days=30),
            end_date=date.today()
        )
        
        if data_points:
            print(f"    找到 {len(data_points)} 個數據點")
            
            # 趨勢分析
            trend = analyzer.analyze_trend(data_points, 30)
            print(f"    趨勢類型: {trend.trend_type}")
            print(f"    變化百分比: {trend.change_percentage:.1f}%")
            print(f"    信心度: {trend.confidence:.2f}")
            
            # 統計摘要
            stats = analyzer.get_statistics_summary(series_name, period_days=30)
            if stats:
                print(f"    最新值: {stats.get('latest_value')}")
                print(f"    平均值: {stats.get('average_value', 0):.2f}")
        else:
            print(f"    ❌ 沒有找到 {series_name} 的數據")
    
    conn.close()
    print("✅ 趨勢分析測試完成")
    return True

def test_alert_system():
    """測試警報系統"""
    print("\n🚨 測試警報系統...")
    
    conn = get_test_connection()
    if not conn:
        return False
    
    analyzer = TimeSeriesAnalyzer(conn)
    
    # 檢查現有警報規則
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as count FROM time_series_alerts WHERE is_active = 1")
    alert_count = cursor.fetchone()['count']
    print(f"  找到 {alert_count} 個活躍警報規則")
    
    # 測試警報檢查
    test_series = ['體重', '數學成績', '月支出']
    
    total_alerts = 0
    for series_name in test_series:
        print(f"  檢查 {series_name} 警報...")
        alerts = analyzer.check_alerts(series_name)
        
        if alerts:
            print(f"    觸發 {len(alerts)} 個警報:")
            for alert in alerts:
                print(f"      - {alert['alert_name']}: {alert['message']}")
                total_alerts += 1
        else:
            print(f"    沒有觸發警報")
    
    conn.close()
    print(f"✅ 警報系統測試完成，共觸發 {total_alerts} 個警報")
    return True

def test_api_simulation():
    """模擬 API 呼叫測試"""
    print("\n🌐 模擬 API 呼叫測試...")
    
    conn = get_test_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 測試 1: 取得時間序列類型
        print("  測試取得時間序列類型...")
        cursor.execute("""
            SELECT id, name, description, unit, category, data_type, color, icon
            FROM time_series_types
            ORDER BY category, name
        """)
        types = cursor.fetchall()
        print(f"    找到 {len(types)} 個時間序列類型")
        
        # 測試 2: 取得時間序列數據
        print("  測試取得時間序列數據...")
        if types:
            test_type = types[0]['name']
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            cursor.execute("""
                SELECT tsd.*, tst.name as series_name, tst.unit
                FROM time_series_data tsd
                JOIN time_series_types tst ON tsd.series_type_id = tst.id
                WHERE tst.name = %s AND tsd.data_date >= %s AND tsd.data_date <= %s
                ORDER BY tsd.data_date ASC
            """, (test_type, start_date, end_date))
            
            data_points = cursor.fetchall()
            print(f"    {test_type} 有 {len(data_points)} 個數據點")
        
        # 測試 3: 取得警報記錄
        print("  測試取得警報記錄...")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM time_series_alert_logs
            WHERE triggered_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """)
        recent_alerts = cursor.fetchone()['count']
        print(f"    最近7天有 {recent_alerts} 個警報記錄")
        
        print("✅ API 模擬測試完成")
        return True
        
    except Exception as e:
        print(f"❌ API 模擬測試失敗: {e}")
        return False
    finally:
        conn.close()

def generate_sample_data():
    """產生範例數據供測試"""
    print("\n🎲 產生範例數據...")
    
    conn = get_test_connection()
    if not conn:
        return False
    
    analyzer = TimeSeriesAnalyzer(conn)
    
    # 產生過去30天的模擬數據
    base_date = date.today() - timedelta(days=30)
    
    sample_data = [
        # 體重數據 (模擬微幅變化)
        ('體重', [65.0 + i * 0.1 + (i % 3) * 0.2 for i in range(30)]),
        # 數學成績 (模擬學習進步)
        ('數學成績', [70 + i * 0.5 + (i % 5) * 3 for i in range(10)]),
        # 月支出 (模擬每週記錄)
        ('月支出', [25000 + i * 500 + (i % 2) * 1000 for i in range(8)]),
    ]
    
    total_points = 0
    for series_name, values in sample_data:
        print(f"  產生 {series_name} 數據...")
        
        for i, value in enumerate(values):
            test_date = base_date + timedelta(days=i)
            if analyzer.store_time_series_data(
                series_name, value, test_date, 
                None, None, 0.95, f"測試數據 {i+1}"
            ):
                total_points += 1
    
    conn.close()
    print(f"✅ 成功產生 {total_points} 個範例數據點")
    return total_points > 0

def run_comprehensive_test():
    """執行完整測試"""
    print("🚀 開始時間序列追蹤功能完整測試")
    print("=" * 60)
    
    test_results = {}
    
    # 1. 設定資料庫
    test_results['database_setup'] = setup_test_database()
    
    # 2. 產生範例數據
    test_results['sample_data'] = generate_sample_data()
    
    # 3. 測試數據提取
    test_results['data_extraction'] = test_data_extraction()
    
    # 4. 測試趨勢分析
    test_results['trend_analysis'] = test_trend_analysis()
    
    # 5. 測試警報系統
    test_results['alert_system'] = test_alert_system()
    
    # 6. 模擬 API 測試
    test_results['api_simulation'] = test_api_simulation()
    
    # 輸出測試結果
    print("\n" + "=" * 60)
    print("📋 測試結果摘要:")
    print("-" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed += 1
    
    print("-" * 30)
    print(f"總計: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("\n🎉 所有測試都通過了！時間序列追蹤功能已完成")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 項測試失敗，需要修復")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
