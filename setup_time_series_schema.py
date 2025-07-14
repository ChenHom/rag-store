#!/usr/bin/env python3
"""
直接建立時間序列架構的腳本
"""

import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def create_time_series_schema():
    """建立時間序列架構"""
    try:
        # 連接到 TiDB Cloud
        conn = mysql.connector.connect(
            host=os.getenv("TIDB_HOST"),
            user=os.getenv("TIDB_USER"),
            password=os.getenv("TIDB_PASSWORD"),
            database=os.getenv("TIDB_DB", "rag"),
            ssl_disabled=False,
            use_unicode=True
        )
        
        cursor = conn.cursor()
        
        # 1. 時間序列數據類型表
        print("建立 time_series_types 表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_series_types (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            unit VARCHAR(20),
            category VARCHAR(50),
            data_type ENUM('numeric', 'percentage', 'score', 'amount') DEFAULT 'numeric',
            color VARCHAR(7),
            icon VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 2. 時間序列數據表
        print("建立 time_series_data 表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_series_data (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            series_type_id BIGINT NOT NULL,
            family_member_id BIGINT,
            document_id BIGINT,
            data_date DATE NOT NULL,
            value DECIMAL(15,4) NOT NULL,
            additional_info JSON,
            source VARCHAR(100),
            confidence_score FLOAT DEFAULT 1.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (series_type_id) REFERENCES time_series_types(id) ON DELETE CASCADE,
            INDEX idx_series_type_date (series_type_id, data_date),
            INDEX idx_document_id (document_id),
            UNIQUE KEY unique_entry (series_type_id, family_member_id, data_date, document_id)
        )
        """)
        
        # 3. 時間序列分析結果表
        print("建立 time_series_analysis 表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_series_analysis (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            series_type_id BIGINT NOT NULL,
            family_member_id BIGINT,
            analysis_type ENUM('trend', 'average', 'growth_rate', 'forecast') NOT NULL,
            period_type ENUM('weekly', 'monthly', 'quarterly', 'yearly') NOT NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            result_value DECIMAL(15,4),
            result_data JSON,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (series_type_id) REFERENCES time_series_types(id) ON DELETE CASCADE,
            INDEX idx_series_analysis (series_type_id, analysis_type, period_type)
        )
        """)
        
        # 4. 時間序列警報規則表
        print("建立 time_series_alerts 表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_series_alerts (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            series_type_id BIGINT NOT NULL,
            family_member_id BIGINT,
            alert_name VARCHAR(100) NOT NULL,
            condition_type ENUM('threshold_high', 'threshold_low', 'rapid_change', 'trend_analysis') NOT NULL,
            threshold_value DECIMAL(15,4),
            change_percentage DECIMAL(5,2),
            period_days INT DEFAULT 30,
            is_active BOOLEAN DEFAULT TRUE,
            last_triggered TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (series_type_id) REFERENCES time_series_types(id) ON DELETE CASCADE
        )
        """)
        
        # 5. 時間序列警報記錄表
        print("建立 time_series_alert_logs 表...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_series_alert_logs (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            alert_id BIGINT NOT NULL,
            triggered_date DATE NOT NULL,
            current_value DECIMAL(15,4),
            previous_value DECIMAL(15,4),
            message TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (alert_id) REFERENCES time_series_alerts(id) ON DELETE CASCADE,
            INDEX idx_alert_date (alert_id, triggered_date)
        )
        """)
        
        # 插入預設時間序列類型
        print("插入預設時間序列類型...")
        time_series_types = [
            ('體重', '體重記錄', 'kg', '健康', 'numeric', '#FF6B6B', '⚖️'),
            ('身高', '身高記錄', 'cm', '健康', 'numeric', '#4ECDC4', '📏'),
            ('BMI', '身體質量指數', 'BMI', '健康', 'numeric', '#45B7D1', '🏃'),
            ('血壓收縮壓', '收縮壓數值', 'mmHg', '健康', 'numeric', '#FF4757', '❤️'),
            ('血壓舒張壓', '舒張壓數值', 'mmHg', '健康', 'numeric', '#FF3838', '💓'),
            ('體脂率', '體脂肪百分比', '%', '健康', 'percentage', '#FFA502', '📊'),
            ('月支出', '每月總支出', '元', '財務', 'amount', '#2ED573', '💰'),
            ('月收入', '每月總收入', '元', '財務', 'amount', '#3742FA', '💵'),
            ('儲蓄率', '每月儲蓄率', '%', '財務', 'percentage', '#8E44AD', '🏦'),
            ('水電費', '水電費支出', '元', '財務', 'amount', '#E74C3C', '⚡'),
            ('電話費', '電話費支出', '元', '財務', 'amount', '#3498DB', '📞'),
            ('信用卡費', '信用卡費用', '元', '財務', 'amount', '#F39C12', '💳'),
            ('國文成績', '國文科成績', '分', '學習', 'score', '#9B59B6', '📚'),
            ('數學成績', '數學科成績', '分', '學習', 'score', '#1ABC9C', '🔢'),
            ('英文成績', '英文科成績', '分', '學習', 'score', '#E67E22', '🌍'),
            ('總平均', '學期總平均', '分', '學習', 'score', '#34495E', '🎯'),
            ('GPA', '學期GPA', 'GPA', '學習', 'numeric', '#16A085', '🏆'),
            ('運動時數', '每週運動時間', '小時', '生活', 'numeric', '#27AE60', '🏃‍♂️'),
            ('睡眠時數', '每日睡眠時間', '小時', '生活', 'numeric', '#8E44AD', '😴'),
            ('閱讀時數', '每週閱讀時間', '小時', '生活', 'numeric', '#D35400', '📖')
        ]
        
        for type_data in time_series_types:
            cursor.execute("""
                INSERT IGNORE INTO time_series_types 
                (name, description, unit, category, data_type, color, icon) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, type_data)
        
        # 插入範例警報規則
        print("插入範例警報規則...")
        cursor.execute("""
            INSERT IGNORE INTO time_series_alerts 
            (series_type_id, alert_name, condition_type, threshold_value, change_percentage, period_days) 
            SELECT id, '體重異常增加', 'rapid_change', NULL, 5.0, 30 
            FROM time_series_types WHERE name = '體重'
        """)
        
        cursor.execute("""
            INSERT IGNORE INTO time_series_alerts 
            (series_type_id, alert_name, condition_type, threshold_value, change_percentage, period_days) 
            SELECT id, '體重過重警告', 'threshold_high', 80.0, NULL, 1 
            FROM time_series_types WHERE name = '體重'
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ 時間序列架構建立完成！")
        return True
        
    except Exception as e:
        print(f"❌ 建立架構失敗: {e}")
        return False

if __name__ == "__main__":
    create_time_series_schema()
