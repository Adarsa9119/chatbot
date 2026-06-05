export default function SessionList({ sessions = [], active, onSelect, onNew }) {
  return (
    <div className="chat-sidebar">
      <div className="chat-sidebar-header">
        <span className="chat-sidebar-title">Sessions</span>
        <button className="btn btn-sm btn-primary" onClick={onNew}>+ New</button>
      </div>
      <div className="session-list">
        {!sessions.length && (
          <p className="text-sm text-muted" style={{ padding:'12px 8px' }}>No sessions yet</p>
        )}
        {sessions.map(s => (
          <div
            key={s.session_id}
            className={`session-item ${active === s.session_id ? 'active' : ''}`}
            onClick={() => onSelect(s.session_id)}
          >
            <div className="session-item-title">{s.title || 'Untitled Session'}</div>
            <div className="session-item-date">{new Date(s.created_at).toLocaleDateString()}</div>
          </div>
        ))}
      </div>
    </div>
  );
}