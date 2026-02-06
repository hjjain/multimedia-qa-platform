import { useState, useCallback } from 'react';
import { sendMessage, streamMessage } from '../services/api';

/**
 * Custom hook for managing chat state and interactions.
 * Supports both regular and streaming responses.
 *
 * @param {string} documentId - The document to chat about.
 * @returns {Object} Chat state and handler functions.
 */
export default function useChat(documentId) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true);

  const sendChatMessage = useCallback(
    async (input) => {
      if (!input.trim() || isLoading) return;

      const userMessage = { role: 'user', content: input };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        if (useStreaming) {
          let assistantContent = '';
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: '', isStreaming: true },
          ]);

          await streamMessage(documentId, input, messages, (chunk) => {
            assistantContent += chunk;
            setMessages((prev) => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1] = {
                role: 'assistant',
                content: assistantContent,
                isStreaming: true,
              };
              return newMessages;
            });
          });

          setMessages((prev) => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1].isStreaming = false;
            return newMessages;
          });
        } else {
          const response = await sendMessage(documentId, input, messages);
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
    },
    [documentId, isLoading, messages, useStreaming]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    useStreaming,
    setUseStreaming,
    sendChatMessage,
    clearMessages,
  };
}
