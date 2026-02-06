import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { sendMessage, streamMessage } from '../services/api';

/**
 * Chat interface component for document Q&A.
 * Supports both regular and streaming responses.
 */
export default function ChatInterface({ documentId, onTimestampClick }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const question = input;
    const userMessage = { role: 'user', content: question };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      if (useStreaming) {
        let assistantContent = '';
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '', isStreaming: true },
        ]);

        await streamMessage(documentId, question, messages, (chunk) => {
          assistantContent += chunk;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: 'assistant',
              content: assistantContent,
              isStreaming: true,
            };
            return updated;
          });
        });

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].isStreaming = false;
          return updated;
        });
      } else {
        const response = await sendMessage(documentId, question, messages);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: response.answer,
            timestamps: response.timestamps,
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, an error occurred. Please try again.',
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-xl shadow-lg">
      {/* Header */}
      <div className="p-4 border-b flex justify-between items-center">
        <h2 className="font-semibold text-gray-800">Chat with Document</h2>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={useStreaming}
            onChange={(e) => setUseStreaming(e.target.checked)}
            className="rounded"
          />
          Stream responses
        </label>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg">Ask a question about your document</p>
            <p className="text-sm mt-2">
              The AI will answer based on the uploaded content
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-xl ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : msg.isError
                    ? 'bg-red-100 text-red-700'
                    : 'bg-gray-100 text-gray-800'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>

              {/* Timestamp links */}
              {msg.timestamps && msg.timestamps.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <p className="text-xs font-medium mb-1">Related timestamps:</p>
                  {msg.timestamps.map((ts, i) => (
                    <button
                      key={i}
                      onClick={() => onTimestampClick(ts.start_time)}
                      className="block text-xs text-blue-600 hover:underline mt-1"
                    >
                      [{formatTime(ts.start_time)}] {ts.text.substring(0, 60)}...
                    </button>
                  ))}
                </div>
              )}

              {msg.isStreaming && (
                <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1" />
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your document..."
            disabled={isLoading}
            className="flex-1 p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
