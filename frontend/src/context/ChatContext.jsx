import { createContext, useContext, useState } from 'react';

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const [sessions, setSessions]         = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages]         = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);

  const addMessage = (msg) => setMessages(prev => [...prev, msg]);
  const clearMessages = () => setMessages([]);
  const toggleDoc = (docId) => setSelectedDocs(prev =>
    prev.includes(docId) ? prev.filter(d => d !== docId) : [...prev, docId]
  );

  return (
    <ChatContext.Provider value={{
      sessions, setSessions,
      activeSession, setActiveSession,
      messages, setMessages, addMessage, clearMessages,
      selectedDocs, setSelectedDocs, toggleDoc,
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => useContext(ChatContext);