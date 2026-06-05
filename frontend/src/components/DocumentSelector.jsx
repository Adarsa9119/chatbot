export default function DocumentSelector({ docs = [], selected = [], onToggle }) {
  if (!docs.length) return (
    <p className="text-sm text-muted">No documents available. Ask an admin to upload documents.</p>
  );
  return (
    <div className="chat-doc-selector">
      {docs.map(doc => (
        <button
          key={doc.doc_id}
          className={`doc-chip ${selected.includes(doc.doc_id) ? 'selected' : ''}`}
          onClick={() => onToggle(doc.doc_id)}
        >
          📄 {doc.title}
        </button>
      ))}
    </div>
  );
}