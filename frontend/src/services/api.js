import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min for large file uploads
});

/**
 * Upload a file with progress tracking.
 * @param {File} file - The file to upload.
 * @param {Function} onProgress - Callback for upload progress (0-100).
 * @returns {Promise<Object>} Upload response with document_id, summary, etc.
 */
export const uploadFile = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      const percent = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      onProgress?.(percent);
    },
  });

  return response.data;
};

/**
 * Get document metadata by ID.
 */
export const getDocument = async (documentId) => {
  const response = await api.get(`/upload/${documentId}`);
  return response.data;
};

/**
 * Send a chat message and get a complete response.
 */
export const sendMessage = async (
  documentId,
  question,
  conversationHistory = []
) => {
  const response = await api.post('/chat/', {
    document_id: documentId,
    question,
    conversation_history: conversationHistory,
  });
  return response.data;
};

/**
 * Stream a chat response using Server-Sent Events.
 * @param {string} documentId - Document to query.
 * @param {string} question - User's question.
 * @param {Array} conversationHistory - Previous messages.
 * @param {Function} onChunk - Callback for each streamed chunk.
 */
export const streamMessage = async (
  documentId,
  question,
  conversationHistory = [],
  onChunk
) => {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id: documentId,
      question,
      conversation_history: conversationHistory,
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ') && !line.includes('[DONE]')) {
        try {
          const data = JSON.parse(line.slice(6));
          onChunk(data.content);
        } catch {
          // Skip malformed chunks
        }
      }
    }
  }
};

/**
 * Get the media file URL for playback.
 */
export const getMediaUrl = (documentId) =>
  `${API_BASE}/media/${documentId}/file`;

/**
 * Get all timestamps for a document.
 */
export const getTimestamps = async (documentId) => {
  const response = await api.get(`/media/${documentId}/timestamps`);
  return response.data;
};

/**
 * Search timestamps by keyword.
 */
export const searchTimestamps = async (documentId, query) => {
  const response = await api.get(
    `/media/${documentId}/timestamps/search`,
    { params: { query } }
  );
  return response.data;
};
