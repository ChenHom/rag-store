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
from openai import OpenAI
import mysql.connector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import date, datetime, timedelta

# Load environment variables
load_dotenv()

# --- OpenAI Configuration ---
openai_client = None
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    print("Warning: OPENAI_API_KEY not found in environment variables")

# --- Request/Response Models ---
class QueryRequest(BaseModel):
    query: str
    # 多維度搜尋參數
    category: Optional[str] = None  # 分類篩選
    tags: Optional[List[str]] = None  # 標籤篩選
    date_from: Optional[str] = None  # 日期範圍篩選（開始）
    date_to: Optional[str] = None  # 日期範圍篩選（結束）
    family_member: Optional[str] = None  # 家庭成員篩選
    amount_min: Optional[float] = None  # 最小金額
    amount_max: Optional[float] = None  # 最大金額
    search_mode: Optional[str] = "hybrid"  # 搜尋模式：semantic, filter, hybrid

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

class UploadResponse(BaseModel):
    message: str
    filename: str
    file_path: str
    document_id: Optional[int] = None
    classification: Optional[Dict[str, Any]] = None

# 時間序列相關模型
class TimeSeriesRequest(BaseModel):
    series_type: str
    family_member_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period_days: Optional[int] = 90

class TimeSeriesDataPoint(BaseModel):
    date: str
    value: float
    family_member: Optional[str] = None
    confidence: Optional[float] = 1.0
    notes: Optional[str] = None

class TimeSeriesResponse(BaseModel):
    series_name: str
    data_points: List[TimeSeriesDataPoint]
    statistics: Dict[str, Any]
    trend_analysis: Dict[str, Any]

class TrendAnalysisRequest(BaseModel):
    series_type: str
    family_member_id: Optional[int] = None
    period_days: Optional[int] = 30

class AlertResponse(BaseModel):
    alert_id: int
    alert_name: str
    series_name: str
    family_member: Optional[str]
    current_value: float
    message: str
    condition_type: str
    triggered_date: str

class DocumentMetadata(BaseModel):
    id: int
    filename: str
    category: Optional[str] = None
    tags: List[str] = []
    document_date: Optional[str] = None
    extracted_amount: Optional[float] = None
    confidence_score: Optional[float] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    document_count: int = 0

class TagResponse(BaseModel):
    id: int
    name: str
    color: Optional[str] = None
    document_count: int = 0

# --- FastAPI App ---
app = FastAPI(
    title="RAG Store API",
    description="API for document upload and RAG-based querying",
    version="0.1.0",
)

# --- CORS Middleware ---
# 內網環境配置
allowed_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:80",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:80",
]

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

# 匯入分類系統和時間序列分析器
from ..classification_system import DocumentClassifier
from ..time_series_analyzer import TimeSeriesAnalyzer, process_document_for_time_series

# 初始化分類器
document_classifier = DocumentClassifier()

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

