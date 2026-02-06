import React from 'react';
import { FileText } from 'lucide-react';

/**
 * Summary component that displays the AI-generated summary
 * of an uploaded document or media file.
 */
export default function Summary({ summary, filename, fileType }) {
  const typeColors = {
    pdf: 'bg-red-100 text-red-700',
    audio: 'bg-green-100 text-green-700',
    video: 'bg-purple-100 text-purple-700',
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center gap-3 mb-4">
        <FileText className="w-6 h-6 text-blue-500" />
        <div className="flex-1 min-w-0">
          <h2 className="font-semibold text-gray-800">Document Summary</h2>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-sm text-gray-500 truncate">{filename}</p>
            <span
              className={`text-xs px-2 py-0.5 rounded-full ${typeColors[fileType] || 'bg-gray-100 text-gray-700'}`}
            >
              {fileType}
            </span>
          </div>
        </div>
      </div>
      <div className="prose prose-sm max-w-none">
        <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
          {summary}
        </p>
      </div>
    </div>
  );
}
