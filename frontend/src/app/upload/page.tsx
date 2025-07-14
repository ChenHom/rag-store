'use client';

import { useState, DragEvent } from 'react';

interface UploadResult {
  message: string;
  filename: string;
  file_path: string;
  document_id?: number;
  classification?: {
    category: string;
    confidence: number;
    extracted_data: {
      amount?: number;
      date?: string;
      person_name?: string;
      company?: string;
      keywords?: string[];
    };
    suggested_tags: string[];
    reasoning: string;
  };
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileChange = (files: FileList | null) => {
    if (files && files[0]) {
      setFile(files[0]);
      setMessage('');
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFileChange(e.dataTransfer.files);
  };

  const handleSubmit = async () => {
    if (!file || isUploading) return;

    setIsUploading(true);
    setMessage('正在上傳並分析文件...');
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }
      
      setMessage('上傳成功！');
      setUploadResult(data);
      setFile(null);
    } catch (error) {
      setMessage(`錯誤: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setUploadResult(null);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-10 p-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 上傳區域 */}
        <div className="border rounded-lg shadow-lg p-6">
          <h1 className="text-2xl font-bold text-center mb-4">上傳文件</h1>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-md p-10 text-center cursor-pointer
                        ${isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input
              id="file-input"
              type="file"
              className="hidden"
              onChange={(e) => handleFileChange(e.target.files)}
            />
            {file ? (
              <div>
                <p className="font-medium">選擇的文件:</p>
                <p className="text-gray-600">{file.name}</p>
                <p className="text-sm text-gray-500 mt-1">
                  大小: {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            ) : (
              <div>
                <p className="text-gray-600">拖放文件到此處，或點擊選擇文件</p>
                <p className="text-sm text-gray-500 mt-2">
                  支援 PDF、圖片、文字檔案
                </p>
              </div>
            )}
          </div>
          <button
            onClick={handleSubmit}
            disabled={!file || isUploading}
            className="w-full btn btn-primary mt-4 disabled:opacity-50"
          >
            {isUploading ? '處理中...' : '上傳並分析'}
          </button>
          {message && (
            <div className={`mt-4 p-3 rounded ${
              message.includes('錯誤') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
            }`}>
              {message}
            </div>
          )}
        </div>

        {/* 分析結果區域 */}
        {uploadResult && uploadResult.classification && (
          <div className="border rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4">分析結果</h2>
            
            {/* 分類結果 */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold mb-2">文件分類</h3>
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{uploadResult.classification.category}</span>
                  <span className="text-sm text-gray-600">
                    信心度: {(uploadResult.classification.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* 提取的數據 */}
            {uploadResult.classification.extracted_data && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold mb-2">提取資訊</h3>
                <div className="bg-gray-50 p-3 rounded-lg space-y-2">
                  {uploadResult.classification.extracted_data.amount && (
                    <div className="flex justify-between">
                      <span>金額:</span>
                      <span className="font-medium">
                        NT$ {uploadResult.classification.extracted_data.amount.toLocaleString()}
                      </span>
                    </div>
                  )}
                  {uploadResult.classification.extracted_data.date && (
                    <div className="flex justify-between">
                      <span>日期:</span>
                      <span className="font-medium">{uploadResult.classification.extracted_data.date}</span>
                    </div>
                  )}
                  {uploadResult.classification.extracted_data.company && (
                    <div className="flex justify-between">
                      <span>公司:</span>
                      <span className="font-medium">{uploadResult.classification.extracted_data.company}</span>
                    </div>
                  )}
                  {uploadResult.classification.extracted_data.person_name && (
                    <div className="flex justify-between">
                      <span>姓名:</span>
                      <span className="font-medium">{uploadResult.classification.extracted_data.person_name}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 建議標籤 */}
            {uploadResult.classification.suggested_tags && uploadResult.classification.suggested_tags.length > 0 && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold mb-2">建議標籤</h3>
                <div className="flex flex-wrap gap-2">
                  {uploadResult.classification.suggested_tags.map((tag, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 關鍵字 */}
            {uploadResult.classification.extracted_data.keywords && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold mb-2">關鍵字</h3>
                <div className="flex flex-wrap gap-2">
                  {uploadResult.classification.extracted_data.keywords.map((keyword, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-sm"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 分析說明 */}
            <div>
              <h3 className="text-lg font-semibold mb-2">分析說明</h3>
              <p className="text-gray-600 text-sm">{uploadResult.classification.reasoning}</p>
            </div>

            {/* 操作按鈕 */}
            <div className="mt-6 pt-4 border-t">
              <a
                href="/classification"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                查看所有文件
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
