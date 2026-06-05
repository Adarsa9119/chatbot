export default function MessageBubble({ message, onSourceClick }) {
  const isUser = message.role === 'user';
  return (
    <div className={`message ${message.role}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      <div className="message-body">
        <div className="message-role">{isUser ? 'You' : 'Assistant'}</div>
        <div className="message-content">{message.content}</div>
        {message.source_chunk_ids?.length > 0 && (
          <div className="message-sources">
            {message.source_chunk_ids.map((id, i) => (
              <button key={id} className="source-chip" onClick={() => onSourceClick?.(id)}>
                Source {i + 1}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}