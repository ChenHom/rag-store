'use client';

import { useState, DragEvent } from 'react';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');
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
    setMessage('Uploading...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL_CLIENT || '';

// ...

      const response = await fetch(`${API_BASE_URL}/api/upload`, { // We'll create this API route next
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }
      
      setMessage(`Success! File '${data.filename}' uploaded.`);
      setFile(null);
    } catch (error) {
      setMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 border rounded-lg shadow-lg">
      <h1 className="text-2xl font-bold text-center mb-4">Upload Document</h1>
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
          <p>Selected file: {file.name}</p>
        ) : (
          <p>Drag & drop a file here, or click to select</p>
        )}
      </div>
      <button
        onClick={handleSubmit}
        disabled={!file || isUploading}
        className="w-full btn btn-primary mt-4"
      >
        {isUploading ? 'Uploading...' : 'Upload'}
      </button>
      {message && <p className="mt-4 text-center">{message}</p>}
    </div>
  );
}
