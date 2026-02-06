import React, { useState, useCallback } from 'react';
import { Upload, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadFile } from '../services/api';

/**
 * Drag-and-drop file upload component with progress indicator.
 * Supports PDF, audio, and video file types.
 */
export default function FileUpload({ onUploadComplete }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(e.type === 'dragenter' || e.type === 'dragover');
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) handleUpload(files[0]);
  }, []);

  const handleUpload = async (file) => {
    const allowedTypes = ['pdf', 'mp3', 'wav', 'mp4', 'webm', 'm4a'];
    const ext = file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(ext)) {
      setError(`Unsupported file type. Allowed: ${allowedTypes.join(', ')}`);
      setStatus('error');
      return;
    }

    setStatus('uploading');
    setError(null);
    setUploadProgress(0);

    try {
      const result = await uploadFile(file, setUploadProgress);
      setStatus('success');
      onUploadComplete(result);
    } catch (err) {
      setStatus('error');
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    }
  };

  const resetUpload = () => {
    setStatus('idle');
    setError(null);
    setUploadProgress(0);
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${status === 'error' ? 'border-red-300 bg-red-50' : ''}
          ${status === 'success' ? 'border-green-300 bg-green-50' : ''}
        `}
      >
        {status === 'idle' && (
          <>
            <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium text-gray-700">
              Drop your file here or click to upload
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Supports PDF, MP3, WAV, MP4, WebM, M4A (max 100MB)
            </p>
            <input
              type="file"
              accept=".pdf,.mp3,.wav,.mp4,.webm,.m4a"
              onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0])}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
          </>
        )}

        {status === 'uploading' && (
          <>
            <Loader2 className="w-12 h-12 mx-auto mb-4 text-blue-500 animate-spin" />
            <p className="text-lg font-medium text-gray-700">
              Uploading & Processing...
            </p>
            <p className="text-sm text-gray-500 mt-1">
              This may take a moment for audio/video files
            </p>
            <div className="w-full max-w-xs mx-auto bg-gray-200 rounded-full h-2 mt-4">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-2">{uploadProgress}%</p>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
            <p className="text-lg font-medium text-green-700">Upload Complete!</p>
            <p className="text-sm text-gray-500 mt-1">
              Your file has been processed successfully
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
            <p className="text-lg font-medium text-red-700">{error}</p>
            <button
              onClick={resetUpload}
              className="mt-4 px-6 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
            >
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  );
}
