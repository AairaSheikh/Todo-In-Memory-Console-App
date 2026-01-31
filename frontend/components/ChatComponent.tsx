/**Chat component for AI-powered task management conversation.*/

'use client';

import { useEffect, useRef, useState } from 'react';
import { chatAPI } from '@/lib/api';
import { useTaskStore } from '@/lib/store';
import styles from './ChatComponent.module.css';

export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface ErrorState {
  message: string;
  type: 'api' | 'network' | 'auth' | 'timeout' | 'validation';
  retryable: boolean;
}

interface ChatComponentProps {
  userId: string;
  token: string;
  onTasksModified?: () => void;
}

export default function ChatComponent({ userId, token, onTasksModified }: ChatComponentProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ErrorState | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const { tasks, setTasks } = useTaskStore();

  // Load conversation history on mount
  useEffect(() => {
    loadConversationHistory();
  }, [userId, token]);

  // Auto-scroll to latest message
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const classifyError = (err: any): ErrorState => {
    // Check for network errors
    if (!err.response) {
      return {
        message: 'Network error. Please check your connection and try again.',
        type: 'network',
        retryable: true,
      };
    }

    const status = err.response.status;
    const detail = err.response?.data?.detail || 'An error occurred';

    // Check for authentication errors
    if (status === 401) {
      return {
        message: 'Your session has expired. Please log in again.',
        type: 'auth',
        retryable: false,
      };
    }

    if (status === 403) {
      return {
        message: 'You do not have permission to perform this action.',
        type: 'auth',
        retryable: false,
      };
    }

    // Check for timeout errors
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      return {
        message: 'Request timed out. Please try again.',
        type: 'timeout',
        retryable: true,
      };
    }

    // Check for validation errors
    if (status === 400) {
      return {
        message: detail,
        type: 'validation',
        retryable: false,
      };
    }

    // Check for rate limiting
    if (status === 429) {
      return {
        message: "You're sending messages too quickly. Please wait a moment.",
        type: 'api',
        retryable: true,
      };
    }

    // Server errors
    if (status >= 500) {
      return {
        message: 'Server error. Please try again later.',
        type: 'api',
        retryable: true,
      };
    }

    // Default API error
    return {
      message: detail || 'Failed to process request',
      type: 'api',
      retryable: true,
    };
  };

  const loadConversationHistory = async () => {
    setIsLoadingHistory(true);
    setError(null);

    try {
      const response = await chatAPI.getHistory(userId);
      const loadedMessages: Message[] = response.data.messages.map((msg: any) => ({
        id: msg.id,
        content: msg.content,
        sender: msg.sender,
        timestamp: new Date(msg.timestamp),
      }));
      setMessages(loadedMessages);
    } catch (err: any) {
      // Don't show error for history loading - just start with empty messages
      console.warn('Could not load conversation history:', err);
      setMessages([]);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputValue.trim()) {
      setError({
        message: 'Message cannot be empty',
        type: 'validation',
        retryable: false,
      });
      return;
    }

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      content: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setError(null);
    setIsLoading(true);
    setLastFailedMessage(inputValue);

    try {
      const response = await chatAPI.sendMessage(userId, inputValue);

      const assistantMessage: Message = {
        id: response.data.assistant_message_id || response.data.id,
        content: response.data.assistant_message || response.data.response,
        sender: 'assistant',
        timestamp: new Date(response.data.timestamp),
      };

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === userMessage.id
            ? { ...msg, id: response.data.user_message_id || response.data.id }
            : msg
        )
      );

      setMessages((prev) => [...prev, assistantMessage]);
      setLastFailedMessage(null);

      // Trigger task list refresh if tasks were modified
      if (onTasksModified) {
        onTasksModified();
      }
    } catch (err: any) {
      const errorState = classifyError(err);
      setError(errorState);
      console.error('Error sending message:', err);
      console.error('Error response data:', err.response?.data);

      // Remove the temporary user message on error
      setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = async () => {
    if (lastFailedMessage) {
      setInputValue(lastFailedMessage);
      // Trigger send after setting input
      setTimeout(() => {
        const form = document.querySelector('form') as HTMLFormElement;
        if (form) {
          form.dispatchEvent(new Event('submit', { bubbles: true }));
        }
      }, 0);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e as any);
    }
  };

  if (isLoadingHistory) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Loading conversation history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>Chat with AI Assistant</h2>
      </div>

      <div className={styles.messageList}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>
            <p>No messages yet. Start a conversation!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`${styles.message} ${styles[`message-${message.sender}`]}`}
            >
              <div className={styles.messageContent}>
                <p>{message.content}</p>
                <span className={styles.timestamp}>
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className={`${styles.message} ${styles['message-assistant']}`}>
            <div className={styles.messageContent}>
              <div className={styles.loadingIndicator}>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className={`${styles.errorMessage} ${styles[`error-${error.type}`]}`}>
          <div className={styles.errorContent}>
            <p>{error.message}</p>
            {error.retryable && (
              <button
                onClick={handleRetry}
                className={styles.retryButton}
                disabled={isLoading}
                aria-label="Retry failed message"
              >
                Retry
              </button>
            )}
          </div>
          <button
            onClick={() => setError(null)}
            className={styles.closeError}
            aria-label="Close error message"
          >
            ×
          </button>
        </div>
      )}

      <form onSubmit={handleSendMessage} className={styles.inputForm}>
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
          disabled={isLoading}
          className={styles.input}
          rows={3}
        />
        <button
          type="submit"
          disabled={isLoading || !inputValue.trim()}
          className={styles.sendButton}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
