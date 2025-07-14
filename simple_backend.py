#!/usr/bin/env python3
"""
簡化版後端用於測試 nginx 配置
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 創建 FastAPI 應用
app = FastAPI(title="RAG Store Test API")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: list

@app.get("/")
def read_root():
    return {"message": "RAG Store API is running", "status": "ok"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "components": {
            "api": "ok",
            "database": "simulated",
            "embedding": "simulated"
        }
    }

@app.post("/api/query")
def query_rag(request: QueryRequest):
    """簡化的查詢端點"""
    return QueryResponse(
        answer=f"這是對查詢「{request.query}」的測試回應。nginx 配置正常運作！",
        sources=[]
    )

@app.post("/api/upload")
def upload_file():
    """簡化的上傳端點"""
    return {
        "message": "檔案上傳功能正常",
        "filename": "test.txt",
        "file_path": "/test/path"
    }

@app.get("/api/files")
def list_files():
    """簡化的檔案列表端點"""
    return {
        "files": [
            {"filename": "test1.txt", "size": 1024},
            {"filename": "test2.pdf", "size": 2048}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
