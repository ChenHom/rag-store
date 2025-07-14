#!/usr/bin/env python3
"""
測試 RAG Store API 的腳本
"""
import requests
import json
import sys
import os
from pathlib import Path

API_BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """測試健康檢查端點"""
    print("🔍 測試健康檢查...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 健康檢查成功")
            print(f"   狀態: {health_data.get('status')}")
            print(f"   組件狀態:")
            for component, status in health_data.get('components', {}).items():
                print(f"     {component}: {status}")
            return True
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康檢查錯誤: {e}")
        return False

def test_upload_file(file_path: str):
    """測試文件上傳"""
    print(f"📤 測試文件上傳: {file_path}")
    try:
        if not Path(file_path).exists():
            print(f"❌ 文件不存在: {file_path}")
            return False

        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_BASE_URL}/api/upload", files=files)

        if response.status_code == 200:
            upload_data = response.json()
            print(f"✅ 文件上傳成功")
            print(f"   訊息: {upload_data.get('message')}")
            print(f"   文件名: {upload_data.get('filename')}")
            return True
        else:
            print(f"❌ 文件上傳失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 文件上傳錯誤: {e}")
        return False

def test_query(query: str):
    """測試 RAG 查詢"""
    print(f"🤖 測試 RAG 查詢: {query}")
    try:
        payload = {"query": query}
        response = requests.post(f"{API_BASE_URL}/api/query", json=payload)

        if response.status_code == 200:
            query_data = response.json()
            print(f"✅ RAG 查詢成功")
            print(f"   回答: {query_data.get('answer')}")
            print(f"   來源數量: {len(query_data.get('sources', []))}")
            for i, source in enumerate(query_data.get('sources', [])[:2]):  # 只顯示前2個來源
                print(f"   來源 {i+1}: {source.get('metadata', {}).get('doc_id', 'unknown')}")
            return True
        else:
            print(f"❌ RAG 查詢失敗: {response.status_code}")
            print(f"   錯誤: {response.text}")
            return False
    except Exception as e:
        print(f"❌ RAG 查詢錯誤: {e}")
        return False

def test_list_files():
    """測試列出文件"""
    print("📁 測試列出文件...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/files")
        if response.status_code == 200:
            files_data = response.json()
            files = files_data.get('files', [])
            print(f"✅ 列出文件成功，共 {len(files)} 個文件")
            for file_info in files[:3]:  # 只顯示前3個文件
                print(f"   - {file_info.get('filename')} ({file_info.get('size')} bytes)")
            return True
        else:
            print(f"❌ 列出文件失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 列出文件錯誤: {e}")
        return False

def main():
    """主要測試函數"""
    print("🚀 開始測試 RAG Store API")
    print("=" * 50)

    # 測試健康檢查
    if not test_health():
        print("❌ 服務器似乎未運行，請確保後端服務已啟動")
        sys.exit(1)

    print("\n" + "-" * 30 + "\n")

    # 測試列出文件
    test_list_files()

    print("\n" + "-" * 30 + "\n")

    # 測試文件上傳（如果存在測試文件）
    test_file = "test_doc.txt"
    if Path(test_file).exists():
        test_upload_file(test_file)
    else:
        print(f"⚠️  測試文件 {test_file} 不存在，跳過上傳測試")

    print("\n" + "-" * 30 + "\n")

    # 測試查詢
    test_queries = [
        "這份文件說了什麼？",
        "主要內容是什麼？",
        "有什麼重要的資訊？"
    ]

    for query in test_queries:
        test_query(query)
        print()

    print("🎉 測試完成！")

if __name__ == "__main__":
    main()
