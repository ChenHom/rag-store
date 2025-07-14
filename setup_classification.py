#!/usr/bin/env python3
"""
設置家庭資料管理分類系統資料庫架構
"""

import mysql.connector
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def setup_classification_schema():
    """設置分類系統的資料庫架構"""
    try:
        # TiDB Cloud 配置
        config = {
            'host': os.getenv("TIDB_HOST"),
            'user': os.getenv("TIDB_USER"),
            'password': os.getenv("TIDB_PASSWORD"),
            'ssl_disabled': False,
            'use_unicode': True
        }

        print("🔌 連接到 TiDB Cloud...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # 讀取分類系統 schema 檔案
        with open('scripts/classification_schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # 分割並執行 SQL 語句
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]

        for statement in statements:
            print(f"📝 執行: {statement[:80]}...")
            try:
                cursor.execute(statement)
                print("✅ 成功")
            except mysql.connector.Error as e:
                if "already exists" in str(e) or "Duplicate" in str(e):
                    print("⚠️  已存在，跳過")
                else:
                    print(f"❌ 錯誤: {e}")
                    raise

        conn.commit()
        cursor.close()
        conn.close()

        print("🎉 分類系統資料庫架構設置完成！")
        return True

    except Exception as e:
        print(f"❌ 設置失敗: {e}")
        return False

def test_classification_schema():
    """測試分類系統架構"""
    try:
        config = {
            'host': os.getenv("TIDB_HOST"),
            'user': os.getenv("TIDB_USER"),
            'password': os.getenv("TIDB_PASSWORD"),
            'database': 'rag',
            'ssl_disabled': False,
            'use_unicode': True
        }

        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # 檢查新建立的表
        new_tables = ['categories', 'family_members', 'tags', 'documents', 'document_tags']
        
        for table in new_tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            result = cursor.fetchone()
            if result:
                print(f"✅ 表 '{table}' 存在")
                
                # 檢查表結構
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"   欄位數量: {len(columns)}")
            else:
                print(f"❌ 表 '{table}' 不存在")

        # 檢查預設資料
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        print(f"📊 預設分類數量: {category_count}")

        cursor.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]
        print(f"🏷️  預設標籤數量: {tag_count}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始設置家庭資料管理分類系統")
    print("=" * 50)

    if setup_classification_schema():
        print("\n" + "-" * 30 + "\n")
        test_classification_schema()
    else:
        print("❌ 設置失敗，請檢查配置")
