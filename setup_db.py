#!/usr/bin/env python3
"""
設置 TiDB Cloud 數據庫 schema
"""
import mysql.connector
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def setup_tidb_cloud_schema():
    """設置 TiDB Cloud 的 schema"""
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

        # 讀取 schema 檔案
        with open('scripts/tidb_cloud_schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # 分割並執行 SQL 語句
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]

        for statement in statements:
            print(f"📝 執行: {statement[:50]}...")
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

        print("🎉 TiDB Cloud schema 設置完成！")
        return True

    except Exception as e:
        print(f"❌ 設置失敗: {e}")
        return False

def test_connection():
    """測試連接並檢查表是否存在"""
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

        # 檢查表是否存在
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"📊 資料庫 'rag' 中的表: {[table[0] for table in tables]}")

        # 檢查 embeddings 表結構
        if ('embeddings',) in tables:
            cursor.execute("DESCRIBE embeddings")
            columns = cursor.fetchall()
            print("📋 embeddings 表結構:")
            for col in columns:
                print(f"  {col[0]}: {col[1]}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ 測試連接失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始設置 TiDB Cloud")
    print("=" * 40)

    if setup_tidb_cloud_schema():
        print("\n" + "-" * 30 + "\n")
        test_connection()
    else:
        print("❌ 設置失敗，請檢查配置")
