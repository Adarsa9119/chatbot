import { useState, useRef, useEffect } from 'react';
import { chatApi } from '../api/chatApi';
import { sessionApi } from '../api/sessionApi';
import { useChat } from '../context/ChatContext';
import MessageBubble from './MessageBubble';
import DocumentSelector from './DocumentSelector';
import SessionList from './SessionList';
import LoadingSpinner from './LoadingSpinner';

export default function ChatWindow({ isAdmin = false }) {
  const {
    sessions, setSessions,
    activeSession, setActiveSession,
    messages, setMessages, addMessage, clearMessages,
    selectedDocs, setSelectedDocs,
  } = useChat();

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sessionLoading, setSessionLoading] = useState(false);
  const [sourceChunk, setSourceChunk] = useState(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const loadSessions = async () => {
    try {
      const res = await sessionApi.getAll();
      setSessions(res.data?.sessions || res.data || []);
    } catch (err) {
      console.error('Failed to load sessions', err);
    }
  };

  const createNewSession = async () => {
    setSessionLoading(true);
    try {
      const res = await sessionApi.create();
      const newSession = res.data?.session || res.data;
      setSessions(prev => [newSession, ...prev]);
      setActiveSession(newSession.session_id);
      clearMessages();
      setError('');
    } catch (err) {
      setError('Failed to create session.');
    } finally {
      setSessionLoading(false);
    }
  };

  const selectSession = async (sessionId) => {
    setActiveSession(sessionId);
    clearMessages();
    setError('');
    try {
      const res = await chatApi.getHistory(sessionId);
      const history = res.data?.messages || res.data || [];
      setMessages(history);
    } catch (err) {
      setError('Failed to load chat history.');
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      await sessionApi.delete(sessionId);
      setSessions(prev => prev.filter(s => s.session_id !== sessionId));
      if (activeSession === sessionId) {
        setActiveSession(null);
        clearMessages();
      }
    } catch (err) {
      setError('Failed to delete session.');
    }
  };

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    if (!activeSession) {
      setError('Please create or select a session first.');
      return;
    }

    const userMsg = {
      role: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
    };
    addMessage(userMsg);
    setInput('');
    setError('');
    setLoading(true);

    try {
      const payload = {
        session_id: activeSession,
        question: trimmed,
        ...(selectedDocs.length > 0 && { document_ids: selectedDocs }),
      };
      const res = await chatApi.ask(payload);
      const data = res.data;

      const assistantMsg = {
        role: 'assistant',
        content: data.answer || data.response || '',
        sources: data.sources || data.chunks || [],
        created_at: new Date().toISOString(),
      };
      addMessage(assistantMsg);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to get a response.';
      addMessage({
        role: 'assistant',
        content: `⚠️ ${detail}`,
        is_error: true,
        created_at: new Date().toISOString(),
      });
      setError('');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-layout">
      {/* Sidebar: sessions */}
      <aside className="chat-sidebar">
        <div className="chat-sidebar-header">
          <span className="chat-sidebar-title">Sessions</span>
          <button
            className="btn btn-sm btn-primary"
            onClick={createNewSession}
            disabled={sessionLoading}
          >
            {sessionLoading ? '…' : '+ New'}
          </button>
        </div>
        <SessionList
          sessions={sessions}
          active={activeSession}
          onSelect={selectSession}
          onDelete={deleteSession}
          onNew={createNewSession}
        />
      </aside>

      {/* Main chat area */}
      <div className="chat-main">
        {/* Document selector */}
        <div className="chat-doc-bar">
          <DocumentSelector
            selected={selectedDocs}
            onChange={setSelectedDocs}
          />
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {!activeSession && (
            <div className="chat-empty">
              <div className="chat-empty-icon">💬</div>
              <p className="chat-empty-title">No session selected</p>
              <p className="chat-empty-sub">
                Create a new session or pick an existing one to start chatting.
              </p>
              <button className="btn btn-primary" onClick={createNewSession}>
                Start New Session
              </button>
            </div>
          )}

          {activeSession && messages.length === 0 && !loading && (
            <div className="chat-empty">
              <div className="chat-empty-icon">🔍</div>
              <p className="chat-empty-title">Ask anything about the documents</p>
              <p className="chat-empty-sub">
                Answers are sourced strictly from the uploaded documents.
              </p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <MessageBubble
              key={idx}
              message={msg}
              onSourceClick={setSourceChunk}
            />
          ))}

          {loading && (
            <div className="chat-typing">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          )}

          {error && (
            <div className="alert alert-error" style={{ margin: '0 24px 12px' }}>
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="chat-input-bar">
          <div className="chat-input-wrap">
            <textarea
              ref={textareaRef}
              className="chat-textarea"
              placeholder={
                activeSession
                  ? 'Ask a question about the documents… (Enter to send)'
                  : 'Select or create a session to begin…'
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={!activeSession || loading}
              rows={1}
            />
            <button
              className="chat-send-btn"
              onClick={sendMessage}
              disabled={!input.trim() || !activeSession || loading}
              title="Send (Enter)"
            >
              {loading ? <LoadingSpinner size={16} /> : '↑'}
            </button>
          </div>
          <p className="chat-input-hint">
            Shift+Enter for new line · Answers come strictly from uploaded documents
          </p>
        </div>
      </div>

      {/* Source chunk modal */}
      {sourceChunk && (
        <div className="modal-overlay" onClick={() => setSourceChunk(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">📄 Source Chunk</div>
            <p className="text-sm text-muted" style={{ marginBottom: 12 }}>
              Document ID: {sourceChunk.doc_id} · Chunk #{sourceChunk.chunk_index}
            </p>
            <div
              style={{
                background: 'var(--bg3)',
                borderRadius: 'var(--radius)',
                padding: '14px',
                fontSize: '0.85rem',
                lineHeight: 1.7,
                color: 'var(--text)',
                maxHeight: 320,
                overflowY: 'auto',
                fontFamily: 'var(--mono)',
                whiteSpace: 'pre-wrap',
              }}
            >
              {sourceChunk.chunk_text}
            </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setSourceChunk(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}