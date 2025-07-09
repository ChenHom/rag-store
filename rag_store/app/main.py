from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import shutil
import tempfile
import asyncio
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import openai
from openai import OpenAI
import mysql.connector
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = None
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# --- Request/Response Models ---
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

class UploadResponse(BaseModel):
    message: str
    filename: str
    file_path: str

# --- FastAPI App ---
app = FastAPI(
    title="RAG Store API",
    description="API for document upload and RAG-based querying",
    version="0.1.0",
)

# --- CORS Middleware ---
# 取得外部 IP 設定
EXTERNAL_IP = os.getenv("EXTERNAL_IP")
EXTERNAL_FRONTEND_PORT = os.getenv("EXTERNAL_FRONTEND_PORT", "8001")

# 允許的來源包含本機、外部 IP 和 ngrok
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    # ngrok 支援 - 允許所有 ngrok 子域名
    "https://*.ngrok-free.app",
    "https://6f78fcf20cfe.ngrok-free.app",
]

# 如果設定了外部 IP，則添加到允許的來源
if EXTERNAL_IP:
    allowed_origins.extend([
        f"http://{EXTERNAL_IP}:{EXTERNAL_FRONTEND_PORT}",
        f"http://{EXTERNAL_IP}:8000",
        f"http://{EXTERNAL_IP}:8001",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
UPLOAD_DIR = Path("raw")
UPLOAD_DIR.mkdir(exist_ok=True)

# OpenAI Configuration
openai_client = None
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# TiDB Cloud Configuration
TIDB_HOST = os.getenv("TIDB_HOST")
TIDB_USER = os.getenv("TIDB_USER")
TIDB_PASSWORD = os.getenv("TIDB_PASSWORD")
TIDB_DB = "rag"

# Local TiDB Configuration
LOCAL_TIDB_HOST = os.getenv("LOCAL_TIDB_HOST", "127.0.0.1")
LOCAL_TIDB_PORT = int(os.getenv("LOCAL_TIDB_PORT", 4000))
LOCAL_TIDB_USER = os.getenv("LOCAL_TIDB_USER", "root")
LOCAL_TIDB_PASSWORD = os.getenv("LOCAL_TIDB_PASSWORD", "")
LOCAL_TIDB_DB = os.getenv("LOCAL_TIDB_DB", "local_db")

# Text processing configuration
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# --- Endpoints ---

# --- Helper Functions ---

def get_tidb_cloud_connection():
    """建立 TiDB Cloud 連線"""
    try:
        if not all([TIDB_HOST, TIDB_USER, TIDB_PASSWORD]):
            return None
        conn = mysql.connector.connect(
            host=TIDB_HOST,
            user=TIDB_USER,
            password=TIDB_PASSWORD,
            database=TIDB_DB,
            ssl_disabled=False,
            use_unicode=True
        )
        return conn
    except Exception as e:
        print(f"TiDB Cloud connection error: {e}")
        return None

def get_local_tidb_connection():
    """建立本機 TiDB 連線"""
    try:
        conn = mysql.connector.connect(
            host=LOCAL_TIDB_HOST,
            port=LOCAL_TIDB_PORT,
            user=LOCAL_TIDB_USER,
            password=LOCAL_TIDB_PASSWORD,
            database=LOCAL_TIDB_DB
        )
        return conn
    except Exception as e:
        print(f"Local TiDB connection error: {e}")
        return None

async def get_embedding(text: str) -> Optional[List[float]]:
    """使用 OpenAI API 產生文字的 embedding"""
    try:
        if not openai_client:
            return None
        response = openai_client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

async def vector_search(query_text: str, limit: int = 4) -> List[Dict[str, Any]]:
    """在 TiDB Cloud 中執行向量搜尋"""
    try:
        # 產生查詢向量
        query_embedding = await get_embedding(query_text)
        if not query_embedding:
            return []

        conn = get_tidb_cloud_connection()
        if not conn:
            # Fallback to text search if no vector db
            return []

        cursor = conn.cursor(dictionary=True)

        # 向量相似度搜尋 SQL - 使用 JSON_EXTRACT 從 JSON 字串中提取向量
        search_sql = """
        SELECT doc_id, chunk,
               VEC_COSINE_DISTANCE(CAST(vec AS VECTOR(1536)), CAST(%s AS VECTOR(1536))) AS distance
        FROM embeddings
        ORDER BY distance ASC
        LIMIT %s
        """

        # 將 embedding 轉換為 JSON 字串格式
        embedding_json = "[" + ",".join(map(str, query_embedding)) + "]"

        cursor.execute(search_sql, (embedding_json, limit))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results

    except Exception as e:
        print(f"Vector search error: {e}")
        return []

async def generate_rag_response(query: str, contexts: List[Dict[str, Any]]) -> str:
    """使用 OpenAI GPT 產生 RAG 回應"""
    try:
        if not openai_client or not contexts:
            return f"無法回答問題「{query}」，因為缺少相關文檔或 API 設定。"

        # 建構 context
        context_text = "\n\n".join([ctx["chunk"] for ctx in contexts])

        prompt = f"""根據以下文檔內容回答問題。如果文檔中沒有相關資訊，請說明無法找到相關資訊。

文檔內容：
{context_text}

問題：{query}

回答："""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個有用的助手，會根據提供的文檔內容回答問題。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"GPT response error: {e}")
        return f"生成回應時發生錯誤：{str(e)}"

async def process_uploaded_file(file_path: Path) -> bool:
    """處理上傳的檔案：OCR -> 分塊 -> 向量化 -> 儲存"""
    try:
        # Step 1: OCR 提取
        ocr_output_dir = Path("ocr_txt")
        ocr_output_dir.mkdir(exist_ok=True)

        # 執行 OCR 腳本
        cmd = ["python", "scripts/ocr_extract.py", str(file_path), "--output-dir", str(ocr_output_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

        if result.returncode != 0:
            print(f"OCR failed: {result.stderr}")
            return False

        # Step 2: 找到提取的文字檔案
        txt_filename = file_path.stem + ".txt"
        txt_path = ocr_output_dir / txt_filename

        if not txt_path.exists():
            # 嘗試 OCR 後綴
            txt_filename = file_path.stem + "_ocr.txt"
            txt_path = ocr_output_dir / txt_filename

        if not txt_path.exists():
            print(f"OCR output not found: {txt_path}")
            return False

        # Step 3: 讀取文字並分塊
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = text_splitter.split_text(content)

        # Step 4: 向量化並儲存到 TiDB Cloud
        conn = get_tidb_cloud_connection()
        if not conn:
            print("Cannot connect to TiDB Cloud")
            return False

        cursor = conn.cursor()
        doc_id = file_path.stem

        for chunk_text in chunks:
            embedding = await get_embedding(chunk_text)
            if embedding:
                # 將 embedding 轉換為 JSON 字串格式
                embedding_json = "[" + ",".join(map(str, embedding)) + "]"
                insert_sql = "INSERT INTO embeddings (doc_id, chunk, vec) VALUES (%s, %s, CAST(%s AS VECTOR(1536)))"
                cursor.execute(insert_sql, (doc_id, chunk_text, embedding_json))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"Successfully processed {file_path.name}: {len(chunks)} chunks")
        return True

    except Exception as e:
        print(f"File processing error: {e}")
        return False

@app.get("/")
def read_root():
    return {"message": "Welcome to RAG Store API", "version": "0.1.0"}

@app.get("/health")
def health_check():
    """健康檢查端點，檢查所有組件狀態"""
    health_status = {"status": "ok", "components": {}}

    # 檢查 OpenAI API
    health_status["components"]["openai"] = "configured" if openai_client else "not_configured"

    # 檢查 TiDB Cloud 連線
    try:
        conn = get_tidb_cloud_connection()
        if conn:
            conn.close()
            health_status["components"]["tidb_cloud"] = "connected"
        else:
            health_status["components"]["tidb_cloud"] = "not_connected"
    except:
        health_status["components"]["tidb_cloud"] = "error"

    # 檢查本機 TiDB 連線
    try:
        conn = get_local_tidb_connection()
        if conn:
            conn.close()
            health_status["components"]["local_tidb"] = "connected"
        else:
            health_status["components"]["local_tidb"] = "not_connected"
    except:
        health_status["components"]["local_tidb"] = "error"

    health_status["message"] = "RAG Store API is running"
    return health_status

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file for processing and storage.
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Check file extension
        allowed_extensions = {'.pdf', '.txt', '.docx', '.png', '.jpg', '.jpeg'}
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_extension} not supported. Allowed: {', '.join(allowed_extensions)}"
            )

        # Save file to upload directory
        file_path = UPLOAD_DIR / file.filename

        # Handle duplicate filenames
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            file_path = UPLOAD_DIR / f"{stem}_{counter}{suffix}"
            counter += 1

        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process the file asynchronously
        processing_success = await process_uploaded_file(file_path)

        message = "File uploaded successfully"
        if processing_success:
            message += " and processed for RAG queries"
        else:
            message += " but processing failed (check logs)"

        return UploadResponse(
            message=message,
            filename=file.filename,
            file_path=str(file_path)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Process a query using RAG (Retrieval-Augmented Generation).
    """
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Step 1: 向量搜尋相關文檔
        search_results = await vector_search(query, limit=4)

        # Step 2: 準備來源資訊
        sources = []
        for result in search_results:
            sources.append({
                "page_content": result["chunk"],
                "metadata": {
                    "doc_id": result["doc_id"],
                    "distance": float(result["distance"])
                }
            })

        # Step 3: 生成回應
        answer = await generate_rag_response(query, search_results)

        return QueryResponse(
            answer=answer,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# --- Additional utility endpoints ---

@app.get("/files")
async def list_files():
    """List uploaded files."""
    try:
        files = []
        if UPLOAD_DIR.exists():
            for file_path in UPLOAD_DIR.iterdir():
                if file_path.is_file():
                    files.append({
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "path": str(file_path)
                    })
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")