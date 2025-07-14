#!/usr/bin/env python3
"""
Test script for RAG Store API endpoints
"""
import requests
import time
import subprocess
import sys
import json

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    try:
        print("Testing RAG Store API...")
        
        # Test health endpoint
        print("\n1. Testing /health endpoint:")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test root endpoint
        print("\n2. Testing / endpoint:")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test query endpoint
        print("\n3. Testing /api/query endpoint:")
        query_data = {"query": "What is artificial intelligence?"}
        response = requests.post(f"{base_url}/api/query", json=query_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Answer: {data['answer'][:150]}...")
            print(f"   Sources count: {len(data['sources'])}")
        else:
            print(f"   Error: {response.text}")
        
        # Test files endpoint
        print("\n4. Testing /api/files endpoint:")
        response = requests.get(f"{base_url}/api/files", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        print("\n✅ All API tests completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to the server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)