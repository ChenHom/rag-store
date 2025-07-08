import os
import csv
import mysql.connector
from dotenv import load_dotenv
import argparse

# --- 設定 ---
# 假設本機 TiDB 的連線資訊也放在 .env 中，或者使用不同的設定檔
# 為了區分，我們使用 LOCAL_TIDB_ 前置詞
# 請在 .env 中加入以下變數：
# LOCAL_TIDB_HOST="127.0.0.1"
# LOCAL_TIDB_USER="root"
# LOCAL_TIDB_PASSWORD=""
# LOCAL_TIDB_PORT=4000
# LOCAL_TIDB_DB="local_db"

load_dotenv('/home/hom/services/rag-store/.env')

LOCAL_TIDB_HOST = os.getenv("LOCAL_TIDB_HOST", "127.0.0.1")
LOCAL_TIDB_USER = os.getenv("LOCAL_TIDB_USER", "root")
LOCAL_TIDB_PASSWORD = os.getenv("LOCAL_TIDB_PASSWORD", "")
LOCAL_TIDB_PORT = int(os.getenv("LOCAL_TIDB_PORT", 4000))
LOCAL_TIDB_DB = os.getenv("LOCAL_TIDB_DB", "local_db")

def get_local_tidb_connection():
    """建立並返回本機 TiDB 連線"""
    try:
        conn = mysql.connector.connect(
            host=LOCAL_TIDB_HOST,
            port=LOCAL_TIDB_PORT,
            user=LOCAL_TIDB_USER,
            password=LOCAL_TIDB_PASSWORD,
            database=LOCAL_TIDB_DB
        )
        print("Successfully connected to local TiDB.")
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to local TiDB: {err}")
        return None

def import_fin_bill_csv(file_path, conn):
    """從 CSV 檔案匯入財務帳單資料"""
    cursor = conn.cursor()
    
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # 假設 CSV 欄位為: date, item, amount, category
            insert_sql = """
                INSERT INTO fin_bill (date, item, amount, category) 
                VALUES (%s, %s, %s, %s)
            """
            
            data_to_insert = []
            for row in reader:
                data_to_insert.append((
                    row['date'], 
                    row['item'], 
                    float(row['amount']), 
                    row['category']
                ))
            
            if data_to_insert:
                cursor.executemany(insert_sql, data_to_insert)
                conn.commit()
                print(f"Successfully inserted {cursor.rowcount} records into fin_bill.")
            else:
                print("No data to insert.")

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        cursor.close()

def main():
    parser = argparse.ArgumentParser(description="Import structured data into local TiDB.")
    parser.add_argument("csv_path", type=str, help="Path to the financial bill CSV file.")
    
    args = parser.parse_args()
    
    conn = get_local_tidb_connection()
    if conn:
        import_fin_bill_csv(args.csv_path, conn)
        conn.close()
        print("Local TiDB connection closed.")

if __name__ == "__main__":
    main()
