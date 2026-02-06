import React, { useState, useRef } from 'react';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import MediaPlayer from './components/MediaPlayer';
import Summary from './components/Summary';
import TimestampList from './components/TimestampList';

/**
 * Main application component.
 * Manages document state and coordinates child components.
 */
export default function App() {
  const [document, setDocument] = useState(null);
  const mediaPlayerRef = useRef(null);

  const handleUploadComplete = (result) => {
    setDocument(result);
  };

  const handleTimestampClick = (time) => {
    mediaPlayerRef.current?.seekTo(time);
  };

  const isMediaFile =
    document?.file_type === 'audio' || document?.file_type === 'video';

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Panscience Document Q&A
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                AI-powered document and multimedia analysis
              </p>
            </div>
            {document && (
              <button
                onClick={() => setDocument(null)}
                className="text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors"
              >
                Upload New File
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {!document ? (
          /* Upload View */
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-800 mb-2">
                Upload & Analyze
              </h2>
              <p className="text-gray-600 max-w-md">
                Upload a PDF, audio, or video file and start asking questions.
                Our AI will analyze your content and provide intelligent answers.
              </p>
            </div>
            <FileUpload onUploadComplete={handleUploadComplete} />
          </div>
        ) : (
          /* Document View */
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Summary & Media */}
            <div className="space-y-6">
              <Summary
                summary={document.summary}
                filename={document.filename}
                fileType={document.file_type}
              />

              {isMediaFile && (
                <>
                  <MediaPlayer
                    ref={mediaPlayerRef}
                    documentId={document.document_id}
                    fileType={document.file_type}
                    filename={document.filename}
                  />
                  <TimestampList
                    documentId={document.document_id}
                    timestamps={document.timestamps || []}
                    onTimestampClick={handleTimestampClick}
                  />
                </>
              )}
            </div>

            {/* Right Column - Chat */}
            <div>
              <ChatInterface
                documentId={document.document_id}
                onTimestampClick={handleTimestampClick}
              />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-auto py-6 text-center text-sm text-gray-500">
        <p>Panscience Document Q&A - Built with FastAPI, React & OpenAI</p>
      </footer>
    </div>
  );
}