async def multi_dimensional_search(
    query_text: str, 
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    family_member: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    search_mode: str = "hybrid",
    limit: int = 4
) -> List[Dict[str, Any]]:
    """
    多維度搜尋功能，支援語義搜尋與條件過濾的組合
    
    Args:
        query_text: 搜尋查詢文字
        category: 文件分類過濾
        tags: 標籤過濾
        date_from/date_to: 日期範圍過濾
        family_member: 家庭成員過濾
        amount_min/amount_max: 金額範圍過濾
        search_mode: 搜尋模式 (semantic, filter, hybrid)
        limit: 結果數量限制
    
    Returns:
        搜尋結果列表
    """
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        
        # 檢查 embeddings 表是否有 document_id 欄位
        cursor.execute("DESCRIBE embeddings")
        columns = [col[0] for col in cursor.fetchall()]
        has_document_id = 'document_id' in columns
        
        # 建構基本查詢
        if search_mode == "semantic":
            # 純語義搜尋模式
            return await vector_search(query_text, limit)
            
        elif search_mode == "filter":
            # 純過濾模式（不使用向量搜尋）
            if has_document_id:
                # 使用 document_id 連接（新版 schema）
                base_sql = """
                SELECT e.doc_id, e.chunk, 0.0 as distance,
                       d.filename, c.name as category, d.document_date, 
                       d.extracted_amount, fm.name as family_member
                FROM embeddings e
                JOIN documents d ON e.document_id = d.id
                LEFT JOIN categories c ON d.category_id = c.id
                LEFT JOIN family_members fm ON d.family_member_id = fm.id
                """
            else:
                # 使用 doc_id 連接（基本 schema）
                base_sql = """
                SELECT e.doc_id, e.chunk, 0.0 as distance
                FROM embeddings e
                """
            
        else:  # hybrid mode
            # 混合模式：結合語義搜尋和過濾條件
            query_embedding = await get_embedding(query_text)
            if not query_embedding:
                # 如果無法生成向量，回退到純過濾模式
                search_mode = "filter"
                if has_document_id:
                    base_sql = """
                    SELECT e.doc_id, e.chunk, 0.0 as distance,
                           d.filename, c.name as category, d.document_date, 
                           d.extracted_amount, fm.name as family_member
                    FROM embeddings e
                    JOIN documents d ON e.document_id = d.id
                    LEFT JOIN categories c ON d.category_id = c.id
                    LEFT JOIN family_members fm ON d.family_member_id = fm.id
                    """
                else:
                    base_sql = """
                    SELECT e.doc_id, e.chunk, 0.0 as distance
                    FROM embeddings e
                    """
            else:
                embedding_json = "[" + ",".join(map(str, query_embedding)) + "]"
                if has_document_id:
                    base_sql = """
                    SELECT e.doc_id, e.chunk,
                           VEC_COSINE_DISTANCE(CAST(e.vec AS VECTOR(1536)), CAST(%s AS VECTOR(1536))) AS distance,
                           d.filename, c.name as category, d.document_date, 
                           d.extracted_amount, fm.name as family_member
                    FROM embeddings e
                    JOIN documents d ON e.document_id = d.id
                    LEFT JOIN categories c ON d.category_id = c.id
                    LEFT JOIN family_members fm ON d.family_member_id = fm.id
                    """
                else:
                    base_sql = """
                    SELECT e.doc_id, e.chunk,
                           VEC_COSINE_DISTANCE(CAST(e.vec AS VECTOR(1536)), CAST(%s AS VECTOR(1536))) AS distance
                    FROM embeddings e
                    """
        
        # 建構過濾條件（只有在有 document_id 時才能使用）
        conditions = []
        params = []
        
        # 添加向量搜尋參數（如果使用混合模式）
        if search_mode == "hybrid" and query_embedding:
            params.append(embedding_json)
        
        # 只有在有 document_id 且有相關表格連接時才能使用以下過濾條件
        if has_document_id:
            # 添加標籤過濾
            if tags:
                tag_join = """
                JOIN document_tags dt ON d.id = dt.document_id
                JOIN tags t ON dt.tag_id = t.id
                """
                base_sql = base_sql.replace("FROM embeddings e", f"FROM embeddings e {tag_join}")
                tag_placeholders = ','.join(['%s'] * len(tags))
                conditions.append(f"t.name IN ({tag_placeholders})")
                params.extend(tags)
            
            # 添加其他過濾條件
            if category:
                conditions.append("c.name = %s")
                params.append(category)
            
            if family_member:
                conditions.append("fm.name = %s")
                params.append(family_member)
            
            if date_from:
                conditions.append("d.document_date >= %s")
                params.append(date_from)
            
            if date_to:
                conditions.append("d.document_date <= %s")
                params.append(date_to)
            
            if amount_min is not None:
                conditions.append("d.extracted_amount >= %s")
                params.append(amount_min)
            
            if amount_max is not None:
                conditions.append("d.extracted_amount <= %s")
                params.append(amount_max)
        
        # 組合條件
        if conditions:
            base_sql += " WHERE " + " AND ".join(conditions)
        
        # 排序和限制
        if search_mode == "hybrid" and query_embedding:
            base_sql += " ORDER BY distance ASC"
        elif has_document_id:
            base_sql += " ORDER BY d.created_at DESC"
        else:
            base_sql += " ORDER BY e.id DESC"
        
        base_sql += " LIMIT %s"
        params.append(limit)
        
        cursor.execute(base_sql, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results
        
    except Exception as e:
        print(f"Multi-dimensional search error: {e}")
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

async def process_uploaded_file(file_path: Path) -> Dict[str, Any]:
    """處理上傳的檔案：OCR -> 分類 -> 分塊 -> 向量化 -> 儲存"""
    try:
        # Step 1: OCR 提取
        ocr_output_dir = Path("ocr_txt")
        ocr_output_dir.mkdir(exist_ok=True)

        # 執行 OCR 腳本
        cmd = ["python", "scripts/ocr_extract.py", str(file_path), "--output-dir", str(ocr_output_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

        if result.returncode != 0:
            print(f"OCR failed: {result.stderr}")
            return {"success": False, "error": "OCR processing failed"}

        # Step 2: 找到提取的文字檔案
        txt_filename = file_path.stem + ".txt"
        txt_path = ocr_output_dir / txt_filename

        if not txt_path.exists():
            # 嘗試 OCR 後綴
            txt_filename = file_path.stem + "_ocr.txt"
            txt_path = ocr_output_dir / txt_filename

        if not txt_path.exists():
            print(f"OCR output not found: {txt_path}")
            return {"success": False, "error": "OCR output not found"}

        # Step 3: 讀取文字內容
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Step 4: 智能分類
        print("Classifying document...")
        classification_result = document_classifier.classify_document(content)
        print(f"Classification result: {classification_result}")

        # Step 5: 儲存文件元資料
        file_stats = file_path.stat()
        document_id = document_classifier.save_document_metadata(
            filename=file_path.name,
            file_path=str(file_path),
            classification_result=classification_result,
            ocr_text=content,
            file_size=file_stats.st_size,
            mime_type=""  # 可以根據副檔名判斷
        )

        # Step 6: 文字分塊
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = text_splitter.split_text(content)

        # Step 7: 向量化並儲存到 TiDB Cloud
        conn = get_tidb_cloud_connection()
        if not conn:
            print("Cannot connect to TiDB Cloud")
            return {"success": False, "error": "Database connection failed"}

        cursor = conn.cursor()
        doc_id = file_path.stem

        for chunk_text in chunks:
            embedding = await get_embedding(chunk_text)
            if embedding:
                # 將 embedding 轉換為 JSON 字串格式
                embedding_json = "[" + ",".join(map(str, embedding)) + "]"
                insert_sql = "INSERT INTO embeddings (doc_id, chunk, vec, document_id) VALUES (%s, %s, CAST(%s AS VECTOR(1536)), %s)"
                cursor.execute(insert_sql, (doc_id, chunk_text, embedding_json, document_id))

        conn.commit()
        cursor.close()

        # Step 8: 提取時間序列數據
        print("Extracting time series data...")
        try:
            # 重新建立連接進行時間序列處理
            conn_ts = get_tidb_cloud_connection()
            if conn_ts:
                document_date = classification_result.get('extracted_date')
                if isinstance(document_date, str):
                    # 轉換字串日期為 date 對象
                    try:
                        document_date = datetime.strptime(document_date, "%Y-%m-%d").date()
                    except ValueError:
                        document_date = date.today()
                elif not document_date:
                    document_date = date.today()
                
                # 提取時間序列數據
                time_series_count = process_document_for_time_series(
                    conn_ts, 
                    document_id, 
                    content, 
                    document_date,
                    None  # family_member_id，可以從分類結果中提取
                )
                conn_ts.close()
                print(f"Extracted {time_series_count} time series data points")
            else:
                print("Cannot connect to database for time series extraction")
        except Exception as ts_error:
            print(f"Time series extraction error: {ts_error}")
            # 不影響主要處理流程，繼續執行

        conn.close()

        print(f"Successfully processed {file_path.name}: {len(chunks)} chunks")
        
        return {
            "success": True,
            "document_id": document_id,
            "classification": classification_result,
            "chunks_count": len(chunks)
        }
        return True

    except Exception as e:
        print(f"File processing error: {e}")
        return False

@app.get("/")
def read_root():
    return {"message": "Welcome to RAG Store API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "ok", "message": "RAG Store API is running"}

@app.post("/api/upload", response_model=UploadResponse)
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
        processing_result = await process_uploaded_file(file_path)

        if processing_result["success"]:
            message = "File uploaded and processed successfully"
            return UploadResponse(
                message=message,
                filename=file.filename,
                file_path=str(file_path),
                document_id=processing_result.get("document_id"),
                classification=processing_result.get("classification")
            )
        else:
            message = f"File uploaded but processing failed: {processing_result.get('error', 'Unknown error')}"
            return UploadResponse(
                message=message,
                filename=file.filename,
                file_path=str(file_path)
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    處理多維度搜尋查詢，支援語義搜尋與條件過濾
    """
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # 使用多維度搜尋功能
        search_results = await multi_dimensional_search(
            query_text=query,
            category=request.category,
            tags=request.tags,
            date_from=request.date_from,
            date_to=request.date_to,
            family_member=request.family_member,
            amount_min=request.amount_min,
            amount_max=request.amount_max,
            search_mode=request.search_mode or "hybrid",
            limit=4
        )

        # 準備來源資訊（包含更多元資料）
        sources = []
        for result in search_results:
            source_metadata = {
                "doc_id": result["doc_id"],
                "distance": float(result.get("distance", 0)),
                "filename": result.get("filename", ""),
                "category": result.get("category", ""),
                "document_date": str(result.get("document_date", "")),
                "extracted_amount": result.get("extracted_amount"),
                "family_member": result.get("family_member", "")
            }
            
            sources.append({
                "page_content": result["chunk"],
                "metadata": source_metadata
            })

        # 生成增強的回應（考慮過濾條件）
        answer = await generate_rag_response(query, search_results)
        
        # 添加搜尋統計資訊
        search_summary = f"\n\n📊 搜尋結果統計：找到 {len(search_results)} 個相關文件片段"
        if request.category:
            search_summary += f"，分類：{request.category}"
        if request.tags:
            search_summary += f"，標籤：{', '.join(request.tags)}"
        if request.date_from or request.date_to:
            date_range = f"{request.date_from or '開始'} 至 {request.date_to or '現在'}"
            search_summary += f"，日期範圍：{date_range}"
        
        answer += search_summary

        return QueryResponse(
            answer=answer,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/api/chat", response_model=QueryResponse)
async def chat_rag(request: QueryRequest):
    """
    聊天端點，功能與查詢端點相同，用於聊天介面
    """
    # 直接呼叫查詢功能，保持一致性
    return await query_rag(request)

# --- Classification and Tagging API Endpoints ---

@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories():
    """取得所有文件分類"""
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor(dictionary=True)
        sql = """
        SELECT c.*, COUNT(d.id) as document_count
        FROM categories c
        LEFT JOIN documents d ON c.id = d.category_id
        GROUP BY c.id, c.name, c.description, c.icon, c.color
        ORDER BY c.name
        """
        cursor.execute(sql)
        categories = cursor.fetchall()
        
        conn.close()
        return [CategoryResponse(**category) for category in categories]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@app.get("/api/tags", response_model=List[TagResponse])
async def get_tags():
    """取得所有標籤"""
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor(dictionary=True)
        sql = """
        SELECT t.*, COUNT(dt.document_id) as document_count
        FROM tags t
        LEFT JOIN document_tags dt ON t.id = dt.tag_id
        GROUP BY t.id, t.name, t.color
        ORDER BY document_count DESC, t.name
        """
        cursor.execute(sql)
        tags = cursor.fetchall()
        
        conn.close()
        return [TagResponse(**tag) for tag in tags]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tags: {str(e)}")

@app.get("/api/documents", response_model=List[DocumentMetadata])
async def get_documents(
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50
):
    """根據條件查詢文件"""
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor(dictionary=True)
        
        # 建構查詢條件
        conditions = []
        params = []
        
        base_sql = """
        SELECT DISTINCT d.id, d.filename, c.name as category, d.document_date, 
               d.extracted_amount, d.confidence_score
        FROM documents d
        LEFT JOIN categories c ON d.category_id = c.id
        """
        
        if tags:
            base_sql += """
            LEFT JOIN document_tags dt ON d.id = dt.document_id
            LEFT JOIN tags t ON dt.tag_id = t.id
            """
            tag_placeholders = ','.join(['%s'] * len(tags))
            conditions.append(f"t.name IN ({tag_placeholders})")
            params.extend(tags)
        
        if category:
            conditions.append("c.name = %s")
            params.append(category)
        
        if date_from:
            conditions.append("d.document_date >= %s")
            params.append(date_from)
        
        if date_to:
            conditions.append("d.document_date <= %s")
            params.append(date_to)
        
        if conditions:
            base_sql += " WHERE " + " AND ".join(conditions)
        
        base_sql += " ORDER BY d.created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(base_sql, params)
        documents = cursor.fetchall()
        
        # 為每個文件取得標籤
        for doc in documents:
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN document_tags dt ON t.id = dt.tag_id
                WHERE dt.document_id = %s
            """, (doc['id'],))
            doc['tags'] = [tag['name'] for tag in cursor.fetchall()]
        
        conn.close()
        return [DocumentMetadata(**doc) for doc in documents]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query documents: {str(e)}")

@app.get("/api/statistics")
async def get_statistics():
    """取得分類統計資訊"""
    try:
        stats = document_classifier.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# --- Additional utility endpoints ---

@app.get("/api/files")
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

@app.get("/api/search/suggestions")
async def get_search_suggestions_endpoint(q: str = ""):
    """取得搜尋建議"""
    try:
        suggestions = await get_search_suggestions(q)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search suggestions: {str(e)}")

@app.get("/api/search/filters")
async def get_search_filters():
    """取得所有可用的搜尋過濾器選項"""
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor(dictionary=True)
        
        filters = {
            "categories": [],
            "tags": [],
            "family_members": [],
            "amount_ranges": [],
            "date_ranges": []
        }
        
        # 取得所有分類
        cursor.execute("SELECT name, icon, color FROM categories ORDER BY name")
        filters["categories"] = cursor.fetchall()
        
        # 取得所有標籤
        cursor.execute("SELECT name, color FROM tags ORDER BY name")
        filters["tags"] = cursor.fetchall()
        
        # 取得所有家庭成員
        cursor.execute("SELECT name FROM family_members ORDER BY name")
        filters["family_members"] = [row["name"] for row in cursor.fetchall()]
        
        # 計算金額範圍
        cursor.execute("""
            SELECT 
                MIN(extracted_amount) as min_amount,
                MAX(extracted_amount) as max_amount,
                AVG(extracted_amount) as avg_amount
            FROM documents 
            WHERE extracted_amount IS NOT NULL
        """)
        amount_stats = cursor.fetchone()
        
        if amount_stats and amount_stats["min_amount"] is not None:
            min_amt = float(amount_stats["min_amount"])
            max_amt = float(amount_stats["max_amount"])
            avg_amt = float(amount_stats["avg_amount"])
            
            filters["amount_ranges"] = [
                {"label": f"小於 ${avg_amt/2:.0f}", "min": 0, "max": avg_amt/2},
                {"label": f"${avg_amt/2:.0f} - ${avg_amt:.0f}", "min": avg_amt/2, "max": avg_amt},
                {"label": f"${avg_amt:.0f} - ${avg_amt*2:.0f}", "min": avg_amt, "max": avg_amt*2},
                {"label": f"大於 ${avg_amt*2:.0f}", "min": avg_amt*2, "max": max_amt}
            ]
        
        # 取得日期範圍
        cursor.execute("""
            SELECT 
                DATE_FORMAT(document_date, '%Y-%m') as month,
                COUNT(*) as count
            FROM documents 
            WHERE document_date IS NOT NULL
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """)
        filters["date_ranges"] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return filters
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search filters: {str(e)}")

@app.post("/api/search/advanced")
async def advanced_search(request: QueryRequest):
    """進階搜尋端點，返回更詳細的結果"""
    try:
        # 使用多維度搜尋
        search_results = await multi_dimensional_search(
            query_text=request.query,
            category=request.category,
            tags=request.tags,
            date_from=request.date_from,
            date_to=request.date_to,
            family_member=request.family_member,
            amount_min=request.amount_min,
            amount_max=request.amount_max,
            search_mode=request.search_mode or "hybrid",
            limit=20  # 進階搜尋返回更多結果
        )
        
        # 整理結果
        results = []
        for result in search_results:
            results.append({
                "doc_id": result["doc_id"],
                "chunk": result["chunk"],
                "distance": float(result.get("distance", 0)),
                "filename": result.get("filename", ""),
                "category": result.get("category", ""),
                "document_date": str(result.get("document_date", "")),
                "extracted_amount": result.get("extracted_amount"),
                "family_member": result.get("family_member", "")
            })
        
        # 統計資訊
        stats = {
            "total_results": len(results),
            "categories_found": len(set(r["category"] for r in results if r["category"])),
            "date_range": {
                "earliest": min((r["document_date"] for r in results if r["document_date"]), default=""),
                "latest": max((r["document_date"] for r in results if r["document_date"]), default="")
            },
            "amount_range": {
                "min": min((r["extracted_amount"] for r in results if r["extracted_amount"]), default=0),
                "max": max((r["extracted_amount"] for r in results if r["extracted_amount"]), default=0)
            }
        }
        
        return {
            "results": results,
            "statistics": stats,
            "search_parameters": {
                "query": request.query,
                "category": request.category,
                "tags": request.tags,
                "date_from": request.date_from,
                "date_to": request.date_to,
                "family_member": request.family_member,
                "amount_min": request.amount_min,
                "amount_max": request.amount_max,
                "search_mode": request.search_mode
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")

# --- Time Series API Endpoints ---

@app.get("/api/timeseries/types")
async def get_time_series_types():
    """取得所有時間序列類型"""
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, description, unit, category, data_type, color, icon
            FROM time_series_types
            ORDER BY category, name
        """)
        types = cursor.fetchall()
        conn.close()
        
        return {"time_series_types": types}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get time series types: {str(e)}")

@app.post("/api/timeseries/data", response_model=TimeSeriesResponse)
async def get_time_series_data(request: TimeSeriesRequest):
    """取得時間序列數據"""
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        analyzer = TimeSeriesAnalyzer(conn)
        
        # 設定日期範圍
        end_date = date.today()
        if request.end_date:
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()
        
        start_date = end_date - timedelta(days=request.period_days or 90)
        if request.start_date:
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
        
        # 取得數據點
        data_points = analyzer.get_time_series_data(
            request.series_type,
            request.family_member_id,
            start_date,
            end_date
        )
        
        # 轉換為回應格式
        response_data_points = [
            TimeSeriesDataPoint(
                date=point.date.isoformat(),
                value=point.value,
                family_member=point.family_member,
                confidence=point.confidence,
                notes=point.notes
            )
            for point in data_points
        ]
        
        # 取得統計摘要
        statistics = analyzer.get_statistics_summary(
            request.series_type,
            request.family_member_id,
            request.period_days or 90
        )
        
        # 趨勢分析
        trend = analyzer.analyze_trend(data_points, request.period_days or 30)
        trend_analysis = {
            "trend_type": trend.trend_type,
            "slope": trend.slope,
            "correlation": trend.correlation,
            "confidence": trend.confidence,
            "change_percentage": trend.change_percentage
        }
        
        conn.close()
        
        return TimeSeriesResponse(
            series_name=request.series_type,
            data_points=response_data_points,
            statistics=statistics,
            trend_analysis=trend_analysis
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get time series data: {str(e)}")

@app.post("/api/timeseries/analysis")
async def analyze_time_series_trend(request: TrendAnalysisRequest):
    """分析時間序列趨勢"""
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        analyzer = TimeSeriesAnalyzer(conn)
        
        # 取得最近一段時間的數據
        end_date = date.today()
        start_date = end_date - timedelta(days=request.period_days or 30)
        
        data_points = analyzer.get_time_series_data(
            request.series_type,
            request.family_member_id,
            start_date,
            end_date
        )
        
        if not data_points:
            raise HTTPException(status_code=404, detail="No data points found for analysis")
        
        # 進行趨勢分析
        trend = analyzer.analyze_trend(data_points, request.period_days or 30)
        
        # 檢查警報
        alerts = analyzer.check_alerts(request.series_type, request.family_member_id)
        
        conn.close()
        
        return {
            "series_type": request.series_type,
            "family_member_id": request.family_member_id,
            "period_days": request.period_days or 30,
            "data_points_count": len(data_points),
            "trend_analysis": {
                "trend_type": trend.trend_type,
                "slope": trend.slope,
                "correlation": trend.correlation,
                "confidence": trend.confidence,
                "change_percentage": trend.change_percentage
            },
            "alerts": alerts,
            "latest_value": data_points[-1].value if data_points else None,
            "latest_date": data_points[-1].date.isoformat() if data_points else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze trend: {str(e)}")

@app.get("/api/timeseries/alerts")
async def get_active_alerts():
    """取得所有活躍的警報"""
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor(dictionary=True)
        
        # 取得最近7天的警報記錄
        sql = """
        SELECT tal.*, ta.alert_name, tst.name as series_name, fm.name as family_member_name
        FROM time_series_alert_logs tal
        JOIN time_series_alerts ta ON tal.alert_id = ta.id
        JOIN time_series_types tst ON ta.series_type_id = tst.id
        LEFT JOIN family_members fm ON ta.family_member_id = fm.id
        WHERE tal.triggered_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        AND tal.is_read = FALSE
        ORDER BY tal.triggered_date DESC, tal.created_at DESC
        LIMIT 50
        """
        
        cursor.execute(sql)
        alert_logs = cursor.fetchall()
        
        alerts = []
        for log in alert_logs:
            alerts.append(AlertResponse(
                alert_id=log['alert_id'],
                alert_name=log['alert_name'],
                series_name=log['series_name'],
                family_member=log['family_member_name'],
                current_value=float(log['current_value']),
                message=log['message'],
                condition_type="", # 需要額外查詢
                triggered_date=log['triggered_date'].isoformat()
            ))
        
        conn.close()
        
        return {"alerts": alerts, "count": len(alerts)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@app.post("/api/timeseries/alerts/{alert_id}/read")
async def mark_alert_as_read(alert_id: int):
    """標記警報為已讀"""
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE time_series_alert_logs 
            SET is_read = TRUE 
            WHERE alert_id = %s
        """, (alert_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": "Alert marked as read", "alert_id": alert_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark alert as read: {str(e)}")

@app.get("/api/timeseries/dashboard")
async def get_time_series_dashboard():
    """取得時間序列儀表板數據"""
    try:
        conn = get_tidb_cloud_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        analyzer = TimeSeriesAnalyzer(conn)
        
        # 取得主要統計數據
        dashboard_data = {
            "summary": {},
            "recent_trends": [],
            "alerts_count": 0,
            "categories": {}
        }
        
        # 取得各類別的最新數據和趨勢
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name, category, color, icon FROM time_series_types")
        series_types = cursor.fetchall()
        
        for series_type in series_types[:10]:  # 限制數量避免過慢
            series_name = series_type['name']
            category = series_type['category']
            
            # 取得統計摘要
            stats = analyzer.get_statistics_summary(series_name, period_days=30)
            if stats:
                if category not in dashboard_data["categories"]:
                    dashboard_data["categories"][category] = []
                
                dashboard_data["categories"][category].append({
                    "name": series_name,
                    "latest_value": stats.get('latest_value'),
                    "latest_date": stats.get('latest_date'),
                    "trend": stats.get('trend_analysis', {}).get('trend_type'),
                    "change_percentage": stats.get('trend_analysis', {}).get('change_percentage'),
                    "color": series_type['color'],
                    "icon": series_type['icon']
                })
        
        # 計算未讀警報數量
        cursor.execute("""
            SELECT COUNT(*) as alert_count 
            FROM time_series_alert_logs 
            WHERE is_read = FALSE 
            AND triggered_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """)
        alert_result = cursor.fetchone()
        dashboard_data["alerts_count"] = alert_result['alert_count'] if alert_result else 0
        
        conn.close()
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")