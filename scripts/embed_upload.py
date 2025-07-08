import os
import openai
import mysql.connector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv('/home/hom/services/rag-store/.env')

# --- 設定 ---
# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
EMBEDDING_MODEL = "text-embedding-3-small"

# TiDB Cloud
TIDB_HOST = os.getenv("TIDB_HOST")
TIDB_USER = os.getenv("TIDB_USER")
TIDB_PASSWORD = os.getenv("TIDB_PASSWORD")
TIDB_DB = "rag"

# 來源與 Chunk 設定
SOURCE_DIR = "/home/hom/services/rag-store/ocr_txt"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

def get_tidb_connection():
    """建立並返回 TiDB 連線"""
    try:
        conn = mysql.connector.connect(
            host=TIDB_HOST,
            user=TIDB_USER,
            password=TIDB_PASSWORD,
            database=TIDB_DB,
            # 建議為 TiDB Cloud 加上 SSL 選項
            # ssl_ca='path/to/ca.pem',
            # ssl_verify_cert=True
        )
        print("Successfully connected to TiDB Cloud.")
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to TiDB: {err}")
        return None

def get_embedding(text, model=EMBEDDING_MODEL):
    """使用 OpenAI API 產生文字的 embedding"""
    try:
        response = openai.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def process_and_upload_files():
    """處理所有文字檔案，產生 embeddings 並上傳到 TiDB"""
    conn = get_tidb_connection()
    if not conn:
        return
        
    cursor = conn.cursor()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    for filename in os.listdir(SOURCE_DIR):
        if filename.endswith(".txt"):
            file_path = os.path.join(SOURCE_DIR, filename)
            doc_id = os.path.splitext(filename)[0] # 使用檔名作為 doc_id
            
            print(f"Processing document: {doc_id}")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            chunks = text_splitter.split_text(content)
            
            for i, chunk_text in enumerate(chunks):
                print(f"  - Generating embedding for chunk {i+1}/{len(chunks)}...")
                
                # 產生 embedding
                vec = get_embedding(chunk_text)
                
                if vec:
                    # 插入資料庫
                    sql = "INSERT INTO embeddings (doc_id, chunk, vec) VALUES (%s, %s, %s)"
                    val = (doc_id, chunk_text, str(vec)) # 將向量轉為字串儲存
                    try:
                        cursor.execute(sql, val)
                    except mysql.connector.Error as err:
                        print(f"  - Database insert failed: {err}")

    # 提交所有變更
    try:
        conn.commit()
        print("\nAll changes have been committed to the database.")
    except mysql.connector.Error as err:
        print(f"Database commit failed: {err}")
        conn.rollback()

    cursor.close()
    conn.close()
    print("Database connection closed.")

def main():
    if not all([OPENAI_API_KEY, TIDB_HOST, TIDB_USER, TIDB_PASSWORD]):
        print("Error: Missing required environment variables in .env file.")
        print("Please set OPENAI_API_KEY, TIDB_HOST, TIDB_USER, and TIDB_PASSWORD.")
        return
        
    process_and_upload_files()

if __name__ == "__main__":
    main()
